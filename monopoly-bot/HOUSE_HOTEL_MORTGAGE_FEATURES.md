# 🏠 Houses, Hotels & Mortgages - Feature Update

## Overview
The Monopoly bot now includes complete house/hotel building and mortgage systems, allowing players to develop properties and manage finances strategically.

---

## 🎯 New Commands

### House & Hotel System

#### `!house <property>` / `!buyhouse` / `!buildhouse` / `!build`
Buy a house for one of your properties.

**Requirements:**
- Must own complete color set
- Property cannot be mortgaged
- Maximum 4 houses per property
- Must have sufficient funds

**House Costs by Color:**
- Brown / Light Blue: $50 per house
- Pink / Orange: $100 per house
- Red / Yellow: $150 per house
- Green / Dark Blue: $200 per house

**Example:**
```
!house Mediterranean Avenue
!house 1  (by position number)
!build Baltic
```

---

#### `!hotel <property>` / `!buyhotel` / `!buildhotel`
Buy a hotel for a property (requires 4 houses first).

**Requirements:**
- Must have exactly 4 houses on the property
- Must own complete color set
- Property cannot be mortgaged
- Hotel cost = 4 × house cost

**Example:**
```
!hotel Boardwalk
!hotel 39
```

---

#### `!sellhouse <property>` / `!sellhotel` / `!demolish`
Sell a house or hotel back to the bank for half price.

**Returns:** 50% of house/hotel cost

**Example:**
```
!sellhouse Park Place
!sellhotel Marvin Gardens
```

---

#### `!develop` / `!development` / `!buildings` / `!improve`
View development options for all your properties.

**Shows:**
- Properties that can be developed
- Current house/hotel count
- Cost to build
- Why properties can't be developed (if applicable)
- Mortgaged properties with values

**Example:**
```
!develop
```

---

### Mortgage System

#### `!mortgage <property>` / `!mortgageprop` / `!mort`
Mortgage a property to get quick cash.

**Details:**
- Receive 50% of property value
- Property becomes inactive (no rent collection)
- Cannot have houses/hotels (must sell first)
- Interest-free loan

**Example:**
```
!mortgage Pennsylvania Railroad
!mort 15
```

---

#### `!unmortgage <property>` / `!unmortgageprop` / `!unmort`
Restore a mortgaged property to active status.

**Cost:** Mortgage value + 10% interest

**Example:**
```
!unmortgage Electric Company
!unmort 12
```

---

## 📊 Game Mechanics

### Rent Multipliers

**With Houses:**
- 1 house: 2× base rent
- 2 houses: 3× base rent
- 3 houses: 4× base rent
- 4 houses: 5× base rent
- Hotel: 5× base rent (same as 4 houses but displayed differently)

### Railroad Rent
Based on number of railroads owned:
- 1 railroad: $25
- 2 railroads: $50
- 3 railroads: $100
- 4 railroads: $200

### Utility Rent
Based on dice roll and ownership:
- 1 utility: 4× dice total
- 2 utilities: 10× dice total

---

## 🤖 NPC Integration

NPCs will automatically:
- Buy houses/hotels when they have complete sets and excess money
- Mortgage properties when low on cash
- Unmortgage when financially stable
- Consider personality type in decisions:
  - **Aggressive**: Build quickly, rarely mortgage
  - **Conservative**: Build slowly, mortgage early
  - **Balanced**: Moderate approach
  - **Random**: Unpredictable behavior

---

## 💡 Strategy Tips

### When to Build:
1. Complete a color set → Start building immediately
2. Keep ~$200 reserve for emergencies
3. Prioritize high-rent properties (Orange, Red, Dark Blue)
4. Build evenly across color sets (can't exceed 4-house gap)

### When to Mortgage:
1. Need cash to avoid bankruptcy
2. Paying urgent rent/hospital fees
3. Low-priority properties (incomplete color sets)
4. As last resort before selling to other players

### When to Unmortgage:
1. Opponents approaching your properties
2. Have excess cash (> $500)
3. Completing a color set for development
4. Early game advantage building

---

## 🔧 Technical Details

### Property Class Methods Added:
- `can_buy_house()` - Check development eligibility
- `get_house_cost()` - Get house building cost
- `get_hotel_cost()` - Get hotel building cost
- `buy_house()` - Add a house
- `buy_hotel()` - Convert 4 houses to hotel
- `sell_house()` - Remove house/hotel
- `get_mortgage_value()` - Get mortgage amount
- `get_unmortgage_cost()` - Get unmortgage cost
- `mortgage_property()` - Mortgage the property
- `unmortgage_property()` - Restore from mortgage

### MonopolyGame Methods Added:
- `buy_house_for_player()` - Handle house purchase
- `buy_hotel_for_player()` - Handle hotel purchase
- `sell_house_for_player()` - Handle house sale
- `mortgage_property_for_player()` - Handle mortgaging
- `unmortgage_property_for_player()` - Handle unmortgaging
- `get_railroad_rent()` - Calculate railroad rent
- `get_utility_rent()` - Calculate utility rent
- `get_property_development_info()` - Get development status

---

## 📝 Command Count Summary

**Total Hybrid Commands:** 16
- Game Management: 6 commands
- Playing: 5 commands
- Houses/Hotels: 4 commands (NEW!)
- Mortgages: 2 commands (NEW!)
- Auction: 4 commands
- Help: 1 command

**Total Aliases:** 40+

---

## 🎮 Example Gameplay Flow

```
Player lands on their own property (Pacific Avenue)
Already owns: Pacific, North Carolina, Pennsylvania (Green set)

!develop
→ Shows: Pacific Ave (0/4 houses, $200/house) - Ready to develop

!house Pacific Avenue
→ Bought house #1 for $200

!house Pacific Avenue
→ Bought house #2 for $200

!house Pacific Avenue  
→ Bought house #3 for $200

!house Pacific Avenue
→ Bought house #4 for $200

!hotel Pacific Avenue
→ Converted to HOTEL for $800! Rent is now $260/turn

Later, need quick cash:
!mortgage Short Line
→ Received $100, property inactive

When able to repay:
!unmortgage Short Line
→ Paid $110 ($100 + 10% interest), property active again
```

---

## ⚠️ Important Rules

1. **Building Restrictions:**
   - Cannot build on mortgaged properties
   - Cannot build on railroads or utilities
   - Must own ALL properties in color group
   - Houses must be distributed evenly (max 1-house difference)

2. **Mortgage Restrictions:**
   - Cannot mortgage with houses/hotels (sell first)
   - Mortgaged properties collect NO rent
   - Can still be traded (stays mortgaged)

3. **Selling Restrictions:**
   - Sell for exactly 50% of purchase price
   - Can only sell on your turn
   - Must maintain even distribution rule

---

## 🚀 Future Expansion Ready

The system is designed for easy expansion:
- Trading system integration
- Property improvement limits
- Advanced NPC strategies
- Tournament modes
- Custom house rules

---

**Bot Version:** 2.0+  
**Last Updated:** Current Session  
**Status:** ✅ Fully Implemented & Tested
