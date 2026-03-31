"""
Monopoly Bot Commands Cog
Contains all Discord commands for the Monopoly game.
"""

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
from typing import Optional
import asyncio

from cogs.monopoly_logic import MonopolyGame, PropertyColor, Player, NPC
from utils.command_handler import CommandConfig


class AuctionStartView(View):
    """Button view for starting an auction."""
    
    def __init__(self, game: MonopolyGame, property_pos: int, requester_id: int):
        super().__init__(timeout=30.0)
        self.game = game
        self.property_pos = property_pos
        self.requester_id = requester_id
    
    @discord.ui.button(label="Start Auction", style=discord.ButtonStyle.green)
    async def start_auction_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("❌ Only the player who declined can start the auction!", ephemeral=True)
            return
        
        success, message = self.game.start_auction(self.property_pos)
        
        if success:
            prop = self.game.board.properties[self.property_pos]
            status = self.game.get_auction_status()
            
            embed = discord.Embed(
                title="🔨 Auction Started!",
                description=f"**{prop.name}** is now up for auction!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Starting Bid", value=f"${status['current_bid'] + 10}", inline=True)
            embed.add_field(name="Min Increment", value=f"${status['min_next_bid'] - status['current_bid']}", inline=True)
            embed.add_field(name="Property Value", value=f"${prop.price}", inline=True)
            embed.set_footer(text="Use !bid <amount> to bid | !pass to skip")
            
            await interaction.response.send_message(embed=embed)
            self.stop()
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("❌ Only the player who declined can cancel!", ephemeral=True)
            return
        
        await interaction.response.send_message("✅ Auction cancelled. Property remains unsold.", ephemeral=True)
        self.stop()


