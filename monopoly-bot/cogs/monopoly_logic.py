"""
Monopoly Game Logic Module
Handles board, properties, players, and game mechanics.
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class PropertyColor(Enum):
    BROWN = "Brown"
    LIGHT_BLUE = "Light Blue"
    PINK = "Pink"
    ORANGE = "Orange"
    RED = "Red"
    YELLOW = "Yellow"
    GREEN = "Green"
    DARK_BLUE = "Dark Blue"
    RAILROAD = "Railroad"
    UTILITY = "Utility"


@dataclass
class Property:
    """Represents a property on the board."""
    name: str
    position: int
    price: int
    rent: int
    color: PropertyColor
    owner: Optional[int] = None  # user_id
    houses: int = 0
    hotel: bool = False
    mortgage: bool = False
    
    def buy(self, user_id: int) -> bool:
        """Attempt to buy the property."""
        if self.owner is not None:
            return False
        self.owner = user_id
        return True
    
    def sell(self) -> bool:
        """Sell the property (remove owner)."""
        if self.owner is None:
            return False
        self.owner = None
        self.houses = 0
        self.hotel = False
        self.mortgage = False
        return True
    
    def get_rent(self) -> int:
        """Calculate current rent based on houses/hotel."""
        if self.mortgage:
            return 0
        
        base_rent = self.rent
        
        if self.hotel:
            return base_rent * 5
        
        if self.houses > 0:
            return base_rent * (1 + self.houses)
        
        return base_rent


@dataclass
class Player:
    """Represents a player in the game."""
    user_id: int
    username: str
    money: int = 1500
    position: int = 0
    properties: List[int] = field(default_factory=list)  # list of property positions
    in_jail: bool = False
    jail_turns: int = 0
    bankrupt: bool = False
    
    def pay(self, amount: int) -> bool:
        """Pay money. Returns False if can't pay (bankrupt)."""
        if self.money >= amount:
            self.money -= amount
            return True
        else:
            self.bankrupt = True
            return False
    
    def receive(self, amount: int):
        """Receive money."""
        self.money += amount
    
    def move(self, steps: int, board_size: int = 40):
        """Move player on the board."""
        old_position = self.position
        self.position = (self.position + steps) % board_size
        
        # Passed GO
        if self.position < old_position and steps > 0:
            self.receive(200)
            return True  # Passed GO
        return False


@dataclass
class Card:
    """Chance or Community Chest card."""
    text: str
    effect: str  # 'money', 'move', 'jail', 'collect', etc.
    value: int = 0
    position: int = 0
    target: str = "self"  # 'self', 'all', 'random'


@dataclass
class Auction:
    """Represents an active auction for a property."""
    property_pos: int
    starting_bid: int
    current_bid: int
    highest_bidder: Optional[int]  # user_id or npc_id
    bidders: Dict[int, int]  # user_id -> max_bid (bid limits)
    active: bool = True
    turn_index: int = 0  # Current bidder index in player order
    pass_count: int = 0  # Consecutive passes
    min_bid_increment: int = 10


