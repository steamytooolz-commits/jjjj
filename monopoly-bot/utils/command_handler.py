"""
Extensive Command Handler for Discord Monopoly Bot
Supports slash commands, prefix commands, permissions, cooldowns, and more.
"""

import asyncio
from typing import Callable, Any, Optional, List, Dict
from dataclasses import dataclass, field
from functools import wraps
import discord
from discord.ext import commands
from discord import app_commands


@dataclass
class CommandConfig:
    """Configuration for a command."""
    name: str
    description: str
    category: str = "General"
    aliases: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    cooldown: float = 0.0  # seconds
    guild_only: bool = False
    nsfw: bool = False
    hidden: bool = False


class CommandHandler:
    """Advanced command handler with extensive features."""
    
    def __init__(self, bot: commands.Bot, prefix: str = "!"):
        self.bot = bot
        self.prefix = prefix
        self.commands: Dict[str, CommandConfig] = {}
        self.cooldowns: Dict[int, Dict[str, float]] = {}  # user_id -> {cmd_name: last_used}
        self.categories: Dict[str, List[str]] = {}
        
    def command(self, config: Optional[CommandConfig] = None, **kwargs):
        """Decorator to register a command with configuration."""
        def decorator(func: Callable):
            cmd_name = config.name if config else func.__name__
            cmd_config = config or CommandConfig(
                name=cmd_name,
                description=kwargs.get('description', 'No description provided.'),
                category=kwargs.get('category', 'General'),
                aliases=kwargs.get('aliases', []),
                permissions=kwargs.get('permissions', []),
                cooldown=kwargs.get('cooldown', 0.0),
                guild_only=kwargs.get('guild_only', False),
                nsfw=kwargs.get('nsfw', False),
                hidden=kwargs.get('hidden', False)
            )
            
            self.commands[cmd_name.lower()] = cmd_config
            
            # Add aliases
            for alias in cmd_config.aliases:
                self.commands[alias.lower()] = cmd_config
            
            # Track categories
            if cmd_config.category not in self.categories:
                self.categories[cmd_config.category] = []
            if cmd_name not in self.categories[cmd_config.category]:
                self.categories[cmd_config.category].append(cmd_name)
            
            # Note: The actual command registration happens in the cog
            # This decorator just stores the configuration
            
            return func
        
        return decorator
    
    async def check_cooldown(self, user_id: int, cmd_name: str, cooldown: float) -> bool:
        """Check if a command is on cooldown for a user."""
        if cooldown <= 0:
            return True
        
        current_time = asyncio.get_event_loop().time()
        
        if user_id not in self.cooldowns:
            self.cooldowns[user_id] = {}
        
        if cmd_name not in self.cooldowns[user_id]:
            self.cooldowns[user_id][cmd_name] = current_time
            return True
        
        elapsed = current_time - self.cooldowns[user_id][cmd_name]
        if elapsed >= cooldown:
            self.cooldowns[user_id][cmd_name] = current_time
            return True
        
        return False
    
    def get_remaining_cooldown(self, user_id: int, cmd_name: str, cooldown: float) -> float:
        """Get remaining cooldown time for a command."""
        if user_id not in self.cooldowns or cmd_name not in self.cooldowns[user_id]:
            return 0.0
        
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self.cooldowns[user_id][cmd_name]
        return max(0.0, cooldown - elapsed)
    
    async def check_permissions(self, ctx: commands.Context, permissions: List[str]) -> bool:
        """Check if user has required permissions."""
        if not permissions:
            return True
        
        if not isinstance(ctx.author, discord.Member):
            return False
        
        for perm in permissions:
            if not hasattr(ctx.author.guild_permissions, perm):
                continue
            if not getattr(ctx.author.guild_permissions, perm):
                return False
        
        return True
    
    def get_help_embed(self, category: Optional[str] = None) -> discord.Embed:
        """Generate a help embed for commands."""
        embed = discord.Embed(
            title="🎩 Monopoly Bot Help",
            description="Use `!command` or `/command` to use commands.",
            color=discord.Color.gold()
        )
        
        if category:
            if category not in self.categories:
                embed.add_field(name="Error", value=f"Category '{category}' not found.")
            else:
                embed.title = f"🎩 {category} Commands"
                for cmd_name in self.categories[category]:
                    cmd = self.commands.get(cmd_name.lower())
                    if cmd and not cmd.hidden:
                        embed.add_field(
                            name=f"`{cmd.name}`",
                            value=cmd.description or "No description.",
                            inline=False
                        )
        else:
            for cat, cmds in self.categories.items():
                cmd_list = ", ".join([f"`{c}`" for c in cmds if not self.commands[c.lower()].hidden])
                if cmd_list:
                    embed.add_field(name=f"{cat}", value=cmd_list, inline=False)
        
        embed.set_footer(text=f"Use !help <command> for detailed info on a command.")
        return embed
    
    def get_command_info(self, cmd_name: str) -> Optional[discord.Embed]:
        """Get detailed information about a specific command."""
        cmd = self.commands.get(cmd_name.lower())
        if not cmd:
            return None
        
        embed = discord.Embed(
            title=f"Command: {cmd.name}",
            description=cmd.description,
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Category", value=cmd.category, inline=True)
        embed.add_field(name="Cooldown", value=f"{cmd.cooldown}s" if cmd.cooldown > 0 else "None", inline=True)
        embed.add_field(name="Guild Only", value="Yes" if cmd.guild_only else "No", inline=True)
        
        if cmd.aliases:
            embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
        
        if cmd.permissions:
            embed.add_field(name="Required Permissions", value=", ".join(cmd.permissions), inline=False)
        
        return embed


class MonopolyBot(commands.Bot):
    """Custom bot class with extensive command handling."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmd_handler = CommandHandler(self)
        self.setup_monopoly_data()
    
    def setup_monopoly_data(self):
        """Initialize monopoly game data structures."""
        self.games: Dict[int, dict] = {}  # channel_id -> game_state
        self.players: Dict[int, dict] = {}  # user_id -> player_data
    
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Loaded {len(self.cmd_handler.commands)} commands')
        try:
            synced = await self.tree.sync()
            print(f'Synced {len(synced)} slash commands.')
        except Exception as e:
            print(f'Failed to sync slash commands: {e}')
    
    async def on_command_error(self, ctx: commands.Context, error):
        """Handle command errors gracefully."""
        if isinstance(error, commands.CommandOnCooldown):
            retry_after = error.retry_after
            await ctx.send(f"⏱️ This command is on cooldown. Try again in `{retry_after:.1f}` seconds.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have the required permissions to use this command.")
        elif isinstance(error, commands.CommandNotFound):
            pass  # Ignore unknown commands
        else:
            await ctx.send(f"❌ An error occurred: `{str(error)}`")
            raise error
