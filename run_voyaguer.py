# Existing code in run_voyaguer.py
from voyager import Voyager
import threading  # Import Python's threading module
import time

# Initialize API key and ports
openai_api_key = "the key open ai"
mc_port = 53164  # Both bots connect to the same Minecraft world

# Create first Voyager instance
voyager_1 = Voyager(
    mc_port=mc_port,
    openai_api_key=openai_api_key,
    server_port=3000,  # First bot's Mineflayer server port
    bot_username="bot1",  # Set unique username for the first bot
    resume=True,
)


# Wait before creating second bot
time.sleep(5)


# Create second Voyager instance
voyager_2 = Voyager(
    mc_port=mc_port,
    openai_api_key=openai_api_key,
    server_port=3001,  # Second bot's Mineflayer server port
    bot_username="bot2",  # Set unique username for the second bot
    resume=True,
)

# Define what each bot thread should do
def run_bot(voyager):
    try:
        voyager.learn()  # Run the bot's learning process
    except Exception as e:
        print(f"Error: {str(e)}")

# Create thread objects - they don't start running yet
bot1_thread = threading.Thread(target=run_bot, args=(voyager_1,))
bot2_thread = threading.Thread(target=run_bot, args=(voyager_2,))

# Start the threads - this actually starts the bots running
bot1_thread.start()
time.sleep(5)  # Wait before starting second bot
bot2_thread.start()

# Wait for both threads to complete
bot1_thread.join()
bot2_thread.join()
