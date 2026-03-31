# 🎉 Monopoly Bot - NPC & Community Chest Upgrade

## What's New

### 🤖 NPC System
- **Full NPC implementation** with 4 distinct personalities:
  - `aggressive` - Buys properties freely, never sells
  - `conservative` - Only buys with plenty of cash, sells when needed
  - `balanced` - Reasonable buying strategy
  - `random` - Unpredictable behavior

- **Auto-play functionality**: NPCs automatically:
  - Roll dice and move
  - Buy properties based on personality
  - Pay rent when landing on owned properties
  - Draw and process Chance/Community Chest cards
  - Pass GO and collect $200

- **Smart decision making**:
  - Property purchase logic based on remaining money
  - Rent payment automation
  - Trade offer generation (ready for future expansion)

### 🃏 Expanded Cards System
- **28 unique cards** (up from 16):
  - 14 Chance cards
  - 14 Community Chest cards
  
- **New card effects**:
  - `move_to` - Move to specific properties (Illinois Ave, St. Charles, Boardwalk)
  - `pay_each` - Pay all players
  - `collect_all` - Collect from all players
  - `get_out_jail` - Get Out of Jail Free cards
  - `repairs` - Property repair costs

- **Card target system**: Cards can affect self or all players

### 🎮 Enhanced Commands
- **New commands added**:
  - `/addnpc [personality]` - Add NPC before game starts
  - `/start [max_players] [npcs_enabled]` - Now supports NPC toggle
  
- **Updated commands**:
  - `/roll` - Auto-processes Chance/Community Chest, triggers next NPC turn
  - `/begin` - Shows NPCs in player list
  - `/board` - Displays both humans and NPCs
  - `/help_monopoly` - Updated with NPC features

### 🔄 Gameplay Improvements
- **Seamless turn flow**: Human → NPC → Human automatically
- **Mixed games**: Play with friends AND NPCs together
- **Solo play**: Start a game alone vs 2-3 NPCs
- **Flexible player count**: 1-8 total participants

## Technical Changes

### Files Modified
1. **cogs/monopoly_logic.py** (+400 lines)
   - Added `NPC` class with full player interface
   - Added `buy_property_npc()` method
   - Added `pay_rent_npc()` method
   - Added `process_card_effect()` for unified card handling
   - Enhanced `MonopolyGame` with NPC management
   - Updated `get_game_state_embed()` to include NPCs

2. **cogs/monopoly_commands.py** (+150 lines)
   - Added `process_npc_turn()` async method
   - Enhanced `roll_dice()` with card processing
   - Added `add_npc()` command
   - Updated all display commands for NPC support

3. **README.md** - Updated documentation

## Usage Examples

### Start a Solo Game vs NPCs
```
/start max_players:4 npcs_enabled:true
/begin
/roll  # Your turn
# NPC automatically plays after you
```

### Add Specific NPC Personalities
```
/start
/addnpc personality:aggressive
/addnpc personality:conservative
/begin
```

### Mixed Human + NPC Game
```
/start max_players:6
/join  # You join
/friend joins
/addnpc personality:balanced
/begin  # 2 humans + 1 NPC
```

## Personality Guide

| Personality | Buying Strategy | Cash Reserve | Best For |
|-------------|----------------|--------------|----------|
| Aggressive | Buy almost anything | $0+ | Challenging opponent |
| Conservative | Only safe purchases | $300+ | Easy opponent |
| Balanced | Reasonable buys | $150+ | Fair game |
| Random | 70% buy chance | Varies | Unpredictable fun |

## Future Enhancements (Ready Foundation)
- NPC trading between each other
- Advanced property development (houses/hotels)
- NPC alliance systems
- Custom NPC names and avatars
- Tournament mode with multiple NPCs

## Code Quality
- ✅ All imports working
- ✅ Type hints throughout
- ✅ Comprehensive error handling
- ✅ Clean separation of concerns
- ✅ Extensible architecture