@dataclass
class NPC:
    """Represents an AI-controlled NPC player."""
    user_id: int
    username: str
    money: int = 1500
    position: int = 0
    properties: List[int] = field(default_factory=list)
    in_jail: bool = False
    jail_turns: int = 0
    bankrupt: bool = False
    personality: str = "balanced"  # 'aggressive', 'conservative', 'balanced', 'random'
    strategy_seed: int = 0
    
    def pay(self, amount: int) -> bool:
        """Pay money. Returns False if can't pay (bankrupt)."""
        if self.money >= amount:
            self.money -= amount
            return True
        else:
            self.bankrupt = True
            return False
    
    def receive(self, amount: int):
        """Receive money."""
        self.money += amount
    
    def move(self, steps: int, board_size: int = 40):
        """Move player on the board."""
        old_position = self.position
        self.position = (self.position + steps) % board_size
        
        # Passed GO
        if self.position < old_position and steps > 0:
            self.receive(200)
            return True  # Passed GO
        return False
    
    def should_buy_property(self, prop: Property, game_state: dict) -> bool:
        """Determine if NPC should buy a property based on personality."""
        if self.money < prop.price:
            return False
        
        remaining_money = self.money - prop.price
        
        if self.personality == "aggressive":
            # Buy almost anything, even if low on cash
            return True
        elif self.personality == "conservative":
            # Only buy if plenty of money left
            return remaining_money >= 300
        elif self.personality == "balanced":
            # Buy if reasonable amount left
            return remaining_money >= 150
        else:  # random
            return random.random() > 0.3
    
    def should_sell_property(self, prop_pos: int, urgent: bool = False) -> bool:
        """Determine if NPC should sell a property."""
        if self.personality == "aggressive":
            return False  # Never sell unless bankrupt
        elif self.personality == "conservative":
            return True if urgent else random.random() > 0.7
        else:
            return urgent
    
    def make_trade_offer(self, other_player: 'Player', game_board: 'MonopolyBoard') -> Optional[dict]:
        """Generate a trade offer based on NPC personality."""
        if not self.properties or not other_player.properties:
            return None
        
        # Simple trade logic: try to complete color sets
        my_props = [game_board.properties[p] for p in self.properties if p in game_board.properties]
        their_props = [game_board.properties[p] for p in other_player.properties if p in game_board.properties]
        
        # Look for color matches
        my_colors = {}
        for prop in my_props:
            if prop.color not in my_colors:
                my_colors[prop.color] = []
            my_colors[prop.color].append(prop)
        
        their_colors = {}
        for prop in their_props:
            if prop.color not in their_colors:
                their_colors[prop.color] = []
            their_colors[prop.color].append(prop)
        
        # Try to find a trade that completes a set for us
        for color, their_list in their_colors.items():
            if color in my_colors and len(my_colors[color]) > 0:
                # We have some, they have some - potential trade
                if len(their_list) + len(my_colors[color]) >= 2:
                    # Propose trade
                    give_props = [p.position for p in my_colors[color][:1]]
                    get_props = [p.position for p in their_list[:1]]
                    
                    # Calculate money adjustment
                    give_value = sum(game_board.properties[p].price for p in give_props)
                    get_value = sum(game_board.properties[p].price for p in get_props)
                    money_diff = give_value - get_value
                    
                    if self.personality == "aggressive":
                        money_adjustment = max(0, money_diff - 50)  # Offer less
                    elif self.personality == "conservative":
                        money_adjustment = money_diff + 50  # Offer more
                    else:
                        money_adjustment = money_diff
                    
                    return {
                        "npc_gives": give_props,
                        "npc_gets": get_props,
                        "npc_money": money_adjustment if money_adjustment > 0 else 0,
                        "player_money": abs(money_adjustment) if money_adjustment < 0 else 0
                    }
        
        return None


