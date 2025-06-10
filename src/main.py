"""
Bishop Bot - Main Entry Point
Last updated: 2025-06-01 04:09:45 UTC by Bioku87
"""
import os
import sys
import asyncio
import logging
import traceback
from logging.handlers import RotatingFileHandler
import discord
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Ensure project structure is properly set up
def verify_directory_structure():
    """Verify and create necessary directories"""
    directories = [
        "logs",
        "data",
        "data/database",
        "data/audio/soundboard/Default",
        "data/audio/soundboard/Combat",
        "data/audio/soundboard/Ambience",
        "data/voice/sessions",
        "data/voice/profiles",
        "config",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    return True

# Setup logging
def setup_logging():
    """Set up logging configuration"""
    LOG_DIR = "logs"
    LOG_FILE = os.path.join(LOG_DIR, "bishop.log")
    os.makedirs(LOG_DIR, exist_ok=True)
    
    logger = logging.getLogger('bishop_bot')
    logger.setLevel(logging.INFO)
    
    # File handler
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# IMPORTANT: Create a dedicated function for the control window
def start_control_window(bot):
    """Start the control window with robust error handling"""
    print("Attempting to start control window...")
    
    try:
        # Directly import control_window here to catch import errors immediately
        import control_window
        print("Control window module imported successfully")
        
        # Initialize the control window
        window = control_window.initialize_control_window(bot)
        
        if window:
            print("Control window initialized successfully")
            return window
        else:
            print("Control window initialization returned None")
            return None
    except ImportError as e:
        print(f"ERROR: Could not import control window module: {e}")
        return None
    except Exception as e:
        print(f"ERROR: Failed to start control window: {e}")
        traceback.print_exc()
        return None

async def main():
    """Main entry point for the Bishop Bot"""
    logger = setup_logging()
    
    # Verify directory structure
    if verify_directory_structure():
        logger.info("Directory structure verified")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Check for .env file and create template if not exists
        if not os.path.exists(".env"):
            with open(".env", "w") as f:
                f.write("# Bishop Bot Environment Variables\n")
                f.write("DISCORD_TOKEN=your_discord_token_here\n")
                f.write("# Optional configuration\n")
                f.write("# OPENAI_API_KEY=your_openai_api_key_here\n")
            logger.info("Created template .env file. Please edit it with your API keys.")
            print("Created template .env file. Please edit it with your API keys.")
            input("Press any key to continue...")
        
        # Get Discord token
        TOKEN = os.getenv('DISCORD_TOKEN')
        if not TOKEN or TOKEN == "your_discord_token_here":
            logger.critical("Discord token not found or not set in environment variables!")
            print("\nError: Discord token not found or not properly set in .env file!")
            print("Please add your Discord token to the .env file as DISCORD_TOKEN=your_token_here\n")
            return

        # Import bot module and create the bot
        try:
            print("Importing bot module...")
            from bot import BishopBot
            
            # Create the bot instance
            print("Creating BishopBot instance...")
            bot = BishopBot()
            if not bot:
                logger.critical("Failed to create BishopBot instance")
                print("\nError: Failed to create BishopBot instance\n")
                return
                
            print("Bot instance created successfully")
        except ImportError as e:
            logger.critical(f"Failed to import bot module: {e}")
            print(f"ERROR: Failed to import bot module: {e}")
            return
        except Exception as e:
            logger.critical(f"Error creating bot instance: {e}")
            print(f"ERROR: Error creating bot instance: {e}")
            traceback.print_exc()
            return
            
        # IMPORTANT: Start the control window in a separate thread
        # This makes sure it doesn't block the bot from starting
        import threading
        control_window_thread = threading.Thread(target=start_control_window, args=(bot,))
        control_window_thread.daemon = True  # This thread will close when the main program exits
        control_window_thread.start()
            
        # Register signal handlers for graceful shutdown if on Unix
        if os.name != 'nt':
            import signal
            for sig in (signal.SIGINT, signal.SIGTERM):
                signal.signal(sig, lambda signal, frame: asyncio.create_task(bot.close()))
        
        # Start the bot
        try:
            logger.info("Starting Bishop Bot...")
            print("Starting Bishop Bot...")
            await bot.start(TOKEN)
        except discord.LoginFailure:
            logger.critical("Invalid Discord token!")
            print("\nError: Invalid Discord token. Please check your .env file.")
        except discord.PrivilegedIntentsRequired:
            logger.critical("Required privileged intents are not enabled!")
            print("\nError: This bot requires privileged intents (Members, Presence, and Message Content).")
            print("Please enable them in the Discord Developer Portal under your bot settings.")
        except Exception as e:
            logger.critical(f"Error starting bot: {e}")
            traceback.print_exc()
            print(f"\nError starting bot: {e}")
        finally:
            if bot and not bot.is_closed():
                await bot.close()
                
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"\nImport error: {e}")
        print("Make sure you have installed all required dependencies:")
        print("pip install -r requirements.txt\n")
        traceback.print_exc()
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        traceback.print_exc()
        print(f"\nError: {e}")
        print("Check the logs for more details.")

if __name__ == "__main__":
    # Properly handles event loop on all platforms
    asyncio.run(main())