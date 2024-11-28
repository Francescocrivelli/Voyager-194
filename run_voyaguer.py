from voyager import Voyager
import threading
import time
import signal
import sys
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MultiAgentManager:
    def __init__(self, mc_port, openai_api_key, num_agents=2, base_server_port=3000):
        self.mc_port = mc_port
        self.openai_api_key = openai_api_key
        self.num_agents = num_agents
        self.base_server_port = base_server_port
        self.agents = []
        self.threads = []
        self.logger = logging.getLogger('MultiAgentManager')
        self.shutdown_event = threading.Event()
        
        # Custom bot names
        self.bot_names = ["bot1-alby", "bot2-france"]
        
        # Create necessary directories
        self.create_directories()

    def create_directories(self):
        # Create base directories
        base_dirs = ["logs", "ckpt"]
        for dir_name in base_dirs:
            os.makedirs(dir_name, exist_ok=True)
            
        # Create bot-specific directories
        for bot_name in self.bot_names:
            # Create log directories
            os.makedirs(f"logs/mineflayer_{bot_name}", exist_ok=True)
            os.makedirs(f"logs/minecraft_{bot_name}", exist_ok=True)
            
            # Create checkpoint directories and subdirectories
            os.makedirs(f"ckpt/{bot_name}/action", exist_ok=True)
            os.makedirs(f"ckpt/{bot_name}/curriculum", exist_ok=True)
            os.makedirs(f"ckpt/{bot_name}/skill", exist_ok=True)
            
            # Initialize chest_memory.json if it doesn't exist
            chest_memory_path = f"ckpt/{bot_name}/action/chest_memory.json"
            if not os.path.exists(chest_memory_path):
                with open(chest_memory_path, 'w') as f:
                    f.write('{}')

    def create_agent(self, index):
        server_port = self.base_server_port + index
        try:
            agent = Voyager(
                mc_port=self.mc_port,
                openai_api_key=self.openai_api_key,
                server_port=server_port,
                bot_username=self.bot_names[index],
                resume=True,  # Changed to False for first run
                env_wait_ticks=20,
                env_request_timeout=600,
                reset_placed_if_failed=False,
                max_iterations=160,
                ckpt_dir=f"ckpt/{self.bot_names[index]}"  # Explicitly set checkpoint directory
            )
            self.logger.info(f"Created agent {self.bot_names[index]} with server port {server_port}")
            return agent
        except Exception as e:
            self.logger.error(f"Error in create_agent for {self.bot_names[index]}: {str(e)}")
            raise e

    def run_agent(self, agent):
        try:
            self.logger.info(f"Starting agent {agent.env.bot_username}")
            while not self.shutdown_event.is_set():
                try:
                    agent.learn()
                    if self.shutdown_event.is_set():
                        break
                except Exception as e:
                    self.logger.error(f"Error in agent {agent.env.bot_username}: {str(e)}")
                    if not self.shutdown_event.is_set():
                        time.sleep(5)
        finally:
            try:
                agent.close()
                self.logger.info(f"Closed agent {agent.env.bot_username}")
            except Exception as e:
                self.logger.error(f"Error closing agent {agent.env.bot_username}: {str(e)}")

    def start(self):
        # Create and start agents
        for i in range(self.num_agents):
            try:
                agent = self.create_agent(i)
                self.agents.append(agent)
                time.sleep(5)  # Wait between agent creation
            except Exception as e:
                self.logger.error(f"Error creating agent {i + 1}: {str(e)}")
                continue

        # Create and start threads
        for agent in self.agents:
            thread = threading.Thread(
                target=self.run_agent,
                args=(agent,),
                name=f"Thread-{agent.env.bot_username}"
            )
            self.threads.append(thread)
            thread.start()
            time.sleep(5)  # Wait between thread starts
            self.logger.info(f"Started thread for {agent.env.bot_username}")

    def stop(self):
        self.logger.info("Shutting down all agents...")
        self.shutdown_event.set()
        
        # First close all agents
        for agent in self.agents:
            try:
                agent.close()
            except Exception as e:
                self.logger.error(f"Error closing agent {agent.env.bot_username}: {str(e)}")
        
        # Then terminate threads with a shorter timeout
        for thread in self.threads:
            try:
                thread.join(timeout=5)  # Reduced timeout
                if thread.is_alive():
                    self.logger.warning(f"Thread {thread.name} did not terminate cleanly")
            except Exception as e:
                self.logger.error(f"Error joining thread {thread.name}: {str(e)}")

        self.logger.info("All agents shut down")

    def signal_handler(self, signum, frame):
        self.logger.info("\nReceived shutdown signal. Stopping agents gracefully...")
        try:
            self.stop()
        finally:
            sys.exit(0)