class MonopolyCommands(commands.Cog):
    """Monopoly game commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # channel_id -> MonopolyGame
    
    def get_game(self, channel_id: int) -> Optional[MonopolyGame]:
        """Get or create a game for a channel."""
        if channel_id not in self.games:
            return None
        return self.games[channel_id]
    
    def create_game(self, channel_id: int) -> MonopolyGame:
        """Create a new game for a channel."""
        game = MonopolyGame(channel_id)
        self.games[channel_id] = game
        return game
    
    @commands.hybrid_command(
        name="start",
        description="Start a new Monopoly game",
        aliases=["newgame", "create"]
    )
    @app_commands.describe(max_players="Maximum number of players (2-8)", npcs_enabled="Enable NPC opponents")
    async def start_game(self, ctx: commands.Context, max_players: int = 4, npcs_enabled: bool = True):
        """Start a new Monopoly game."""
        max_players = max(2, min(8, max_players))
        
        if ctx.channel.id in self.games:
            game = self.games[ctx.channel.id]
            if game.game_started:
                await ctx.send("❌ A game is already in progress!")
                return
            else:
                del self.games[ctx.channel.id]
        
        game = MonopolyGame(ctx.channel.id, max_players=max_players, npcs_enabled=npcs_enabled)
        self.games[ctx.channel.id] = game
        
        npc_status = "✅ Enabled" if npcs_enabled else "❌ Disabled"
        embed = discord.Embed(
            title="🎩 New Monopoly Game Created!",
            description=f"Use `!join` or `/join` to join the game!\nNPCs will auto-fill if needed.",
            color=discord.Color.green()
        )
        embed.add_field(name="Max Players", value=str(max_players), inline=True)
        embed.add_field(name="NPCs", value=npc_status, inline=True)
        embed.add_field(name="Host", value=ctx.author.name, inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(
        name="join",
        description="Join an existing Monopoly game",
        aliases=["enter"]
    )
    async def join_game(self, ctx: commands.Context):
        """Join a Monopoly game."""
        game = self.get_game(ctx.channel.id)
        
        if not game:
            await ctx.send("❌ No game found! Use `!start` to create one.")
            return
        
        if game.game_started:
            await ctx.send("❌ The game has already started!")
            return
        
        if game.add_player(ctx.author.id, ctx.author.name):
            player_count = len(game.players)
            embed = discord.Embed(
                title="✅ Joined the Game!",
                description=f"{ctx.author.name}, you've joined the Monopoly game!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Starting Money", value="$1500", inline=True)
            embed.add_field(name="Players", value=f"{player_count}", inline=True)
            
            # Show all players
            players_list = "\n".join([p.username for p in game.players.values()])
            embed.add_field(name="All Players", value=players_list or "None", inline=False)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Could not join. Game might be full or you're already in.")
    
    @commands.hybrid_command(
        name="leave",
        description="Leave the current game",
        aliases=["exit", "quit"]
    )
    async def leave_game(self, ctx: commands.Context):
        """Leave the current game."""
        game = self.get_game(ctx.channel.id)
        
        if not game:
            await ctx.send("❌ No game found!")
            return
        
        if game.remove_player(ctx.author.id):
            await ctx.send(f"✅ {ctx.author.name} has left the game.")
        else:
            await ctx.send("❌ You're not in this game!")
    
    @commands.hybrid_command(
        name="addnpc",
        description="Add an NPC to the game (before it starts)",
        aliases=["addbot", "npc"]
    )
    @app_commands.describe(personality="NPC personality type")
    async def add_npc(self, ctx: commands.Context, personality: str = "balanced"):
        """Add an NPC to the game."""
        game = self.get_game(ctx.channel.id)
        
        if not game:
            await ctx.send("❌ No game found! Use `!start` first.")
            return
        
        if game.game_started:
            await ctx.send("❌ Game already started! Can't add NPCs now.")
            return
        
        personalities = ["aggressive", "conservative", "balanced", "random"]
        if personality.lower() not in personalities:
            await ctx.send(f"❌ Invalid personality! Choose from: {', '.join(personalities)}")
            return
        
        npc_name = f"NPC {len(game.npcs) + 1}"
        if game.add_npc(npc_name, personality.lower()):
            await ctx.send(f"✅ Added **{npc_name}** ({personality}) to the game!")
        else:
            await ctx.send("❌ Could not add NPC. Game might be full.")
    
    @commands.hybrid_command(
        name="begin",
        description="Start the game (requires at least 1 human player)",
        aliases=["play", "launch"]
    )
    async def begin_game(self, ctx: commands.Context):
        """Begin the Monopoly game."""
        game = self.get_game(ctx.channel.id)
        
        if not game:
            await ctx.send("❌ No game found!")
            return
        
        if len(game.players) < 1:
            await ctx.send("❌ Need at least 1 human player to start!")
            return
        
        if game.start_game():
            embed = discord.Embed(
                title="🎲 Game Started!",
                description="Let the Monopoly begin!",
                color=discord.Color.gold()
            )
            
            players_info = ""
            for player in game.players.values():
                players_info += f"👤 {player.username} - ${player.money}\n"
            for npc in game.npcs.values():
                players_info += f"🤖 {npc.username} ({npc.personality}) - ${npc.money}\n"
            
            embed.add_field(name="All Players", value=players_info, inline=False)
            
            current = game.get_current_entity()
            if current:
                turn_icon = "👤" if isinstance(current, Player) else "🤖"
                embed.add_field(name="Current Turn", value=f"{turn_icon} {current.username}", inline=True)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to start the game.")
    
    async def process_npc_turn(self, game: MonopolyGame, npc: NPC, channel):
        """Process an NPC's turn automatically."""
        await asyncio.sleep(2)  # Small delay for realism
        
        # Roll dice
        die1, die2 = game.roll_dice()
        total = die1 + die2
        
        # Move NPC
        passed_go = npc.move(total)
        
        # Get landed space
        space_name = game.board.get_space_name(npc.position)
        space_type = game.board.get_space_type(npc.position)
        
        messages = [f"🤖 **{npc.username}**'s turn!"]
        messages.append(f"🎲 Rolled **{die1}** + **{die2}** = **{total}**")
        messages.append(f"📍 Landed on **{space_name}** ({space_type})")
        
        if passed_go:
            messages.append("🎉 Passed GO! Collected $200")
        
        # Handle property purchase
        if space_type in ["Property", "Railroad", "Utility"]:
            prop = game.board.properties.get(npc.position)
            if prop and prop.owner is None:
                success, msg = game.buy_property_npc(npc, npc.position)
                if success:
                    messages.append(f"🏠 {msg}")
                else:
                    messages.append(f"💭 {npc.username} decided not to buy.")
            elif prop and prop.owner and prop.owner != npc.user_id:
                # Pay rent
                success, msg = game.pay_rent_npc(npc, npc.position)
                if success:
                    messages.append(f"💸 {msg}")
        
        # Handle Chance/Community Chest
        elif space_type == "Chance":
            card = game.board.draw_chance()
            if card:
                result, card_msgs = game.process_card_effect(npc, card)
                messages.append(f"🃏 {result}")
                messages.extend(card_msgs)
        
        elif space_type == "Community Chest":
            card = game.board.draw_community_chest()
            if card:
                result, card_msgs = game.process_card_effect(npc, card)
                messages.append(f"🎁 {result}")
                messages.extend(card_msgs)
        
        # Send all messages as one embed
        embed = discord.Embed(
            title="🤖 NPC Turn",
            description="\n".join(messages),
            color=discord.Color.blue()
        )
        embed.add_field(name="💰 Money", value=f"${npc.money}", inline=True)
        embed.add_field(name="🏠 Properties", value=str(len(npc.properties)), inline=True)
        
        await channel.send(embed=embed)
        
        # Move to next turn
        game.next_turn()
    
    @commands.hybrid_command(
        name="roll",
        description="Roll the dice and move",
        aliases=["throw", "dice"]
    )
    async def roll_dice(self, ctx: commands.Context):
        """Roll dice and move."""
        game = self.get_game(ctx.channel.id)
        
        if not game or not game.game_started:
            await ctx.send("❌ No active game!")
            return
        
        # Check if it's an NPC's turn
        current_entity = game.get_current_entity()
        if isinstance(current_entity, NPC):
            await ctx.send(f"⏳ It's **{current_entity.username}**'s turn (NPC). Please wait...")
            return
        
        current_player = game.get_current_player()
        if not current_player or current_player.user_id != ctx.author.id:
            current = game.get_current_entity()
            await ctx.send(f"❌ It's not your turn! Current: {current.username if current else 'Unknown'}")
            return
        
        if current_player.bankrupt:
            await ctx.send("❌ You're bankrupt and out of the game!")
            return
        
        # Roll dice
        die1, die2 = game.roll_dice()
        total = die1 + die2
        
        # Move player
        passed_go = current_player.move(total)
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"{ctx.author.name} rolled **{die1}** + **{die2}** = **{total}**",
            color=discord.Color.orange()
        )
        
        if passed_go:
            embed.add_field(name="🎉 Passed GO!", value="Collected $200", inline=False)
        
        # Get current space
        space_name = game.board.get_space_name(current_player.position)
        space_type = game.board.get_space_type(current_player.position)
        
        embed.add_field(name="📍 Landed On", value=f"{space_name} ({space_type})", inline=False)
        embed.add_field(name="💰 Money", value=f"${current_player.money}", inline=True)
        embed.add_field(name="🏠 Properties", value=str(len(current_player.properties)), inline=True)
        
        # Handle special spaces - Just inform, don't auto-pay (use !payrent command)
        if space_type in ["Property", "Railroad", "Utility"]:
            prop = game.board.properties.get(current_player.position)
            if prop and prop.owner and prop.owner != current_player.user_id:
                owner = game.players.get(prop.owner) or game.npcs.get(prop.owner)
                rent = prop.get_rent()
                embed.add_field(
                    name="💸 Rent Due!",
                    value=f"Owned by {owner.username if owner else 'Unknown'}\nUse `!payrent` to pay ${rent}",
                    inline=False
                )
        
        elif space_type == "Chance":
            card = game.board.draw_chance()
            if card:
                result, messages = game.process_card_effect(current_player, card)
                embed.add_field(name="🃏 Chance", value=result, inline=False)
                if messages:
                    embed.add_field(name="Effects", value="\n".join(messages[:3]), inline=False)
        
        elif space_type == "Community Chest":
            card = game.board.draw_community_chest()
            if card:
                result, messages = game.process_card_effect(current_player, card)
                embed.add_field(name="🎁 Community Chest", value=result, inline=False)
                if messages:
                    embed.add_field(name="Effects", value="\n".join(messages[:3]), inline=False)
        
        await ctx.send(embed=embed)
        
        # After human turn, check if next is NPC and process
        game.next_turn()
        next_entity = game.get_current_entity()
        if isinstance(next_entity, NPC) and not next_entity.bankrupt:
            await self.process_npc_turn(game, next_entity, ctx.channel)
    
    @commands.hybrid_command(
        name="buy",
        description="Buy the property you landed on",
        aliases=["purchase"]
    )
    async def buy_property(self, ctx: commands.Context):
        """Buy the current property."""
        game = self.get_game(ctx.channel.id)
        
        if not game or not game.game_started:
            await ctx.send("❌ No active game!")
            return
        
        # Check if auction is active
        if game.active_auction:
            await ctx.send("⏳ An auction is already in progress! Use `!bid` or `!pass`")
            return
        
        current_player = game.get_current_player()
        if current_player.user_id != ctx.author.id:
            await ctx.send("❌ It's not your turn!")
            return
        
        pos = current_player.position
        success, message = game.buy_property(current_player, pos)
        
        if success:
            prop = game.board.properties[pos]
            embed = discord.Embed(
                title="🏠 Property Purchased!",
                description=f"You bought **{prop.name}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Price", value=f"${prop.price}", inline=True)
            embed.add_field(name="Remaining Money", value=f"${current_player.money}", inline=True)
            embed.add_field(name="Total Properties", value=str(len(current_player.properties)), inline=True)
            await ctx.send(embed=embed)
        else:
            # Offer to start auction if player declines or can't afford
            if "Not enough money" not in message:
                # Ask if they want to start auction
                embed = discord.Embed(
                    title="💭 Property Purchase Declined",
                    description=f"{message}\n\nStart an auction?",
                    color=discord.Color.orange()
                )
                view = AuctionStartView(game, pos, ctx.author.id)
                await ctx.send(embed=embed, view=view)
            else:
                await ctx.send(f"❌ {message}")
    
    @commands.hybrid_command(
        name="auction",
        description="Start an auction for the current property",
        aliases=["startauction"]
    )
    async def start_auction_cmd(self, ctx: commands.Context):
        """Start an auction for the current property."""
        game = self.get_game(ctx.channel.id)
        
        if not game or not game.game_started:
            await ctx.send("❌ No active game!")
            return
        
        if game.active_auction:
            await ctx.send("⏳ An auction is already in progress!")
            return
        
        current_player = game.get_current_player()
        if current_player and current_player.user_id != ctx.author.id:
            await ctx.send("❌ It's not your turn!")
            return
        
        # Get current position (either from current player or last roller)
        if current_player:
            pos = current_player.position
        else:
            await ctx.send("❌ No player to auction for!")
            return
        
        success, message = game.start_auction(pos)
        
        if success:
            prop = game.board.properties[pos]
            status = game.get_auction_status()
            
            embed = discord.Embed(
                title="🔨 Auction Started!",
                description=f"**{prop.name}** is now up for auction!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Starting Bid", value=f"${status['current_bid'] + 10}", inline=True)
            embed.add_field(name="Min Increment", value=f"${status['min_next_bid'] - status['current_bid']}", inline=True)
            embed.add_field(name="Property Value", value=f"${prop.price}", inline=True)
            embed.set_footer(text="Use !bid <amount> to bid | !pass to skip")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    
    @commands.hybrid_command(
        name="bid",
        description="Place a bid in the current auction",
        aliases=["offer"]
    )
    @app_commands.describe(amount="The amount you want to bid")
    async def bid(self, ctx: commands.Context, amount: int):
        """Place a bid in the current auction."""
        game = self.get_game(ctx.channel.id)
        
        if not game or not game.active_auction:
            await ctx.send("❌ No active auction!")
            return
        
        success, message = game.place_bid(ctx.author.id, amount)
        
        if success:
            status = game.get_auction_status()
            entity = game.players.get(ctx.author.id) or game.npcs.get(ctx.author.id)
            
            embed = discord.Embed(
                title="💰 New Highest Bid!",
                description=f"**{entity.username}** bids **${amount}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Property", value=status['property'], inline=True)
            embed.add_field(name="Current Bid", value=f"${status['current_bid']}", inline=True)
            embed.add_field(name="Next Min Bid", value=f"${status['min_next_bid']}", inline=True)
            embed.set_footer(text="Other players: use !bid <higher amount> or !pass")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    
    @commands.hybrid_command(
        name="pass",
        description="Pass on bidding in the current auction",
        aliases=["skip", "passbid"]
    )
    async def pass_bid(self, ctx: commands.Context):
        """Pass on bidding in the current auction."""
        game = self.get_game(ctx.channel.id)
        
        if not game or not game.active_auction:
            await ctx.send("❌ No active auction!")
            return
        
        success, message = game.pass_bid(ctx.author.id)
        
        if success:
            await ctx.send(f"⏭️ {message}")
            
            # Check if auction ended
            if not game.active_auction:
                # Auction ended, show result
                pass
        else:
            await ctx.send(f"❌ {message}")
    
    @commands.hybrid_command(
        name="auctionstatus",
        description="View the current auction status",
        aliases=["auctioninfo", "bidstatus"]
    )
    async def auction_status(self, ctx: commands.Context):
        """View the current auction status."""
        game = self.get_game(ctx.channel.id)
        
        if not game:
            await ctx.send("❌ No game found!")
            return
        
        if not game.active_auction:
            await ctx.send("ℹ️ No active auction!")
            return
        
        status = game.get_auction_status()
        prop = game.board.properties[game.active_auction.property_pos]
        
        embed = discord.Embed(
            title="🔨 Current Auction",
            description=f"**{status['property']}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Current Bid", value=f"${status['current_bid']}", inline=True)
        embed.add_field(name="Highest Bidder", value=status['highest_bidder'] or "No bids yet", inline=True)
        embed.add_field(name="Next Min Bid", value=f"${status['min_next_bid']}", inline=True)
        embed.add_field(name="Passes", value=str(status['pass_count']), inline=True)
        embed.add_field(name="Property Price", value=f"${prop.price}", inline=True)
        embed.add_field(name="Rent", value=f"${prop.rent}", inline=True)
        embed.set_footer(text="Use !bid <amount> to bid | !pass to skip your turn")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(
        name="status",
        description="View your current status",
        aliases=["stats", "info", "me"]
    )
    async def player_status(self, ctx: commands.Context):
        """View player status."""
        game = self.get_game(ctx.channel.id)
        
        if not game:
            await ctx.send("❌ No game found!")
            return
        
        player = game.players.get(ctx.author.id)
        if not player:
            await ctx.send("❌ You're not in this game!")
            return
        
        embed = discord.Embed(
            title=f"👤 {player.username}'s Status",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="💰 Money", value=f"${player.money}", inline=True)
        embed.add_field(name="📍 Position", value=str(player.position), inline=True)
        embed.add_field(name="🏠 Properties", value=str(len(player.properties)), inline=True)
        
        if player.in_jail:
            embed.add_field(name="⛓️ In Jail", value=f"{player.jail_turns} turns remaining", inline=True)
        
        embed.add_field(name="💀 Bankrupt", value="Yes" if player.bankrupt else "No", inline=True)
        
        # List properties
        if player.properties:
            prop_names = []
            for pos in player.properties:
                prop = game.board.properties.get(pos)
                if prop:
                    prop_names.append(f"{prop.name} (${prop.price})")
            
            if prop_names:
                embed.add_field(
                    name="📋 Your Properties",
                    value="\n".join(prop_names[:5]),  # Show first 5
                    inline=False
                )
                if len(prop_names) > 5:
                    embed.set_footer(text=f"... and {len(prop_names) - 5} more")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(
        name="board",
        description="View the game board state",
        aliases=["game", "state"]
    )
    async def view_board(self, ctx: commands.Context):
        """View the current game board state."""
        game = self.get_game(ctx.channel.id)
        
        if not game or not game.game_started:
            await ctx.send("❌ No active game!")
            return
        
        state = game.get_game_state_embed()
        
        embed = discord.Embed(
            title="🎩 Monopoly Game State",
            description=f"Turn #{state['turn']} | Current: {state['current_player']}",
            color=discord.Color.purple()
        )
        
        for player_data in state['players']:
            status_emoji = "🎲" if player_data['status'] else ""
            if player_data['status'] == "💀 Bankrupt":
                status_emoji = "💀"
            
            embed.add_field(
                name=f"{status_emoji} {player_data['name']}",
                value=f"💰 ${player_data['money']} | 📍 Pos {player_data['position']} | 🏠 {player_data['properties']} props",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(
        name="end",
        description="End the current game",
        aliases=["stop", "finish"]
    )
    async def end_game(self, ctx: commands.Context):
        """End the current game."""
        game = self.get_game(ctx.channel.id)
        
        if not game:
            await ctx.send("❌ No game found!")
            return
        
        # Determine winner (most money and properties)
        winner = None
        max_score = 0
        
        for player in game.players.values():
            if not player.bankrupt:
                score = player.money + sum(
                    game.board.properties[p].price for p in player.properties if p in game.board.properties
                )
                if score > max_score:
                    max_score = score
                    winner = player
        
        embed = discord.Embed(
            title="🏆 Game Over!",
            description="The Monopoly game has ended!",
            color=discord.Color.gold()
        )
        
        if winner:
            embed.add_field(name="🥇 Winner", value=winner.username, inline=True)
            embed.add_field(name="💰 Final Wealth", value=f"${max_score}", inline=True)
        else:
            embed.add_field(name="Result", value="No winner (all bankrupt)", inline=True)
        
        # Clean up
        del self.games[ctx.channel.id]
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(
        name="houses",
        description="Buy a house for a property you own",
        aliases=["buyhouse", "buildhouse", "build"]
    )
    @app_commands.describe(property_name="Name or position of the property")
    async def buy_house_cmd(self, ctx: commands.Context, *, property_name: str):
        """Buy a house for one of your properties."""
        game = self.get_game(ctx.channel.id)
        if not game or not game.game_started:
            await ctx.send("❌ No active game! Use `!start` to begin.")
            return
        
        player = game.get_current_player()
        if not player or player.user_id != ctx.author.id:
            await ctx.send("❌ Not your turn!")
            return
        
        # Find property by name or position
        prop_pos = None
        try:
            prop_pos = int(property_name)
        except ValueError:
            for pos, prop in game.board.properties.items():
                if property_name.lower() in prop.name.lower():
                    prop_pos = pos
                    break
        
        if prop_pos is None or prop_pos not in game.board.properties:
            await ctx.send("❌ Invalid property! Use property name or position number.")
            return
        
        success, message = game.buy_house_for_player(player, prop_pos)
        
        if success:
            embed = discord.Embed(title="🏠 House Built!", description=message, color=discord.Color.green())
            prop = game.board.properties[prop_pos]
            embed.add_field(name="Property", value=prop.name, inline=True)
            embed.add_field(name="Houses", value=f"{prop.houses}/4", inline=True)
            embed.add_field(name="Current Rent", value=f"${prop.get_rent()}", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    
    @commands.hybrid_command(
        name="hotel",
        description="Buy a hotel for a property (requires 4 houses)",
        aliases=["buyhotel", "buildhotel"]
    )
    @app_commands.describe(property_name="Name or position of the property")
    async def buy_hotel_cmd(self, ctx: commands.Context, *, property_name: str):
        """Buy a hotel for one of your properties."""
        game = self.get_game(ctx.channel.id)
        if not game or not game.game_started:
            await ctx.send("❌ No active game! Use `!start` to begin.")
            return
        
        player = game.get_current_player()
        if not player or player.user_id != ctx.author.id:
            await ctx.send("❌ Not your turn!")
            return
        
        # Find property by name or position
        prop_pos = None
        try:
            prop_pos = int(property_name)
        except ValueError:
            for pos, prop in game.board.properties.items():
                if property_name.lower() in prop.name.lower():
                    prop_pos = pos
                    break
        
        if prop_pos is None or prop_pos not in game.board.properties:
            await ctx.send("❌ Invalid property! Use property name or position number.")
            return
        
        success, message = game.buy_hotel_for_player(player, prop_pos)
        
        if success:
            embed = discord.Embed(title="🏨 Hotel Built!", description=message, color=discord.Color.gold())
            prop = game.board.properties[prop_pos]
            embed.add_field(name="Property", value=prop.name, inline=True)
            embed.add_field(name="Status", value="🏨 HOTEL", inline=True)
            embed.add_field(name="New Rent", value=f"${prop.get_rent()}", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    
    @commands.hybrid_command(
        name="mortgage",
        description="Mortgage a property to get cash",
        aliases=["mortgageprop", "mort"]
    )
    @app_commands.describe(property_name="Name or position of the property")
    async def mortgage_cmd(self, ctx: commands.Context, *, property_name: str):
        """Mortgage one of your properties to get quick cash."""
        game = self.get_game(ctx.channel.id)
        if not game or not game.game_started:
            await ctx.send("❌ No active game! Use `!start` to begin.")
            return
        
        player = game.get_current_player()
        if not player or player.user_id != ctx.author.id:
            await ctx.send("❌ Not your turn!")
            return
        
        # Find property by name or position
        prop_pos = None
        try:
            prop_pos = int(property_name)
        except ValueError:
            for pos, prop in game.board.properties.items():
                if property_name.lower() in prop.name.lower():
                    prop_pos = pos
                    break
        
        if prop_pos is None or prop_pos not in game.board.properties:
            await ctx.send("❌ Invalid property! Use property name or position number.")
            return
        
        success, message = game.mortgage_property_for_player(player, prop_pos)
        
        if success:
            prop = game.board.properties[prop_pos]
            embed = discord.Embed(title="📜 Property Mortgaged!", description=message, color=discord.Color.orange())
            embed.add_field(name="Property", value=prop.name, inline=True)
            embed.add_field(name="Cash Received", value=f"${prop.get_mortgage_value()}", inline=True)
            embed.add_field(name="To Unmortgage", value=f"${prop.get_unmortgage_cost()}", inline=True)
            embed.set_footer(text="⚠️ Mortgaged properties don't collect rent!")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    
    @commands.hybrid_command(
        name="unmortgage",
        description="Unmortgage a property to activate it again",
        aliases=["unmortgageprop", "unmort"]
    )
    @app_commands.describe(property_name="Name or position of the property")
    async def unmortgage_cmd(self, ctx: commands.Context, *, property_name: str):
        """Unmortgage one of your properties."""
        game = self.get_game(ctx.channel.id)
        if not game or not game.game_started:
            await ctx.send("❌ No active game! Use `!start` to begin.")
            return
        
        player = game.get_current_player()
        if not player or player.user_id != ctx.author.id:
            await ctx.send("❌ Not your turn!")
            return
        
        # Find property by name or position
        prop_pos = None
        try:
            prop_pos = int(property_name)
        except ValueError:
            for pos, prop in game.board.properties.items():
                if property_name.lower() in prop.name.lower():
                    prop_pos = pos
                    break
        
        if prop_pos is None or prop_pos not in game.board.properties:
            await ctx.send("❌ Invalid property! Use property name or position number.")
            return
        
        success, message = game.unmortgage_property_for_player(player, prop_pos)
        
        if success:
            prop = game.board.properties[prop_pos]
            embed = discord.Embed(title="✅ Property Unmortgaged!", description=message, color=discord.Color.green())
            embed.add_field(name="Property", value=prop.name, inline=True)
            embed.add_field(name="Cost Paid", value=f"${prop.get_unmortgage_cost()}", inline=True)
            embed.set_footer(text="✓ Property now collects rent again!")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    
    @commands.hybrid_command(
        name="sellhouse",
        description="Sell a house/hotel back to the bank",
        aliases=["sellhouse", "sellhotel", "demolish"]
    )
    @app_commands.describe(property_name="Name or position of the property")
    async def sell_house_cmd(self, ctx: commands.Context, *, property_name: str):
        """Sell a house or hotel back to the bank for half price."""
        game = self.get_game(ctx.channel.id)
        if not game or not game.game_started:
            await ctx.send("❌ No active game! Use `!start` to begin.")
            return
        
        player = game.get_current_player()
        if not player or player.user_id != ctx.author.id:
            await ctx.send("❌ Not your turn!")
            return
        
        # Find property by name or position
        prop_pos = None
        try:
            prop_pos = int(property_name)
        except ValueError:
            for pos, prop in game.board.properties.items():
                if property_name.lower() in prop.name.lower():
                    prop_pos = pos
                    break
        
        if prop_pos is None or prop_pos not in game.board.properties:
            await ctx.send("❌ Invalid property! Use property name or position number.")
            return
        
        success, message = game.sell_house_for_player(player, prop_pos)
        
        if success:
            prop = game.board.properties[prop_pos]
            embed = discord.Embed(title="💰 House Sold!", description=message, color=discord.Color.dark_gold())
            embed.add_field(name="Property", value=prop.name, inline=True)
            house_cost = prop.get_house_cost()
            embed.add_field(name="Cash Received", value=f"${house_cost // 2}", inline=True)
            if prop.hotel:
                embed.add_field(name="Status", value="🏨 Has Hotel", inline=True)
            else:
                embed.add_field(name="Houses", value=f"{prop.houses}/4", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    
    @commands.hybrid_command(
        name="develop",
        description="View development options for your properties",
        aliases=["development", "buildings", "improve"]
    )
    async def develop_cmd(self, ctx: commands.Context):
        """View which properties can be developed with houses/hotels."""
        game = self.get_game(ctx.channel.id)
        if not game or not game.game_started:
            await ctx.send("❌ No active game! Use `!start` to begin.")
            return
        
        player = game.get_current_player()
        if not player or player.user_id != ctx.author.id:
            await ctx.send("❌ Not your turn!")
            return
        
        dev_info = game.get_property_development_info(player)
        
        embed = discord.Embed(
            title="🏗️ Property Development Options",
            description=f"Your money: **${player.money}**",
            color=discord.Color.blue()
        )
        
        if dev_info["developable"]:
            can_build = [p for p in dev_info["developable"] if p.get("can_develop", False)]
            cant_build = [p for p in dev_info["developable"] if not p.get("can_develop", True)]
            
            if can_build:
                build_text = ""
                for prop in can_build[:5]:  # Show first 5
                    if prop.get("hotel"):
                        build_text += f"**{prop['name']}**: 🏨 Hotel (max)\n"
                    elif prop["houses"] == 4:
                        build_text += f"**{prop['name']}**: Can buy HOTEL for ${prop.get('hotel_cost', 0)}\n"
                    else:
                        build_text += f"**{prop['name']}**: {prop['houses']}/4 houses - House costs ${prop.get('house_cost', 0)}\n"
                
                if len(can_build) > 5:
                    build_text += f"...and {len(can_build) - 5} more"
                
                embed.add_field(name="✅ Can Develop", value=build_text or "None", inline=False)
            
            if cant_build:
                cant_text = ""
                for prop in cant_build[:5]:
                    cant_text += f"**{prop['name']}**: {prop.get('reason', 'Cannot build')}\n"
                
                if len(cant_build) > 5:
                    cant_text += f"...and {len(cant_build) - 5} more"
                
                embed.add_field(name="❌ Cannot Develop Yet", value=cant_text or "None", inline=False)
        else:
            embed.add_field(name="Properties", value="No developable properties owned!", inline=False)
        
        if dev_info["mortgaged"]:
            mort_text = ""
            for prop in dev_info["mortgaged"][:5]:
                mort_text += f"**{prop['name']}**: Mortgage ${prop['mortgage_value']} | Unmortgage ${prop['unmortgage_cost']}\n"
            
            if len(dev_info["mortgaged"]) > 5:
                mort_text += f"...and {len(dev_info['mortgaged']) - 5} more"
            
            embed.add_field(name="📜 Mortgaged Properties", value=mort_text, inline=False)
        
        embed.set_footer(text="Use !house <property> or !hotel <property> to build")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(
        name="help_monopoly",
        description="Show Monopoly command help",
        aliases=["monopoly_help", "commands"]
    )
    async def monopoly_help(self, ctx: commands.Context):
        """Show help for Monopoly commands."""
        embed = discord.Embed(
            title="🎩 Monopoly Bot Commands",
            description="Complete guide to playing Monopoly with NPCs!",
            color=discord.Color.blue()
        )
        
        commands_list = [
            ("🎮 Game Management", 
             "`!start [max_players] [npcs]` - Create new game\n`!join` - Join game\n`!leave` - Leave game\n`!addnpc [personality]` - Add NPC opponent\n`!begin` - Start game"),
            ("🎲 Playing",
             "`!roll` - Roll dice & move\n`!buy` - Buy property\n`!status` - View your stats\n`!board` - View all players\n`!payrent` - Pay rent when landed"),
            ("🏗️ Houses & Hotels",
             "`!house <property>` - Buy a house\n`!hotel <property>` - Buy a hotel (needs 4 houses)\n`!sellhouse <property>` - Sell house/hotel\n`!develop` - View development options"),
            ("📜 Mortgages",
             "`!mortgage <property>` - Mortgage property for cash\n`!unmortgage <property>` - Restore property\nGet 50% value, pay 55% to restore!"),
            ("🔨 Auction System",
             "`!auction` - Start auction for current property\n`!bid <amount>` - Place a bid\n`!pass` - Pass on bidding\n`!auctionstatus` - View auction info"),
            ("🤖 NPC Features",
             "NPCs auto-play their turns!\nPersonalities: aggressive, conservative, balanced, random\nAuto-buy properties & pay rent\nNPCs participate in auctions!"),
            ("🃏 Cards",
             "Chance & Community Chest\n28 unique cards with various effects\nAuto-processed when landed on")
        ]
        
        for category, cmds in commands_list:
            embed.add_field(name=category, value=cmds, inline=False)
        
        embed.set_footer(text="Use !help <command> for more details | Hybrid: works with / and !")
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function to load the cog."""
    await bot.add_cog(MonopolyCommands(bot))
