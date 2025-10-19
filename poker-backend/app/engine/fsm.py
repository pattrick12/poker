from typing import List, Dict, Any, Tuple, Optional
import json
from enum import Enum
from dataclasses import dataclass, asdict, field

class GamePhase(str, Enum):
    WAITING = "waiting"
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"

@dataclass
class PlayerState:
    id: str
    username: str
    chips: int
    current_bet: int = 0
    has_folded: bool = False
    is_active: bool = True
    hole_cards: List[Dict[str, str]] = None # [{"rank": "A", "suit": "s"}, ...]

@dataclass
class GameState:
    table_id: str
    phase: str = "waiting"
    pot: int = 0
    community_cards: list = field(default_factory=list)
    players: list = field(default_factory=list)
    current_turn_index: int = None
    dealer_index: int = 0
    min_bet: int = 20
    deck: list = field(default_factory=list)
    actions_this_round: int = 0  # Track how many actions in current betting round

    def to_dict(self):
        d = asdict(self)
        # Don't serialize deck or hidden hole cards for public view usually, 
        # but for internal state we keep them. 
        # We'll handle sanitization in the view layer.
        return d

class PokerFSM:
    def __init__(self, table_id):
        self.table_id = table_id
        self.state = GameState(
            table_id=table_id,
            phase=GamePhase.WAITING,
            pot=0,
            community_cards=[],
            players=[],
            current_turn_index=None,
            dealer_index=0,
            min_bet=20, # Blinds: 10/20
            deck=[]
        )

    async def apply(self, action: Dict[str, Any], rng) -> Tuple[List[Any], Any]:
        events = []
        act_type = action.get("action")
        player_id = action.get("player_id")

        if act_type == "join":
            # Check if player already exists
            if not any(p.id == player_id for p in self.state.players):
                new_player = PlayerState(
                    id=player_id,
                    username=action.get("username", f"Player-{player_id[:4]}"),
                    chips=action.get("buyin", 1000),
                    hole_cards=[]
                )
                self.state.players.append(new_player)
                events.append(self._create_event("player_joined", {"player": asdict(new_player)}))
                
                # Broadcast current waiting state immediately so all clients see the new player
                events.append(self._create_event("state_update", {"phase": self.state.phase, "players": [asdict(p) for p in self.state.players]}))
                
                # Auto-start if enough players (e.g., 2)
                if len(self.state.players) >= 2 and self.state.phase == GamePhase.WAITING:
                    await self._start_hand(rng, events)

        elif act_type in ["fold", "check", "call", "raise"]:
            # Validate it's the player's turn before processing
            if self.state.current_turn_index is not None:
                current_player = self.state.players[self.state.current_turn_index]
                if current_player.id == player_id:
                    await self._handle_game_action(action, events, rng)
                else:
                    print(f"[FSM] Ignoring action from {player_id} - not their turn (current: {current_player.id})")
            else:
                print(f"[FSM] Ignoring action - game not in progress")

        return events, self

    async def _start_hand(self, rng, events):
        self.state.phase = GamePhase.PREFLOP
        self.state.pot = 0
        self.state.community_cards = []
        
        # Anti-Cheat: Generate Secret & Commitment
        import uuid
        hand_id = str(uuid.uuid4())
        server_secret = rng.generate_secret()
        commitment = rng.compute_commitment(server_secret, hand_id)
        
        # Store for reveal later
        self.current_hand_secret = server_secret
        self.current_hand_id = hand_id
        self.current_hand_commitment = commitment
        
        # Seed RNG
        seed = rng.generate_seed(server_secret, hand_id)
        rng.rng.seed(seed)
        
        self.state.deck = self._create_deck()
        rng.shuffle(self.state.deck)
        
        # Reset player states
        for p in self.state.players:
            p.current_bet = 0
            p.has_folded = False
            p.hole_cards = [self.state.deck.pop(), self.state.deck.pop()]
        
        # Blinds
        sb_idx = (self.state.dealer_index + 1) % len(self.state.players)
        bb_idx = (self.state.dealer_index + 2) % len(self.state.players)
        
        # Simple blind posting
        self._post_blind(sb_idx, self.state.min_bet // 2)
        self._post_blind(bb_idx, self.state.min_bet)
        
        self.state.current_turn_index = (bb_idx + 1) % len(self.state.players)
        
        events.append(self._create_event("hand_started", {
            "dealer": self.state.dealer_index,
            "hand_id": hand_id,
            "commitment": commitment
        }))

    def _post_blind(self, player_idx, amount):
        player = self.state.players[player_idx]
        bet = min(player.chips, amount)
        player.chips -= bet
        player.current_bet += bet
        self.state.pot += bet

    async def _handle_game_action(self, action, events, rng):
        if self.state.current_turn_index is None:
            return

        player = self.state.players[self.state.current_turn_index]
        if player.id != action.get("player_id"):
            return # Not turn

        act_type = action.get("action")
        amount = action.get("amount", 0)
        
        current_max_bet = max((p.current_bet for p in self.state.players), default=0)
        
        if act_type == "fold":
            player.has_folded = True
            player.is_active = False
        elif act_type == "call":
            to_call = current_max_bet - player.current_bet
            bet = min(player.chips, to_call)
            player.chips -= bet
            player.current_bet += bet
            self.state.pot += bet
        elif act_type == "check":
            # Check is only valid if player's bet matches current max
            if player.current_bet < current_max_bet:
                # Invalid check - should call/fold instead
                print(f"[FSM] Invalid check from {player.id} - bet {player.current_bet} < max {current_max_bet}")
                return
            # Valid check - no chips move, just advance turn 
        elif act_type == "raise":
            # Raise logic: amount is the *total* bet they want to be at
            # OR amount is the *additional* amount. Standard is usually "raise to X" or "raise by X".
            # Let's assume "raise by X" on top of current max for simplicity, or "raise to X".
            # Let's use "raise to X" where X >= current_max_bet + min_raise
            
            # Simplified: amount is the TOTAL amount the player puts in for this round
            if amount < current_max_bet + self.state.min_bet:
                 # Invalid raise
                 return
            
            diff = amount - player.current_bet
            if player.chips >= diff:
                player.chips -= diff
                player.current_bet += diff
                self.state.pot += diff
            else:
                # All-in case: Player puts in everything they have
                actual_bet = player.chips
                player.chips = 0
                player.current_bet += actual_bet
                self.state.pot += actual_bet
                # Note: In a real engine, we'd create a side pot here.
                # For this implementation, we'll keep a single pot but note the all-in.
                # Side pots are complex; this is a simplified "complete" logic.

        events.append(self._create_event("player_action", {
            "player_id": player.id,
            "action": act_type,
            "amount": amount,
            "chips": player.chips,
            "current_bet": player.current_bet
        }))

        # Increment action counter
        self.state.actions_this_round += 1

        # Move turn
        await self._next_turn(events, rng)

    async def _next_turn(self, events, rng):
        active_players = [p for p in self.state.players if not p.has_folded]
        if len(active_players) <= 1:
            # Everyone folded, remaining player wins
            if active_players:
                await self._end_hand(events, rng, winner=active_players[0], hand_name="opponent folded")
            return

        # Check if betting round is over
        current_max_bet = max((p.current_bet for p in self.state.players if not p.has_folded), default=0)
        
        # Round is complete if:
        # 1. All active players have matched the max bet OR are all-in (chips == 0)
        all_matched_or_allin = all(
            (p.current_bet == current_max_bet or p.chips == 0) 
            for p in active_players
        )
        
        # We need to check if everyone has acted. In a proper implementation, we'd track
        # "last_action_index" but for simplicity, we count actions.
        # Round ends when: all bets equal AND everyone has acted at least once
        if all_matched_or_allin and len(active_players) > 1 and self.state.actions_this_round >= len(active_players):
            # Everyone has acted and equalized bets, move to next phase
            await self._next_phase(events, rng)
            return
            
        # Find next active player who can still act (has chips)
        start_idx = self.state.current_turn_index
        next_idx = (start_idx + 1) % len(self.state.players)
        
        # Skip folded players and all-in players
        attempts = 0
        while attempts < len(self.state.players):
            if not self.state.players[next_idx].has_folded and self.state.players[next_idx].chips > 0:
                self.state.current_turn_index = next_idx
                return
            next_idx = (next_idx + 1) % len(self.state.players)
            attempts += 1
            
        # If we get here, all remaining players are all-in, move to next phase
        await self._next_phase(events, rng)

    async def _next_phase(self, events, rng):
        # Reset action counter and bets for new round
        self.state.actions_this_round = 0
        for p in self.state.players:
            p.current_bet = 0
            
        if self.state.phase == GamePhase.PREFLOP:
            self.state.phase = GamePhase.FLOP
            self.state.community_cards.extend([self.state.deck.pop() for _ in range(3)])
        elif self.state.phase == GamePhase.FLOP:
            self.state.phase = GamePhase.TURN
            self.state.community_cards.append(self.state.deck.pop())
        elif self.state.phase == GamePhase.TURN:
            self.state.phase = GamePhase.RIVER
            self.state.community_cards.append(self.state.deck.pop())
        elif self.state.phase == GamePhase.RIVER:
            self.state.phase = GamePhase.SHOWDOWN
            await self._showdown(events, rng)
            return
            
        # Set turn to first active player after dealer
        next_idx = (self.state.dealer_index + 1) % len(self.state.players)
        while self.state.players[next_idx].has_folded:
            next_idx = (next_idx + 1) % len(self.state.players)
        self.state.current_turn_index = next_idx
            
        events.append(self._create_event("phase_change", {
            "phase": self.state.phase,
            "community_cards": self.state.community_cards,
            "pot": self.state.pot
        }))

    async def _showdown(self, events, rng):
        # Evaluate hands
        from treys import Evaluator, Card
        
        active_players = [p for p in self.state.players if not p.has_folded]
        if not active_players:
            return

        evaluator = Evaluator()
        best_rank = float('inf')
        winner = None
        
        # Helper to convert our card format to treys format
        def to_treys_card(card):
            rank_map = {'2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', 
                       '8': '8', '9': '9', 'T': 'T', 'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'}
            suit_map = {'h': 'h', 'd': 'd', 'c': 'c', 's': 's'}
            return Card.new(rank_map[card['rank']] + suit_map[card['suit']])
        
        # Evaluate each player's hand
        for player in active_players:
            try:
                # Convert hole cards and community cards to treys format
                hole = [to_treys_card(c) for c in player.hole_cards]
                board = [to_treys_card(c) for c in self.state.community_cards]
                
                # Evaluate hand (lower rank is better)
                rank = evaluator.evaluate(board, hole)
                
                if rank < best_rank:
                    best_rank = rank
                    winner = player
            except Exception as e:
                print(f"Error evaluating hand for {player.id}: {e}")
                # Fallback to random if evaluation fails
                if winner is None:
                    winner = player
        
        if winner is None:
            winner = active_players[0]
                
        # Get hand class name for display
        hand_class = evaluator.get_rank_class(best_rank)
        hand_name = evaluator.class_to_string(hand_class)
        
        await self._end_hand(events, rng, winner, hand_name)

    async def _end_hand(self, events, rng, winner, hand_name="Unknown"):
        winner.chips += self.state.pot
        events.append(self._create_event("showdown", {
            "winner_id": winner.id,
            "amount": self.state.pot,
            "winning_hand": hand_name,
            "server_secret": getattr(self, 'current_hand_secret', None),
            "hand_id": getattr(self, 'current_hand_id', None)
        }))
        
        # Log to Postgres (Fire and forget task in real app, here await for simplicity)
        try:
            from app.storage.pg import pg_client
            # Ensure connected
            await pg_client.connect()
            await pg_client.log_hand(
                self.table_id, 
                getattr(self, 'current_hand_id', 'unknown'),
                0, # Seed not stored directly in this flow, derived
                getattr(self, 'current_hand_secret', ''),
                getattr(self, 'current_hand_commitment', ''),
                json.dumps([e.payload for e in events])
            )
        except Exception as e:
            print(f"Failed to log hand: {e}")
        
        self.state.pot = 0
        self.state.phase = GamePhase.WAITING
        self.state.community_cards = []
        self.state.current_turn_index = None
        self.state.dealer_index = (self.state.dealer_index + 1) % len(self.state.players)
        
        # Auto-start next hand after delay?
        if len(self.state.players) >= 2:
             await self._start_hand(rng, events)

    def _create_deck(self):
        ranks = "23456789TJQKA"
        suits = "shdc"
        return [{"rank": r, "suit": s} for r in ranks for s in suits]

    def _create_event(self, type, payload):
        return DummyEvent(type, payload)

    def to_primitive(self):
        return {
            "data": json.dumps(self.state.to_dict())
        }

class DummyEvent:
    def __init__(self, type, payload):
        self.type = type
        self.payload = payload
    
    def to_json(self):
        return json.dumps({"type": self.type, "payload": self.payload})