if __name__ == "__main__":
    # Your existing configuration
    MC_PORT = 61943  # Your Minecraft server port
    NUM_AGENTS = 2  # Number of bots you want to run
    BASE_SERVER_PORT = 3000

    # Create and start the manager
    manager = MultiAgentManager(
        mc_port=MC_PORT,
        openai_api_key=OPENAI_API_KEY,
        num_agents=NUM_AGENTS,
        base_server_port=BASE_SERVER_PORT
    )

    try:
        manager.start()
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop()
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        manager.stop()
        sys.exit(1)

# from voyager import Voyager
# import threading
# import time
# import signal
# import sys
# import logging
# import os
# import json
# import shutil

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )

# class MultiAgentManager:
#     def __init__(self, mc_port, openai_api_key, num_agents=2, base_server_port=3000):
#         self.mc_port = mc_port
#         self.openai_api_key = openai_api_key
#         self.num_agents = num_agents
#         self.base_server_port = base_server_port
#         self.agents = []
#         self.threads = []
#         self.running = True
#         self.logger = logging.getLogger('MultiAgentManager')
        
#         # Custom bot names
#         self.bot_names = ["bot1-alby", "bot2-france"]
        
#         # Create necessary directories
#         self.create_directories()
        
#         # Shared skill directory
#         self.shared_skill_dir = "shared_skills"
#         os.makedirs(self.shared_skill_dir, exist_ok=True)

#     def create_directories(self):
#         # Create base directories
#         base_dirs = ["logs", "ckpt"]
#         for dir_name in base_dirs:
#             os.makedirs(dir_name, exist_ok=True)
            
#         # Create bot-specific directories
#         for bot_name in self.bot_names:
#             # Create log directories
#             os.makedirs(f"logs/mineflayer_{bot_name}", exist_ok=True)
#             os.makedirs(f"logs/minecraft_{bot_name}", exist_ok=True)
            
#             # Create checkpoint directories with nested structure
#             checkpoint_dirs = [
#                 f"ckpt/{bot_name}/{bot_name}/action",
#                 f"ckpt/{bot_name}/{bot_name}/curriculum",
#                 f"ckpt/{bot_name}/{bot_name}/skill",
#                 f"ckpt/{bot_name}/{bot_name}/skill/code",
#                 f"ckpt/{bot_name}/{bot_name}/skill/description",
#                 f"ckpt/{bot_name}/{bot_name}/skill/vectordb"
#             ]
            
#             for dir_path in checkpoint_dirs:
#                 os.makedirs(dir_path, exist_ok=True)
            
#             # Initialize required JSON files
#             files_to_init = {
#                 f"ckpt/{bot_name}/{bot_name}/action/chest_memory.json": "{}",
#                 f"ckpt/{bot_name}/{bot_name}/curriculum/completed_tasks.json": "[]",
#                 f"ckpt/{bot_name}/{bot_name}/curriculum/failed_tasks.json": "[]",
#                 f"ckpt/{bot_name}/{bot_name}/curriculum/qa_cache.json": "{}",
#                 f"ckpt/{bot_name}/{bot_name}/skill/skills.json": "{}"
#             }
            
#             for file_path, initial_content in files_to_init.items():
#                 try:
#                     if not os.path.exists(file_path):
#                         with open(file_path, 'w') as f:
#                             f.write(initial_content)
#                         self.logger.info(f"Created file: {file_path}")
#                     else:
#                         self.logger.info(f"File already exists: {file_path}")
                        
#                     # Verify file exists and is readable
#                     with open(file_path, 'r') as f:
#                         content = f.read()
#                         self.logger.info(f"Successfully verified file: {file_path}")
#                 except Exception as e:
#                     self.logger.error(f"Error handling file {file_path}: {str(e)}")
#                     raise

#     def share_skills(self, source_agent, target_agent):
#         """Share skills from source agent to target agent."""
#         try:
#             source_skills_dir = f"ckpt/{source_agent.env.bot_username}/{source_agent.env.bot_username}/skill"
#             target_skills_dir = f"ckpt/{target_agent.env.bot_username}/{target_agent.env.bot_username}/skill"
            
#             # Read source skills
#             with open(f"{source_skills_dir}/skills.json", 'r') as f:
#                 source_skills = json.load(f)
            
#             # Read target skills
#             with open(f"{target_skills_dir}/skills.json", 'r') as f:
#                 target_skills = json.load(f)
                
#             # Merge skills
#             for skill_name, skill_data in source_skills.items():
#                 if skill_name not in target_skills:
#                     target_skills[skill_name] = skill_data
                    
#                     # Copy associated files
#                     if os.path.exists(f"{source_skills_dir}/code/{skill_name}.js"):
#                         shutil.copy2(
#                             f"{source_skills_dir}/code/{skill_name}.js",
#                             f"{target_skills_dir}/code/{skill_name}.js"
#                         )
#                     if os.path.exists(f"{source_skills_dir}/description/{skill_name}.txt"):
#                         shutil.copy2(
#                             f"{source_skills_dir}/description/{skill_name}.txt",
#                             f"{target_skills_dir}/description/{skill_name}.txt"
#                         )
            