class MonopolyBoard:
    """Classic Monopoly board with 40 spaces."""
    
    def __init__(self):
        self.properties: Dict[int, Property] = {}
        self.special_spaces: Dict[int, str] = {}  # position -> type
        self.chance_cards: List[Card] = []
        self.community_chest_cards: List[Card] = []
        self.board_size = 40
        
        self._setup_board()
        self._setup_cards()
    
    def _setup_board(self):
        """Set up the classic Monopoly board."""
        # Properties: (position, name, price, rent, color)
        property_data = [
            (1, "Mediterranean Avenue", 60, 2, PropertyColor.BROWN),
            (3, "Baltic Avenue", 60, 4, PropertyColor.BROWN),
            (5, "Reading Railroad", 200, 25, PropertyColor.RAILROAD),
            (6, "Oriental Avenue", 100, 6, PropertyColor.LIGHT_BLUE),
            (8, "Vermont Avenue", 100, 6, PropertyColor.LIGHT_BLUE),
            (9, "Connecticut Avenue", 120, 8, PropertyColor.LIGHT_BLUE),
            (11, "St. Charles Place", 140, 10, PropertyColor.PINK),
            (13, "States Avenue", 140, 10, PropertyColor.PINK),
            (14, "Virginia Avenue", 160, 12, PropertyColor.PINK),
            (15, "Pennsylvania Railroad", 200, 25, PropertyColor.RAILROAD),
            (16, "St. James Place", 180, 14, PropertyColor.ORANGE),
            (18, "Tennessee Avenue", 180, 14, PropertyColor.ORANGE),
            (19, "New York Avenue", 200, 16, PropertyColor.ORANGE),
            (21, "Kentucky Avenue", 220, 18, PropertyColor.RED),
            (23, "Indiana Avenue", 220, 18, PropertyColor.RED),
            (24, "Illinois Avenue", 240, 20, PropertyColor.RED),
            (25, "B. & O. Railroad", 200, 25, PropertyColor.RAILROAD),
            (26, "Atlantic Avenue", 260, 22, PropertyColor.YELLOW),
            (27, "Ventnor Avenue", 260, 22, PropertyColor.YELLOW),
            (29, "Marvin Gardens", 280, 24, PropertyColor.YELLOW),
            (31, "Pacific Avenue", 300, 26, PropertyColor.GREEN),
            (32, "North Carolina Avenue", 300, 26, PropertyColor.GREEN),
            (34, "Pennsylvania Avenue", 320, 28, PropertyColor.GREEN),
            (35, "Short Line", 200, 25, PropertyColor.RAILROAD),
            (37, "Park Place", 350, 35, PropertyColor.DARK_BLUE),
            (39, "Boardwalk", 400, 50, PropertyColor.DARK_BLUE),
        ]
        
        for pos, name, price, rent, color in property_data:
            self.properties[pos] = Property(
                name=name,
                position=pos,
                price=price,
                rent=rent,
                color=color
            )
        
        # Special spaces
        self.special_spaces = {
            0: "GO",
            4: "Income Tax",
            7: "Chance",
            10: "Jail",
            17: "Community Chest",
            20: "Free Parking",
            22: "Chance",
            30: "Go To Jail",
            33: "Community Chest",
            36: "Chance",
            38: "Luxury Tax"
        }
        
        # Utilities
        self.properties[12] = Property(
            name="Electric Company",
            position=12,
            price=150,
            rent=4,
            color=PropertyColor.UTILITY
        )
        self.properties[28] = Property(
            name="Water Works",
            position=28,
            price=150,
            rent=4,
            color=PropertyColor.UTILITY
        )
    
    def _setup_cards(self):
        """Set up Chance and Community Chest cards."""
        chance_effects = [
            ("Advance to Go (Collect $200)", "move", 0, 0, "self"),
            ("Bank pays you dividend of $50", "money", 50, 0, "self"),
            ("Go back 3 spaces", "move_back", 3, 0, "self"),
            ("Go to Jail - Do not pass GO", "jail", 0, 0, "self"),
            ("You have won a crossword competition. Collect $100", "money", 100, 0, "self"),
            ("Speeding fine $15", "money", -15, 0, "self"),
            ("Take a trip to Reading Railroad", "move_to", 0, 5, "self"),
            ("Your building loan matures. Collect $150", "money", 150, 0, "self"),
            ("Pay each player $50", "pay_each", 50, 0, "all"),
            ("Advance to Illinois Avenue", "move_to", 0, 24, "self"),
            ("Advance to St. Charles Place", "move_to", 0, 11, "self"),
            ("Take a walk on the Boardwalk", "move_to", 0, 39, "self"),
            ("You are assessed for street repairs. Pay $40 per house, $115 per hotel", "repairs", 0, 0, "self"),
            ("Get out of Jail Free", "get_out_jail", 0, 0, "self"),
        ]
        
        community_effects = [
            ("Advance to Go (Collect $200)", "move", 0, 0, "self"),
            ("Bank error in your favor. Collect $200", "money", 200, 0, "self"),
            ("Doctor's fee. Pay $50", "money", -50, 0, "self"),
            ("From sale of stock you get $50", "money", 50, 0, "self"),
            ("Go to Jail - Do not pass GO", "jail", 0, 0, "self"),
            ("Grand Opera Night. Collect $50 from every player", "collect_all", 50, 0, "all"),
            ("Holiday Fund matures. Receive $100", "money", 100, 0, "self"),
            ("Income tax refund. Collect $20", "money", 20, 0, "self"),
            ("Life insurance matures. Collect $100", "money", 100, 0, "self"),
            ("Pay hospital fees of $100", "money", -100, 0, "self"),
            ("Receive $25 consultancy fee", "money", 25, 0, "self"),
            ("Second prize in beauty contest. Collect $10", "money", 10, 0, "self"),
            ("Get out of Jail Free", "get_out_jail", 0, 0, "self"),
            ("It is your birthday. Collect $10 from every player", "collect_all", 10, 0, "all"),
        ]
        
        for text, effect, value, position, target in chance_effects:
            self.chance_cards.append(Card(text=text, effect=effect, value=value, position=position, target=target))
        
        for text, effect, value, position, target in community_effects:
            self.community_chest_cards.append(Card(text=text, effect=effect, value=value, position=position, target=target))
        
        # Shuffle cards
        random.shuffle(self.chance_cards)
        random.shuffle(self.community_chest_cards)
    
    def draw_chance(self) -> Optional[Card]:
        """Draw a Chance card."""
        if not self.chance_cards:
            self._setup_cards()
            random.shuffle(self.chance_cards)
        return self.chance_cards.pop() if self.chance_cards else None
    
    def draw_community_chest(self) -> Optional[Card]:
        """Draw a Community Chest card."""
        if not self.community_chest_cards:
            self._setup_cards()
            random.shuffle(self.community_chest_cards)
        return self.community_chest_cards.pop() if self.community_chest_cards else None
    
    def get_space_name(self, position: int) -> str:
        """Get the name of a space."""
        if position in self.special_spaces:
            return self.special_spaces[position]
        elif position in self.properties:
            return self.properties[position].name
        else:
            return f"Space {position}"
    
    def get_space_type(self, position: int) -> str:
        """Get the type of a space."""
        if position == 0:
            return "GO"
        elif position in self.properties:
            prop = self.properties[position]
            if prop.color == PropertyColor.UTILITY:
                return "Utility"
            elif prop.color == PropertyColor.RAILROAD:
                return "Railroad"
            else:
                return "Property"
        elif position in self.special_spaces:
            return self.special_spaces[position]
        else:
            return "Empty"


