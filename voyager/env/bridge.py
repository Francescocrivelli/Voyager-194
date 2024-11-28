import os.path
import time
import warnings
from typing import SupportsFloat, Any, Tuple, Dict

import requests
import json

import gymnasium as gym
from gymnasium.core import ObsType

import voyager.utils as U

from .minecraft_launcher import MinecraftInstance
from .process_monitor import SubprocessMonitor


class VoyagerEnv(gym.Env):
    def __init__(
        self,
        mc_port=None,
        azure_login=None,
        server_host="http://127.0.0.1",
        server_port=3000,
        request_timeout=600,
        log_path="./logs",
        bot_username="bot",
    ):
        self.bot_username = bot_username
        if not mc_port and not azure_login:
            raise ValueError("Either mc_port or azure_login must be specified")
        if mc_port and azure_login:
            warnings.warn(
                "Both mc_port and mc_login are specified, mc_port will be ignored"
            )
        self.mc_port = mc_port
        self.azure_login = azure_login
        self.server = f"{server_host}:{server_port}"
        self.server_port = server_port
        self.request_timeout = request_timeout
        self.log_path = log_path
        self.mineflayer = self.get_mineflayer_process(server_port)
        if azure_login:
            self.mc_instance = self.get_mc_instance()
        else:
            self.mc_instance = None
        self.has_reset = False
        self.reset_options = None
        self.connected = False
        self.server_paused = False

    def get_mineflayer_process(self, server_port):
        log_dir = U.f_join(self.log_path, f"mineflayer_{self.bot_username}")
        U.f_mkdir(self.log_path, log_dir)
        file_path = os.path.abspath(os.path.dirname(__file__))
        return SubprocessMonitor(
            commands=[
                "node",
                U.f_join(file_path, "mineflayer/index.js"),
                str(server_port),
            ],
            name=f"mineflayer_{self.bot_username}",
            ready_match=r"Server started on port (\d+)",
            log_path=log_dir,
        )

    def get_mc_instance(self):
        print(f"Creating Minecraft server for {self.bot_username}")
        log_dir = U.f_join(self.log_path, f"minecraft_{self.bot_username}")
        U.f_mkdir(self.log_path, log_dir)
        return MinecraftInstance(
            **self.azure_login,
            mineflayer=self.mineflayer,
            log_path=log_dir,
        )

    def check_process(self):
        if self.mc_instance and not self.mc_instance.is_running:
            print(f"Starting Minecraft server for {self.bot_username}")
            self.mc_instance.run()
            self.mc_port = self.mc_instance.port
            self.reset_options["port"] = self.mc_instance.port
            print(f"Server started on port {self.reset_options['port']}")
        retry = 0
        while not self.mineflayer.is_running:
            print(f"Mineflayer process has exited for {self.bot_username}, restarting")
            self.mineflayer.run()
            if not self.mineflayer.is_running:
                if retry > 3:
                    raise RuntimeError(f"Mineflayer process failed to start for {self.bot_username}")
                else:
                    continue
            print(self.mineflayer.ready_line)
            res = requests.post(
                f"{self.server}/start",
                json=self.reset_options,
                timeout=self.request_timeout,
            )
            if res.status_code != 200:
                self.mineflayer.stop()
                raise RuntimeError(
                    f"Minecraft server reply with code {res.status_code} for {self.bot_username}"
                )
            return res.json()

    def step(
        self,
        code: str,
        programs: str = "",
    ) -> Tuple[ObsType, SupportsFloat, bool, bool, Dict[str, Any]]:
        if not self.has_reset:
            raise RuntimeError("Environment has not been reset yet")
        self.check_process()
        
        data = {
            "code": code,
            "programs": programs,
        }
        res = requests.post(
            f"{self.server}/step", json=data, timeout=self.request_timeout
        )
        if res.status_code != 200:
            raise RuntimeError(f"Failed to step Minecraft server for {self.bot_username}")
        returned_data = res.json()
        
        return json.loads(returned_data)

    def render(self):
        raise NotImplementedError("render is not implemented")

    def reset(
        self,
        *,
        seed=None,
        options=None,
    ) -> Tuple[ObsType, Dict[str, Any]]:
        if options is None:
            options = {}

        if options.get("inventory", {}) and options.get("mode", "hard") != "hard":
            raise RuntimeError("inventory can only be set when options is hard")

        self.reset_options = {
            "port": self.mc_port,
            "reset": options.get("mode", "hard"),
            "inventory": options.get("inventory", {}),
            "equipment": options.get("equipment", []),
            "spread": options.get("spread", False),
            "waitTicks": options.get("wait_ticks", 5),
            "position": options.get("position", None),
            "username": self.bot_username,
            "server_port": self.server_port
        }

        # Remove pause/unpause calls here as well
        self.mineflayer.stop()
        time.sleep(1)  # wait for mineflayer to exit

        returned_data = self.check_process()
        self.has_reset = True
        self.connected = True
        # All the reset in step will be soft
        self.reset_options["reset"] = "soft"
        return json.loads(returned_data)

    def close(self):
        self.unpause()
        if self.connected:
            try:
                res = requests.post(f"{self.server}/stop")
                if res.status_code == 200:
                    self.connected = False
            except:
                pass
        if self.mc_instance:
            self.mc_instance.stop()
        self.mineflayer.stop()
        return not self.connected

    def pause(self):
        if self.mineflayer.is_running and not self.server_paused:
            try:
                res = requests.post(f"{self.server}/pause")
                if res.status_code == 200:
                    self.server_paused = True
            except:
                pass
        return self.server_paused

    def unpause(self):
        if self.mineflayer.is_running and self.server_paused:
            try:
                res = requests.post(f"{self.server}/pause")
                if res.status_code == 200:
                    self.server_paused = False
            except:
                pass
        return self.server_paused