#             # Save updated target skills
#             with open(f"{target_skills_dir}/skills.json", 'w') as f:
#                 json.dump(target_skills, f, indent=2)
                
#             self.logger.info(f"Skills shared from {source_agent.env.bot_username} to {target_agent.env.bot_username}")
            
#         except Exception as e:
#             self.logger.error(f"Error sharing skills: {str(e)}")

#     def create_agent(self, index):
#         server_port = self.base_server_port + index
#         try:
#             agent = Voyager(
#                 mc_port=self.mc_port,
#                 openai_api_key=self.openai_api_key,
#                 server_port=server_port,
#                 bot_username=self.bot_names[index],
#                 resume=False,
#                 env_wait_ticks=20,
#                 env_request_timeout=600,
#                 reset_placed_if_failed=False,
#                 max_iterations=160,
#                 ckpt_dir=f"ckpt/{self.bot_names[index]}",
#                 skill_library_dir=self.shared_skill_dir
#             )
#             self.logger.info(f"Created agent {self.bot_names[index]} with server port {server_port}")
#             return agent
#         except Exception as e:
#             self.logger.error(f"Error in create_agent for {self.bot_names[index]}: {str(e)}")
#             raise e

#     def run_agent(self, agent, agent_index):
#         try:
#             self.logger.info(f"Starting agent {agent.env.bot_username}")
#             while self.running:
#                 try:
#                     agent.learn()
                    
#                     # Share skills with other agents periodically
#                     if len(self.agents) > 1:
#                         for other_agent in self.agents:
#                             if other_agent != agent:
#                                 self.share_skills(agent, other_agent)
                    
#                     if not self.running:
#                         break
#                 except Exception as e:
#                     self.logger.error(f"Error in agent {agent.env.bot_username}: {str(e)}")
#                     time.sleep(5)  # Wait before retrying
#         finally:
#             try:
#                 agent.close()
#                 self.logger.info(f"Closed agent {agent.env.bot_username}")
#             except Exception as e:
#                 self.logger.error(f"Error closing agent {agent.env.bot_username}: {str(e)}")

#     def start(self):
#         # Initialize signal handler for graceful shutdown
#         signal.signal(signal.SIGINT, self.signal_handler)
#         signal.signal(signal.SIGTERM, self.signal_handler)

#         # Create and start agents
#         for i in range(self.num_agents):
#             try:
#                 agent = self.create_agent(i)
#                 self.agents.append(agent)
#                 time.sleep(5)  # Wait between agent creation
#             except Exception as e:
#                 self.logger.error(f"Error creating agent {i + 1}: {str(e)}")
#                 continue

#         # Create and start threads
#         for i, agent in enumerate(self.agents):
#             thread = threading.Thread(
#                 target=self.run_agent,
#                 args=(agent, i),
#                 name=f"Thread-{agent.env.bot_username}"
#             )
#             self.threads.append(thread)
#             thread.start()
#             time.sleep(5)  # Wait between thread starts
#             self.logger.info(f"Started thread for {agent.env.bot_username}")

#     def stop(self):
#         self.logger.info("Shutting down all agents...")
#         self.running = False
        
#         # Close all agents
#         for agent in self.agents:
#             try:
#                 agent.close()
#                 self.logger.info(f"Closed agent {agent.env.bot_username}")
#             except Exception as e:
#                 self.logger.error(f"Error closing agent {agent.env.bot_username}: {str(e)}")

#         # Wait for threads to complete with timeout
#         for thread in self.threads:
#             thread.join(timeout=30)
#             if thread.is_alive():
#                 self.logger.warning(f"Thread {thread.name} did not terminate cleanly")

#         self.logger.info("All agents shut down")

#     def signal_handler(self, signum, frame):
#         self.logger.info("\nReceived shutdown signal. Stopping agents gracefully...")
#         self.stop()
#         sys.exit(0)


# if __name__ == "__main__":
#     MC_PORT = 61943  # Your Minecraft server port
#     OPENAI_API_KEY = "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"  # Replace with your API key
#     NUM_AGENTS = 2
#     BASE_SERVER_PORT = 3000

#     # Create and start the manager
#     manager = MultiAgentManager(
#         mc_port=MC_PORT,
#         openai_api_key=OPENAI_API_KEY,
#         num_agents=NUM_AGENTS,
#         base_server_port=BASE_SERVER_PORT
#     )

#     try:
#         manager.start()
#         # Keep main thread alive
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         manager.stop()
#         sys.exit(0)
#     except Exception as e:
#         logging.error(f"Fatal error: {str(e)}")
#         manager.stop()
#         sys.exit(1)