class MonopolyGame:
    """Manages a complete Monopoly game session."""
    
    def __init__(self, channel_id: int, max_players: int = 4, npcs_enabled: bool = True):
        self.channel_id = channel_id
        self.max_players = max_players
        self.board = MonopolyBoard()
        self.players: Dict[int, Player] = {}
        self.npcs: Dict[int, NPC] = {}
        self.npcs_enabled = npcs_enabled
        self.all_player_ids: List[int] = []  # Combined human + NPC IDs for turn order
        self.current_player_index: int = 0
        self.game_started: bool = False
        self.game_over: bool = False
        self.winner: Optional[int] = None
        self.dice_rolls: List[Tuple[int, int]] = []
        self.turn_count: int = 0
        self.get_out_jail_cards: Dict[int, int] = {}  # user_id -> count of cards
        self.active_auction: Optional[Auction] = None  # Current active auction
        self.auction_bids: Dict[int, int] = {}  # player_id -> bid amount for current auction
    
    def add_player(self, user_id: int, username: str) -> bool:
        """Add a human player to the game."""
        total_players = len(self.players) + len(self.npcs)
        if total_players >= self.max_players:
            return False
        if user_id in self.players:
            return False
        
        self.players[user_id] = Player(user_id=user_id, username=username)
        self._update_player_order()
        return True
    
    def add_npc(self, username: str, personality: str = "balanced") -> bool:
        """Add an NPC player to the game."""
        total_players = len(self.players) + len(self.npcs)
        if total_players >= self.max_players:
            return False
        
        # Generate unique NPC ID (negative to avoid conflicts with real user IDs)
        npc_id = -len(self.npcs) - 1
        self.npcs[npc_id] = NPC(
            user_id=npc_id,
            username=username,
            personality=personality
        )
        self._update_player_order()
        return True
    
    def _update_player_order(self):
        """Update the combined list of all player IDs for turn order."""
        self.all_player_ids = list(self.players.keys()) + list(self.npcs.keys())
    
    def remove_player(self, user_id: int) -> bool:
        """Remove a human player from the game."""
        if user_id not in self.players:
            return False
        
        del self.players[user_id]
        self._update_player_order()
        return True
    
    def start_game(self) -> bool:
        """Start the game. Auto-fills with NPCs if needed."""
        total_players = len(self.players) + len(self.npcs)
        
        if total_players < 2:
            # Auto-add NPCs if enabled and not enough players
            if self.npcs_enabled:
                while total_players < 3 and total_players < self.max_players:
                    personalities = ["aggressive", "conservative", "balanced"]
                    npc_name = f"NPC {len(self.npcs) + 1}"
                    personality = personalities[len(self.npcs) % len(personalities)]
                    self.add_npc(npc_name, personality)
                    total_players += 1
        
        if total_players < 2:
            return False
        
        self.game_started = True
        self._update_player_order()
        return True
    
    def get_current_player(self) -> Optional[Player]:
        """Get the current human player."""
        if not self.all_player_ids:
            return None
        
        current_id = self.all_player_ids[self.current_player_index % len(self.all_player_ids)]
        return self.players.get(current_id)
    
    def get_current_npc(self) -> Optional[NPC]:
        """Get the current NPC if it's an NPC's turn."""
        if not self.all_player_ids:
            return None
        
        current_id = self.all_player_ids[self.current_player_index % len(self.all_player_ids)]
        return self.npcs.get(current_id)
    
    def is_current_player_human(self) -> bool:
        """Check if current player is human."""
        current = self.get_current_player()
        return current is not None
    
    def get_current_entity(self):
        """Get current player entity (human or NPC)."""
        if not self.all_player_ids:
            return None
        
        current_id = self.all_player_ids[self.current_player_index % len(self.all_player_ids)]
        if current_id in self.players:
            return self.players[current_id]
        elif current_id in self.npcs:
            return self.npcs[current_id]
        return None
    
    def next_turn(self):
        """Move to the next player's turn."""
        if not self.all_player_ids:
            return
        
        self.current_player_index = (self.current_player_index + 1) % len(self.all_player_ids)
        self.turn_count += 1
    
    def roll_dice(self) -> Tuple[int, int]:
        """Roll two dice."""
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        self.dice_rolls.append((die1, die2))
        return die1, die2
    
    def buy_property(self, player: Player, property_pos: int) -> Tuple[bool, str]:
        """Attempt to buy a property. Triggers auction if declined."""
        if property_pos not in self.board.properties:
            return False, "Not a buyable property!"
        
        prop = self.board.properties[property_pos]
        
        if prop.owner is not None:
            return False, "Property already owned!"
        
        if player.money < prop.price:
            return False, "Not enough money!"
        
        player.pay(prop.price)
        prop.buy(player.user_id)
        player.properties.append(property_pos)
        
        return True, f"Bought {prop.name} for ${prop.price}!"
    
    def start_auction(self, property_pos: int) -> Tuple[bool, str]:
        """Start an auction for a property."""
        if property_pos not in self.board.properties:
            return False, "Invalid property!"
        
        prop = self.board.properties[property_pos]
        
        if prop.owner is not None:
            return False, "Property already owned!"
        
        if self.active_auction is not None:
            return False, "Another auction is already in progress!"
        
        # Get all non-bankrupt players (humans and NPCs)
        eligible_bidders = [pid for pid, p in self.players.items() if not p.bankrupt and p.money >= 10]
        eligible_bidders += [nid for nid, n in self.npcs.items() if not n.bankrupt and n.money >= 10]
        
        if len(eligible_bidders) < 2:
            return False, "Not enough eligible bidders!"
        
        starting_bid = max(10, prop.price // 4)
        
        self.active_auction = Auction(
            property_pos=property_pos,
            starting_bid=starting_bid,
            current_bid=starting_bid - 10,  # So first bid becomes starting_bid
            highest_bidder=None,
            bidders={},
            active=True,
            turn_index=0,
            pass_count=0,
            min_bid_increment=10
        )
        
        return True, f"Auction started for {prop.name}! Starting bid: ${starting_bid}"
    
    def place_bid(self, player_id: int, amount: int) -> Tuple[bool, str]:
        """Place a bid in the current auction."""
        if self.active_auction is None or not self.active_auction.active:
            return False, "No active auction!"
        
        auction = self.active_auction
        prop = self.board.properties[auction.property_pos]
        
        # Check if player is eligible
        entity = self.players.get(player_id) or self.npcs.get(player_id)
        if not entity or entity.bankrupt:
            return False, "You're not eligible to bid!"
        
        if player_id not in self.all_player_ids:
            return False, "You're not in this game!"
        
        # Validate bid amount
        min_bid = auction.current_bid + auction.min_bid_increment
        if amount < min_bid:
            return False, f"Minimum bid is ${min_bid}!"
        
        if amount > entity.money:
            return False, "You don't have enough money!"
        
        # Place the bid
        auction.current_bid = amount
        auction.highest_bidder = player_id
        auction.pass_count = 0
        
        return True, f"Bid of ${amount} placed by {entity.username}!"
    
    def pass_bid(self, player_id: int) -> Tuple[bool, str]:
        """Pass on bidding in the current auction."""
        if self.active_auction is None or not self.active_auction.active:
            return False, "No active auction!"
        
        auction = self.active_auction
        entity = self.players.get(player_id) or self.npcs.get(player_id)
        
        if not entity:
            return False, "Player not found!"
        
        auction.pass_count += 1
        
        # If all but one player have passed
        total_bidders = len([p for p in self.players.values() if not p.bankrupt]) + \
                       len([n for n in self.npcs.values() if not n.bankrupt])
        
        if auction.pass_count >= total_bidders - 1 and auction.highest_bidder is not None:
            # End auction
            return self.end_auction()
        
        return True, f"{entity.username} passed."
    
    def end_auction(self) -> Tuple[bool, str]:
        """End the current auction and transfer property."""
        if self.active_auction is None:
            return False, "No active auction!"
        
        auction = self.active_auction
        
        if auction.highest_bidder is None:
            # No bids, property goes back to bank
            self.active_auction = None
            return True, "Auction ended with no bids. Property remains unsold."
        
        winner = self.players.get(auction.highest_bidder) or self.npcs.get(auction.highest_bidder)
        prop = self.board.properties[auction.property_pos]
        
        if winner:
            winner.pay(auction.current_bid)
            prop.buy(auction.highest_bidder)
            winner.properties.append(auction.property_pos)
            
            self.active_auction = None
            return True, f"🏆 Auction won by {winner.username} for ${auction.current_bid}! They bought {prop.name}."
        
        self.active_auction = None
        return False, "Auction winner not found!"
    
    def get_auction_status(self) -> Optional[dict]:
        """Get current auction status."""
        if self.active_auction is None:
            return None
        
        auction = self.active_auction
        prop = self.board.properties[auction.property_pos]
        
        highest_bidder_name = None
        if auction.highest_bidder:
            entity = self.players.get(auction.highest_bidder) or self.npcs.get(auction.highest_bidder)
            if entity:
                highest_bidder_name = entity.username
        
        return {
            "property": prop.name,
            "current_bid": auction.current_bid,
            "highest_bidder": highest_bidder_name,
            "min_next_bid": auction.current_bid + auction.min_bid_increment,
            "pass_count": auction.pass_count
        }
    
    def sell_property(self, player: Player, property_pos: int) -> Tuple[bool, str]:
        """Sell a property back to the bank."""
        if property_pos not in self.board.properties:
            return False, "Invalid property!"
        
        prop = self.board.properties[property_pos]
        
        if prop.owner != player.user_id:
            return False, "You don't own this property!"
        
        # Sell for half price
        sell_price = prop.price // 2
        player.receive(sell_price)
        player.properties.remove(property_pos)
        prop.sell()
        
        return True, f"Sold {prop.name} for ${sell_price}!"
    
    def buy_property_npc(self, npc: NPC, property_pos: int) -> Tuple[bool, str]:
        """Attempt to buy a property for an NPC."""
        if property_pos not in self.board.properties:
            return False, "Not a buyable property!"
        
        prop = self.board.properties[property_pos]
        
        if prop.owner is not None:
            return False, "Property already owned!"
        
        if not npc.should_buy_property(prop, {}):
            return False, "NPC chose not to buy"
        
        npc.pay(prop.price)
        prop.buy(npc.user_id)
        npc.properties.append(property_pos)
        
        return True, f"{npc.username} bought {prop.name} for ${prop.price}!"
    
    def pay_rent(self, player: Player, property_pos: int) -> Tuple[bool, str]:
        """Pay rent to property owner (human player)."""
        if property_pos not in self.board.properties:
            return False, "Not a rentable property!"
        
        prop = self.board.properties[property_pos]
        
        if prop.owner is None or prop.owner == player.user_id:
            return False, "No rent to pay!"
        
        rent = prop.get_rent()
        
        if player.money < rent:
            # Player goes bankrupt
            player.pay(player.money)
            # Transfer properties to owner if human, otherwise back to bank
            owner = self.players.get(prop.owner) or self.npcs.get(prop.owner)
            if owner:
                owner.receive(player.money)
            return True, f"Bankrupt! Paid ${player.money} to owner."
        
        owner = self.players.get(prop.owner) or self.npcs.get(prop.owner)
        if owner:
            player.pay(rent)
            owner.receive(rent)
            return True, f"Paid ${rent} rent to {owner.username}!"
        
        return False, "Owner not in game!"
    
    def pay_rent_npc(self, npc: NPC, property_pos: int) -> Tuple[bool, str]:
        """Pay rent for an NPC."""
        if property_pos not in self.board.properties:
            return False, "Not a rentable property!"
        
        prop = self.board.properties[property_pos]
        
        if prop.owner is None or prop.owner == npc.user_id:
            return False, "No rent to pay!"
        
        rent = prop.get_rent()
        
        if npc.money < rent:
            npc.pay(npc.money)
            owner = self.players.get(prop.owner) or self.npcs.get(prop.owner)
            if owner:
                owner.receive(npc.money)
            return True, f"{npc.username} went bankrupt! Paid ${npc.money}."
        
        owner = self.players.get(prop.owner) or self.npcs.get(prop.owner)
        if owner:
            npc.pay(rent)
            owner.receive(rent)
            return True, f"{npc.username} paid ${rent} rent to {owner.username}!"
        
        return False, "Owner not in game!"
    
    def process_card_effect(self, player, card: Card) -> Tuple[str, List[str]]:
        """Process a Chance/Community Chest card effect. Returns (result_text, log_messages)."""
        messages = []
        result = f"Drew card: {card.text}"
        
        if card.effect == "money":
            if card.value > 0:
                player.receive(card.value)
                messages.append(f"💰 Received ${card.value}!")
            else:
                player.pay(abs(card.value))
                messages.append(f"💸 Paid ${abs(card.value)}!")
        
        elif card.effect == "move":
            old_pos = player.position
            player.move(card.value if card.value > 0 else 0)
            if player.position == 0 and old_pos != 0:
                messages.append("🎉 Advanced to GO! Collected $200")
        
        elif card.effect == "move_back":
            player.position = (player.position - card.value) % 40
        
        elif card.effect == "move_to":
            player.position = card.position
            if card.position == 0:
                player.receive(200)
                messages.append("🎉 Advanced to GO! Collected $200")
        
        elif card.effect == "jail":
            player.in_jail = True
            player.jail_turns = 0
            player.position = 10
            messages.append("⛓️ Go to Jail! Do not pass GO!")
        
        elif card.effect == "collect_all":
            for pid, p in self.players.items():
                if pid != player.user_id and not p.bankrupt:
                    amount = min(p.money, card.value)
                    p.pay(amount)
                    player.receive(amount)
            for nid, n in self.npcs.items():
                if nid != player.user_id and not n.bankrupt:
                    amount = min(n.money, card.value)
                    n.pay(amount)
                    player.receive(amount)
            messages.append(f"💰 Collected ${card.value} from each player!")
        
        elif card.effect == "pay_each":
            total_paid = 0
            for pid, p in self.players.items():
                if pid != player.user_id and not p.bankrupt:
                    player.pay(card.value)
                    p.receive(card.value)
                    total_paid += card.value
            for nid, n in self.npcs.items():
                if nid != player.user_id and not n.bankrupt:
                    player.pay(card.value)
                    n.receive(card.value)
                    total_paid += card.value
            messages.append(f"💸 Paid ${total_paid} total to all players!")
        
        elif card.effect == "get_out_jail":
            self.get_out_jail_cards[player.user_id] = self.get_out_jail_cards.get(player.user_id, 0) + 1
            messages.append("📜 Received 'Get Out of Jail Free' card!")
        
        elif card.effect == "repairs":
            # Calculate repairs based on houses/hotels (simplified)
            total_props = len(player.properties) if hasattr(player, 'properties') else len(player.properties)
            repair_cost = total_props * 25  # Simplified calculation
            player.pay(repair_cost)
            messages.append(f"🔨 Paid ${repair_cost} for property repairs!")
        
        return result, messages
    
    def get_game_state_embed(self) -> dict:
        """Get current game state as embed data including NPCs."""
        current_human = self.get_current_player()
        current_npc = self.get_current_npc()
        
        players_info = []
        
        # Add human players
        for p in self.players.values():
            status = ""
            if p == current_human:
                status = "🎲 Current Turn"
            if p.bankrupt:
                status = "💀 Bankrupt"
            players_info.append({
                "name": p.username,
                "money": p.money,
                "position": p.position,
                "properties": len(p.properties),
                "status": status,
                "type": "human"
            })
        
        # Add NPCs
        for n in self.npcs.values():
            status = ""
            if n == current_npc:
                status = "🤖 Current Turn"
            if n.bankrupt:
                status = "💀 Bankrupt"
            players_info.append({
                "name": f"🤖 {n.username}",
                "money": n.money,
                "position": n.position,
                "properties": len(n.properties),
                "status": status,
                "type": "npc",
                "personality": n.personality
            })
        
        return {
            "players": players_info,
            "turn": self.turn_count,
            "current_player": current.username if current else None,
            "game_over": self.game_over,
            "winner": self.winner
        }
