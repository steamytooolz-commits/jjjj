# 🎩 Discord Monopoly Bot with NPCs

A full-featured Monopoly bot for Discord with intelligent NPC opponents, extensive command handler, and support for both slash commands (`/`) and prefix commands (`!`).

## Features

### 🎮 Game Features
- **Classic Monopoly gameplay** with 40 spaces
- **28 Properties** including railroads and utilities
- **Expanded Chance & Community Chest** (28 unique cards!)
- **Smart NPC opponents** with unique personalities
- **Player management** (1-8 players + NPCs)
- **Property buying, selling, and rent collection**
- **Jail mechanics** with Get Out of Jail Free cards
- **Bankruptcy system**
- **Automatic winner determination**

### 🤖 NPC System
- **4 Personalities**: Aggressive, Conservative, Balanced, Random
- **Auto-play turns** - NPCs roll, move, buy, and pay automatically
- **Strategic decision making** based on personality type
- **Seamless integration** - Play solo or with friends vs NPCs
- **Personality-based trading** - NPCs make trade offers

### 🔨 Auction System
- **Dynamic property auctions** when players decline to buy
- **Interactive bidding** with button prompts
- **NPC participation** in auctions based on personality
- **Fair market prices** through competitive bidding
- **5 auction commands** for full control

### ⚙️ Command Handler Features
- **Hybrid commands** - Works with both `/` and `!` prefixes
- **15+ Commands** with multiple aliases each
- **Command categories** - Organized command structure
- **Cooldown system** - Prevent spam
- **Permission checks** - Control access
- **Help system** - Built-in help commands
- **Error handling** - Graceful error messages
- **Beautiful embeds** - Formatted responses

## Installation

### Prerequisites
- Python 3.8+
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))

### Setup Steps

1. **Clone or download this repository**

2. **Install dependencies:**
   ```bash
   cd monopoly-bot
   pip install -r requirements.txt
   ```

3. **Configure your bot token:**
   
   Create a `.env` file in the `monopoly-bot` directory:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_actual_bot_token_here
   ```

4. **Run the bot:**
   ```bash
   python main.py
   ```

## Commands

### 🎮 Game Management

| Command | Aliases | Description |
|---------|---------|-------------|
| `!start [max_players]` | `!newgame`, `!create` | Start a new Monopoly game (2-4 players) |
| `!join` | `!enter` | Join an existing game |
| `!leave` | `!exit`, `!quit` | Leave the current game |
| `!begin` | `!play`, `!launch` | Start the game (requires 2+ players) |
| `!end` | `!stop`, `!finish` | End the current game |

### 🎲 Playing the Game

| Command | Aliases | Description |
|---------|---------|-------------|
| `!roll` | `!throw`, `!dice` | Roll dice and move your piece |
| `!buy` | `!purchase` | Buy the property you landed on |
| `!status` | `!stats`, `!info`, `!me` | View your current status |
| `!board` | `!game`, `!state` | View the entire game board state |
| `!payrent` | `!pay` | Pay rent to property owner |

### 🔨 Auction System

| Command | Aliases | Description |
|---------|---------|-------------|
| `!auction` | `!startauction` | Start an auction for current property |
| `!bid <amount>` | `!offer` | Place a bid in active auction |
| `!pass` | `!skip`, `!passbid` | Pass on bidding this round |
| `!auctionstatus` | `!auctioninfo`, `!bidstatus` | View current auction details |

### ℹ️ Help & Info

| Command | Aliases | Description |
|---------|---------|-------------|
| `!help_monopoly` | `!monopoly_help`, `!commands` | Show all Monopoly commands |

## Usage Example

1. **Start a game:**
   ```
   !start
   ```

2. **Players join:**
   ```
   !join
   ```

3. **Begin the game:**
   ```
   !begin
   ```

4. **Take turns:**
   ```
   !roll          # Roll the dice
   !buy           # Buy the property (if you want it)
   !auction       # Start auction if you decline to buy
   !bid 150       # Bid in an auction
   !pass          # Pass on bidding
   !status        # Check your money and properties
   ```

5. **End the game:**
   ```
   !end           # Determine winner and end game
   ```

## Bot Configuration

### Creating a Discord Bot Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent
6. Copy the bot token and add it to your `.env` file
7. Go to "OAuth2" → "URL Generator"
8. Select scopes: `bot`, `applications.commands`
9. Select permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
10. Use the generated URL to invite the bot to your server

## Project Structure

```
monopoly-bot/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── cogs/
│   ├── monopoly_logic.py   # Game logic (board, properties, players)
│   └── monopoly_commands.py # Discord commands
├── utils/
│   └── command_handler.py  # Extensive command handler
└── data/                   # Future: Save/load game data
```

## Advanced Features

### Command Handler Capabilities

The bot includes an extensive command handler (`utils/command_handler.py`) with:

- **CommandConfig dataclass** - Configure commands with metadata
- **Cooldown management** - Per-user, per-command cooldowns
- **Permission system** - Check Discord permissions
- **Category organization** - Group commands logically
- **Help embed generation** - Automatic help message creation
- **Hybrid command support** - Both slash and prefix commands

### Game Logic

The game logic (`cogs/monopoly_logic.py`) implements:

- **Complete 40-space board** with all classic properties
- **Property ownership** and rent calculation
- **House/hotel system** (ready for expansion)
- **Mortgage system** (ready for expansion)
- **Chance/Community Chest cards** with various effects
- **Player movement** with GO collection
- **Bankruptcy detection**

## Customization

### Adding New Commands

1. Add the command to `cogs/monopoly_commands.py`:
   ```python
   @commands.hybrid_command(
       name="yourcommand",
       description="Description here",
       aliases=["alias1", "alias2"]
   )
   async def your_command(self, ctx: commands.Context):
       # Your command logic here
       await ctx.send("Response!")
   ```

2. The command will automatically be available as both `!yourcommand` and `/yourcommand`

### Modifying Game Rules

Edit `cogs/monopoly_logic.py` to change:
- Starting money (default: $1500)
- Property prices and rents
- GO reward (default: $200)
- Number of players allowed

## Troubleshooting

### Bot doesn't respond to commands
- Ensure the bot has proper permissions in your server
- Check that Message Content Intent is enabled
- Verify the bot token is correct

### Slash commands not showing
- Wait a few minutes for Discord to sync commands
- Try kicking and re-inviting the bot
- Run `!help_monopoly` to verify the bot is working

### Error: DISCORD_TOKEN not found
- Make sure you created a `.env` file (not `.env.txt`)
- Check that the token is correctly formatted
- Ensure no extra spaces or quotes around the token

## License

This project is open source and available for personal use.

## Support

For issues or feature requests, please check the documentation or extend the code as needed.

---

**Enjoy playing Monopoly on Discord! 🎩🎲**
