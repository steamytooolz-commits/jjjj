"""
Main entry point for the Discord Monopoly Bot.
Run this file to start the bot.
"""

import os
import asyncio
from dotenv import load_dotenv

from utils.command_handler import MonopolyBot

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ Error: DISCORD_TOKEN not found in environment variables!")
    print("Please create a .env file with your Discord bot token.")
    print("Example: DISCORD_TOKEN=your_token_here")
    exit(1)


async def main():
    """Main function to run the bot."""
    # Initialize bot with required intents
    intents = discord.Intents.default()
    intents.message_content = True  # Required for prefix commands
    intents.members = True
    
    # Create bot instance
    bot = MonopolyBot(
        command_prefix="!",
        intents=intents,
        description="🎩 A full-featured Monopoly bot for Discord!"
    )
    
    # Load cogs
    async with bot:
        await bot.load_extension("cogs.monopoly_commands")
        print("✅ Loaded MonopolyCommands cog")
        
        # Start the bot
        await bot.start(TOKEN)


if __name__ == "__main__":
    import discord
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot shutting down...")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
