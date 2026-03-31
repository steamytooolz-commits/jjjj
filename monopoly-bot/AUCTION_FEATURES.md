# 🎩 Monopoly Bot - Auction System

## Overview
The auction system allows players to bid on properties they or others decline to purchase at face value. This adds strategic depth and ensures properties always get sold!

## How Auctions Work

### Starting an Auction

**Automatic Prompt:**
- When a player uses `!buy` but declines (doesn't have enough money or chooses not to buy), they get a button prompt to start an auction

**Manual Start:**
- Use `!auction` or `!startauction` during your turn when on an unowned property
- Any player can request an auction for the current player's landed property

### Bidding Process

1. **Starting Bid**: Set at 25% of property value (minimum $10)
2. **Minimum Increment**: $10 above current bid
3. **Turn-Based**: Players take turns bidding or passing
4. **NPC Participation**: NPCs automatically bid based on their personality:
   - **Aggressive**: Bids aggressively, often overpays
   - **Conservative**: Only bids if great value
   - **Balanced**: Reasonable bidding strategy
   - **Random**: Unpredictable bidding

### Commands

#### `!auction` / `!startauction`
Start an auction for the current property.
```
!auction
```

#### `!bid <amount>` / `!offer <amount>`
Place a bid in the active auction.
```
!bid 150
!offer 200
```

#### `!pass` / `!skip` / `!passbid`
Pass on bidding this round. If all but one player pass, the auction ends.
```
!pass
```

#### `!auctionstatus` / `!auctioninfo` / `!bidstatus`
View current auction details.
```
!auctionstatus
```

### Auction Rules

- **Eligibility**: All non-bankrupt players with at least $10 can bid
- **Winning**: Highest bidder when all others pass wins the property
- **Payment**: Winner pays immediately and receives the property
- **No Reserve**: Property sells regardless of final price
- **One at a Time**: Only one auction can be active per game

### NPC Bidding Behavior

| Personality | Strategy |
|------------|----------|
| Aggressive | Bids up to 80% of money, competes fiercely |
| Conservative | Only bids if under market value, keeps cash reserve |
| Balanced | Bids reasonably, considers property value |
| Random | Random decisions, unpredictable |

### Example Auction Flow

```
Player 1 lands on Boardwalk ($400)
Player 1: !buy
Bot: ❌ Not enough money! Start an auction? [Buttons: Start Auction | Cancel]
Player 1: [Clicks Start Auction]
Bot: 🔨 Auction Started! Boardwalk is now up for auction! Starting bid: $100

Player 2: !bid 100
Bot: 💰 Player 2 bids $100! Next min bid: $110

NPC 1 (Aggressive): !bid 150
Bot: 💰 NPC 1 bids $150! Next min bid: $160

Player 2: !bid 160
Bot: 💰 Player 2 bids $160!

Player 3: !pass
Bot: ⏭️ Player 3 passed.

Player 2: !pass
Bot: ⏭️ Player 2 passed.

🏆 Auction won by NPC 1 for $150! They bought Boardwalk.
```

### Strategic Tips

1. **For Humans**: 
   - Watch NPC personalities - aggressive ones may overbid
   - Pass early to let NPCs drive up the price
   - Snipe at the end when NPCs have passed

2. **Against Aggressive NPCs**:
   - Let them overpay early
   - Save money for better properties
   - They often run out of cash

3. **Against Conservative NPCs**:
   - They'll drop out early
   - Good chance to get properties cheap

4. **General Strategy**:
   - Don't get caught in bidding wars
   - Know when to fold
   - Consider property's strategic value (completing sets)

## Integration with Existing Features

- Works seamlessly with NPC auto-play
- Auctions pause normal turn order
- After auction, game resumes from where it left off
- Properties bought at auction generate rent normally
- Can build houses/hotels on auctioned properties

## Future Enhancements (Planned)

- Auto-bid limits for humans
- Auction history tracking
- Statistics on auction wins/losses
- Special auction events
- Trade offers during auctions
