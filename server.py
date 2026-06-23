import asyncio
import json
import os
import random
import socket
import string
from pathlib import Path

import chess
import chess.variant
from aiohttp import WSMsgType, web


ROOT = Path(__file__).parent
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
MAX_ROOMS = 1000
MAX_CONNECTIONS_PER_IP = 6
MAX_MSG_SIZE = 16_384
MSG_RATE_LIMIT = 10
MSG_RATE_WINDOW = 1.0

_ip_connections: dict[str, int] = {}

VARIANTS = {
    "classic": {
        "label": "Classic",
        "description": "Regular chess, clean and familiar.",
        "board": chess.Board,
    },
    "three_check": {
        "label": "Three-Check",
        "description": "Win by checking the enemy king three times.",
        "board": chess.variant.ThreeCheckBoard,
    },
    "king_hill": {
        "label": "King of the Hill",
        "description": "Win by marching your king into the center.",
        "board": chess.variant.KingOfTheHillBoard,
    },
    "atomic": {
        "label": "Atomic",
        "description": "Captures explode nearby pieces.",
        "board": chess.variant.AtomicBoard,
    },
    "dice": {
        "label": "Dice Chess",
        "description": "A die chooses which piece type must move.",
        "board": chess.Board,
    },
    "fog": {
        "label": "Fog of War",
        "description": "You only see what your army can reach.",
        "board": chess.Board,
    },
    "thress": {
        "label": "Thress",
        "description": "Every third move, pick one of three silly rule cards.",
        "board": chess.Board,
    },
}

PIECE_NAMES = {
    chess.PAWN: "Pawn",
    chess.KNIGHT: "Knight",
    chess.BISHOP: "Bishop",
    chess.ROOK: "Rook",
    chess.QUEEN: "Queen",
    chess.KING: "King",
}

PROMOTION_MAP = {
    "q": chess.QUEEN,
    "r": chess.ROOK,
    "b": chess.BISHOP,
    "n": chess.KNIGHT,
}

BOT_DIFFICULTIES = {
    "easy": {
        "label": "Easy Explorer",
        "description": "Mostly random legal moves while it learns what the pieces do.",
        "skill": 0.15,
        "chaos": 0.85,
        "aggression": 0.25,
        "greed": 0.35,
    },
    "medium": {
        "label": "Balanced Club Bot",
        "description": "A normal casual opponent that likes sensible tactics.",
        "skill": 0.55,
        "chaos": 0.38,
        "aggression": 0.55,
        "greed": 0.65,
    },
    "hard": {
        "label": "Hard Grinder",
        "description": "Low-chaos material play with sharper tactical priorities.",
        "skill": 0.82,
        "chaos": 0.14,
        "aggression": 0.58,
        "greed": 0.82,
    },
    "dougdoug": {
        "label": "DougDoug Chaos",
        "description": "Unofficially inspired by streamer-brain chess: fearless, confused, funny.",
        "skill": 0.2,
        "chaos": 0.96,
        "aggression": 0.78,
        "greed": 0.55,
        "style": "chaos",
    },
    "greedy_goblin": {
        "label": "Greedy Goblin",
        "description": "If it can capture something, it probably will. Consequences are future goblin's problem.",
        "skill": 0.45,
        "chaos": 0.5,
        "aggression": 0.52,
        "greed": 1.0,
        "style": "greedy",
    },
    "coffeehouse": {
        "label": "Coffeehouse Attacker",
        "description": "Checks, threats, sacrifices, vibes. Hates quiet positions.",
        "skill": 0.58,
        "chaos": 0.48,
        "aggression": 1.0,
        "greed": 0.45,
        "style": "attacker",
    },
    "gotham": {
        "label": "Gotham Tactics",
        "description": "Unofficial GothamChess-flavored bot: tactical, instructive, and allergic to hanging queens.",
        "skill": 0.72,
        "chaos": 0.22,
        "aggression": 0.72,
        "greed": 0.72,
        "style": "coach",
    },
    "magnus": {
        "label": "Magnus-ish Endboss",
        "description": "Unofficial elite-flavored bot: calm, flexible, and annoyingly hard to trick.",
        "skill": 0.96,
        "chaos": 0.04,
        "aggression": 0.48,
        "greed": 0.68,
        "style": "endboss",
    },
}

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

THRESS_MUTATORS = [
    {
        "id": "march_pawns",
        "name": "March of the Pawnguins",
        "description": "Every pawn waddles one square forward if the square is empty.",
    },
    {
        "id": "the_rumbling",
        "name": "The Rumbling",
        "description": "Every pawn storms forward one square, deleting anything in front of it.",
    },
    {
        "id": "they_deserved_it",
        "name": "They Deserved It",
        "description": "One random non-king piece disappears.",
    },
    {
        "id": "going_woke",
        "name": "Going Woke",
        "description": "Pieces on files E-H slide one square toward the queenside if open.",
    },
    {
        "id": "horse_girl_summoning",
        "name": "Horse Girl Summoning",
        "description": "Your side gets a knight on a random empty square.",
    },
    {
        "id": "rook_market_crash",
        "name": "Rook Market Crash",
        "description": "All rooks turn into bishops. Diversification failed.",
    },
    {
        "id": "pawn_union",
        "name": "Pawn Union",
        "description": "Your pawns become queenside-to-kingside commuters and shift right if open.",
    },
    {
        "id": "minor_inconvenience",
        "name": "Minor Inconvenience",
        "description": "A random bishop or knight from either side becomes a pawn.",
    },
]


class ChessVariantGame:
    def __init__(self, variant_id="classic"):
        self.variant_id = variant_id
        self.variant = VARIANTS[variant_id]
        self.board = self.variant["board"]()
        self.game_state = "waiting"
        self.message = "Choose a variant, wait for both players, then start."
        self.last_move = None
        self.dice_piece = None
        self.move_count = 0
        self.move_history = []
        self.pending_mutator = None
        self.active_mutators = []
        self.mutator_history = []

    def reset_board(self):
        self.board = self.variant["board"]()
        self.last_move = None
        self.dice_piece = None
        self.move_count = 0
        self.move_history = []
        self.pending_mutator = None
        self.active_mutators = []
        self.mutator_history = []
        if self.variant_id == "dice":
            self.roll_dice()

    def set_waiting(self, message="Waiting for another player to join this room."):
        self.reset_board()
        self.game_state = "waiting"
        self.message = message

    def set_ready(self):
        self.reset_board()
        self.game_state = "ready"
        self.message = f"{self.variant['label']} selected. Host can start."

    def start(self):
        self.reset_board()
        self.game_state = "playing"
        self.update_status()

    def restart(self):
        self.start()

    def return_to_ready(self):
        self.set_ready()

    def toggle_pause(self):
        if self.game_state == "playing":
            self.game_state = "paused"
            self.message = "Game paused by the host."
        elif self.game_state == "paused":
            self.game_state = "playing"
            self.update_status()

    def player_color(self, player_index):
        return chess.WHITE if player_index == 0 else chess.BLACK

    def player_index_for_turn(self):
        return 0 if self.board.turn == chess.WHITE else 1

    def color_name(self, color=None):
        active_color = self.board.turn if color is None else color
        return "White" if active_color == chess.WHITE else "Black"

    def roll_dice(self):
        choices = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
        legal_piece_types = {
            self.board.piece_at(move.from_square).piece_type
            for move in self.board.legal_moves
            if self.board.piece_at(move.from_square)
        }

        if not legal_piece_types:
            self.dice_piece = random.choice(choices)
            return

        # Reroll until the active side has at least one legal move with that piece type.
        possible = [piece for piece in choices if piece in legal_piece_types]
        self.dice_piece = random.choice(possible)

    def update_status(self):
        outcome = self.board.outcome(claim_draw=True)
        if outcome:
            self.game_state = "gameover"
            if outcome.winner is None:
                self.message = "Draw."
            else:
                self.message = f"{self.color_name(outcome.winner)} wins."
            return

        if self.variant_id == "dice":
            if self.dice_piece is None:
                self.roll_dice()
            self.message = f"{self.color_name()} to move a {PIECE_NAMES[self.dice_piece]}."
            return

        if self.variant_id == "thress":
            if self.pending_mutator:
                self.message = f"{self.color_name()} must pick a mutator."
            else:
                self.message = f"{self.color_name()} to move. Thress cards appear every third move."
            return

        if self.variant_id == "three_check":
            remaining = getattr(self.board, "remaining_checks", None)
            if remaining:
                used = [3 - remaining[0], 3 - remaining[1]]
                self.message = f"{self.color_name()} to move. Checks: White {used[0]}/3, Black {used[1]}/3."
                return

        if self.board.is_check():
            self.message = f"{self.color_name()} is in check."
        else:
            self.message = f"{self.color_name()} to move."

    def needs_promotion(self, from_square, to_square):
        piece = self.board.piece_at(from_square)
        if not piece or piece.piece_type != chess.PAWN:
            return False

        to_rank = chess.square_rank(to_square)
        return (piece.color == chess.WHITE and to_rank == 7) or (
            piece.color == chess.BLACK and to_rank == 0
        )

    def move(self, player_index, from_name, to_name, promotion=None):
        if self.game_state != "playing":
            return False, "Start the game first."

        if player_index is None or self.player_color(player_index) != self.board.turn:
            return False, "It is not your turn."

        if self.variant_id == "thress" and self.pending_mutator:
            return False, "Pick a Thress mutator first."

        try:
            from_square = chess.parse_square(from_name)
            to_square = chess.parse_square(to_name)
        except ValueError:
            return False, "That square is not valid."

        piece = self.board.piece_at(from_square)
        if piece is None:
            return False, "There is no piece on that square."

        if piece.color != self.player_color(player_index):
            return False, "That is not your piece."

        if self.variant_id == "dice" and piece.piece_type != self.dice_piece:
            return False, f"The die says {PIECE_NAMES[self.dice_piece]}."

        promotion_piece = None
        if self.needs_promotion(from_square, to_square):
            promotion_piece = PROMOTION_MAP.get(str(promotion or "q").lower(), chess.QUEEN)

        move = chess.Move(from_square, to_square, promotion=promotion_piece)
        if move not in self.board.legal_moves:
            return False, "That move is not legal."

        self.push_legal_move(move)
        return True, self.message

    def candidate_moves(self):
        moves = list(self.board.legal_moves)
        if self.variant_id == "dice" and self.dice_piece is not None:
            moves = [
                move
                for move in moves
                if (
                    self.board.piece_at(move.from_square)
                    and self.board.piece_at(move.from_square).piece_type == self.dice_piece
                )
            ]
        return moves

    def push_legal_move(self, move):
        self.board.push(move)
        self.move_count += 1
        self.last_move = {
            "from": chess.square_name(move.from_square),
            "to": chess.square_name(move.to_square),
            "promotion": chess.piece_symbol(move.promotion) if move.promotion else None,
        }
        self.move_history.append(move.uci())

        if self.variant_id == "dice" and not self.board.outcome(claim_draw=True):
            self.roll_dice()

        if self.variant_id == "thress" and not self.board.outcome(claim_draw=True):
            self.maybe_offer_mutators()

        self.update_status()

    def bot_move(self, difficulty):
        if self.game_state != "playing" or self.pending_mutator:
            return False

        move = self.choose_bot_move(difficulty)
        if move is None:
            self.update_status()
            return False

        self.push_legal_move(move)
        return True

    def choose_bot_move(self, difficulty):
        moves = self.candidate_moves()
        if not moves:
            return None

        profile = BOT_DIFFICULTIES.get(difficulty, BOT_DIFFICULTIES["easy"])
        skill = profile.get("skill", 0.4)
        chaos = profile.get("chaos", 0.5)

        if random.random() < chaos * (1 - skill) * 0.72:
            return random.choice(moves)

        scored = [(self.score_bot_move(move, profile), move) for move in moves]
        scored.sort(key=lambda item: item[0], reverse=True)

        if profile.get("style") == "chaos":
            top_count = max(2, min(len(scored), 3 + int(chaos * 12)))
            return random.choice([move for _, move in scored[:top_count]])

        if skill < 0.35:
            top_count = max(1, min(len(scored), 8))
            return random.choice([move for _, move in scored[:top_count]])

        best_score = scored[0][0]
        tolerance = 4 + (1 - skill) * 90 + chaos * 45
        best_moves = [move for score, move in scored if score >= best_score - tolerance]
        return random.choice(best_moves)

    def score_bot_move(self, move, profile):
        bot_color = self.board.turn
        piece = self.board.piece_at(move.from_square)
        score = 0
        greed = profile.get("greed", 0.55)
        aggression = profile.get("aggression", 0.55)
        chaos = profile.get("chaos", 0.4)
        skill = profile.get("skill", 0.5)

        if move.promotion:
            score += PIECE_VALUES.get(move.promotion, 0)

        if self.board.is_capture(move):
            captured = self.board.piece_at(move.to_square)
            attacker = self.board.piece_at(move.from_square)
            if captured:
                score += PIECE_VALUES[captured.piece_type] * (0.9 + greed * 2.0)
            if attacker:
                score -= PIECE_VALUES[attacker.piece_type] * (0.22 - skill * 0.12)

        if piece:
            score += self.personality_piece_bonus(move, piece, profile)

        self.board.push(move)
        try:
            outcome = self.board.outcome(claim_draw=True)
            if outcome:
                if outcome.winner == bot_color:
                    score += 100000
                elif outcome.winner is None:
                    score += 10
                else:
                    score -= 100000
            else:
                score += self.material_score(bot_color) * (0.35 + skill * 0.85)
                if self.board.is_check():
                    score += 35 + aggression * 80
        finally:
            self.board.pop()

        # Small jitter keeps repeated bot games from feeling like one memorized script.
        return score + random.uniform(-10, 10 + chaos * 80)

    def personality_piece_bonus(self, move, piece, profile):
        score = 0
        style = profile.get("style")
        aggression = profile.get("aggression", 0.55)
        chaos = profile.get("chaos", 0.4)

        center = {chess.D4, chess.E4, chess.D5, chess.E5}
        extended_center = center | {chess.C3, chess.D3, chess.E3, chess.F3, chess.C6, chess.D6, chess.E6, chess.F6}

        if move.to_square in center:
            score += 26
        elif move.to_square in extended_center:
            score += 11

        if self.board.gives_check(move):
            score += 45 + aggression * 75

        if self.board.is_castling(move):
            score += 34

        if piece.piece_type in {chess.KNIGHT, chess.BISHOP}:
            home_rank = 0 if piece.color == chess.WHITE else 7
            if chess.square_rank(move.from_square) == home_rank:
                score += 18

        if piece.piece_type == chess.QUEEN and len(self.board.move_stack) < 8:
            score -= 22 if style != "chaos" else 8

        if piece.piece_type == chess.KING and not self.board.is_castling(move):
            score -= 30 if style != "chaos" else 5

        if style == "chaos":
            if piece.piece_type in {chess.KNIGHT, chess.QUEEN, chess.KING}:
                score += 16
            if self.board.is_capture(move) or self.board.gives_check(move):
                score += 55

        if style == "greedy" and self.board.is_capture(move):
            score += 120

        if style == "attacker":
            if self.board.gives_check(move):
                score += 110
            if move.to_square in center:
                score += 20
            if piece.piece_type == chess.PAWN:
                score += 8

        if style == "coach":
            if piece.piece_type == chess.QUEEN and len(self.board.move_stack) < 10:
                score -= 30
            if self.board.is_capture(move) or self.board.gives_check(move):
                score += 35

        if style == "endboss":
            if move.to_square in center:
                score += 22
            if self.board.is_capture(move):
                score += 18
            score -= chaos * 10

        return score

    def material_score(self, color):
        score = 0
        for piece in self.board.piece_map().values():
            value = PIECE_VALUES[piece.piece_type]
            score += value if piece.color == color else -value
        return score

    def maybe_offer_mutators(self):
        if (self.move_count + 1) % 3 != 0:
            self.pending_mutator = None
            return

        options = random.sample(THRESS_MUTATORS, 3)
        self.pending_mutator = {
            "chooser": "white" if self.board.turn == chess.WHITE else "black",
            "options": options,
        }

    def choose_mutator(self, player_index, mutator_id):
        if self.variant_id != "thress":
            return False, "Thress is not selected."

        if self.game_state != "playing":
            return False, "Start the game first."

        if not self.pending_mutator:
            return False, "There is no mutator to choose right now."

        if self.player_color(player_index) != self.board.turn:
            return False, "It is not your mutator choice."

        options = self.pending_mutator["options"]
        mutator = next((option for option in options if option["id"] == mutator_id), None)
        if not mutator:
            return False, "Choose one of the offered mutators."

        applied = self.apply_mutator(mutator["id"])
        self.pending_mutator = None
        self.mutator_history.append(
            {
                "ply": self.move_count + 1,
                "chooser": "white" if self.board.turn == chess.WHITE else "black",
                "id": mutator["id"],
                "name": mutator["name"],
                "description": mutator["description"],
                "message": applied,
            }
        )
        self.active_mutators.insert(0, mutator)
        self.active_mutators = self.active_mutators[:8]
        self.update_status()
        self.message = applied or f"{mutator['name']} activated. {self.message}"
        return True, self.message

    def occupied_squares(self):
        return [square for square in chess.SQUARES if self.board.piece_at(square)]

    def empty_squares(self):
        return [square for square in chess.SQUARES if self.board.piece_at(square) is None]

    def random_empty_square(self):
        empties = self.empty_squares()
        return random.choice(empties) if empties else None

    def sanitize_after_mutation(self):
        self.board.castling_rights = self.board.clean_castling_rights()
        self.board.ep_square = None

    def apply_mutator(self, mutator_id):
        if mutator_id == "march_pawns":
            changed = self.advance_all_pawns(capturing=False)
            return f"March of the Pawnguins moved {changed} pawn(s)."

        if mutator_id == "the_rumbling":
            changed = self.advance_all_pawns(capturing=True)
            return f"The Rumbling moved {changed} pawn(s)."

        if mutator_id == "they_deserved_it":
            candidates = [
                square
                for square in self.occupied_squares()
                if self.board.piece_at(square).piece_type != chess.KING
            ]
            if not candidates:
                return "Everyone deserved it, but nobody was eligible."
            square = random.choice(candidates)
            removed = self.board.remove_piece_at(square)
            self.sanitize_after_mutation()
            return f"They Deserved It removed a {PIECE_NAMES[removed.piece_type]} from {chess.square_name(square)}."

        if mutator_id == "going_woke":
            changed = self.shift_files_left()
            return f"Going Woke shifted {changed} piece(s) queenside."

        if mutator_id == "horse_girl_summoning":
            square = self.random_empty_square()
            if square is None:
                return "Horse Girl Summoning found no stable."
            self.board.set_piece_at(square, chess.Piece(chess.KNIGHT, self.board.turn))
            self.sanitize_after_mutation()
            return f"Horse Girl Summoning placed a knight on {chess.square_name(square)}."

        if mutator_id == "rook_market_crash":
            changed = 0
            for square in self.occupied_squares():
                piece = self.board.piece_at(square)
                if piece and piece.piece_type == chess.ROOK:
                    self.board.set_piece_at(square, chess.Piece(chess.BISHOP, piece.color))
                    changed += 1
            self.sanitize_after_mutation()
            return f"Rook Market Crash converted {changed} rook(s)."

        if mutator_id == "pawn_union":
            changed = self.shift_friendly_pawns_right()
            return f"Pawn Union shifted {changed} pawn(s)."

        if mutator_id == "minor_inconvenience":
            candidates = [
                square
                for square in self.occupied_squares()
                if self.board.piece_at(square).piece_type in {chess.BISHOP, chess.KNIGHT}
            ]
            if not candidates:
                return "Minor Inconvenience had no minor pieces to bother."
            square = random.choice(candidates)
            piece = self.board.piece_at(square)
            self.board.set_piece_at(square, chess.Piece(chess.PAWN, piece.color))
            self.sanitize_after_mutation()
            return f"Minor Inconvenience turned a piece on {chess.square_name(square)} into a pawn."

        return None

    def advance_all_pawns(self, capturing=False):
        moves = []
        for square in self.occupied_squares():
            piece = self.board.piece_at(square)
            if not piece or piece.piece_type != chess.PAWN:
                continue
            rank_delta = 1 if piece.color == chess.WHITE else -1
            target = square + 8 * rank_delta
            if target not in chess.SQUARES:
                continue
            target_piece = self.board.piece_at(target)
            if target_piece and not capturing:
                continue
            if target_piece and target_piece.piece_type == chess.KING:
                continue
            moves.append((square, target, piece))

        targets_written = set()
        for square, target, piece in moves:
            if square in targets_written:
                continue
            targets_written.add(target)
            self.board.remove_piece_at(square)
            if self.board.piece_at(target):
                self.board.remove_piece_at(target)
            final_piece = piece
            target_rank = chess.square_rank(target)
            if target_rank in {0, 7}:
                final_piece = chess.Piece(chess.QUEEN, piece.color)
            self.board.set_piece_at(target, final_piece)

        self.sanitize_after_mutation()
        return len(targets_written)

    def shift_files_left(self):
        # Snapshot valid moves from the original board so each piece shifts at most one square.
        moves = []
        for file_index in range(4, 8):
            for rank in range(8):
                square = chess.square(file_index, rank)
                target = chess.square(file_index - 1, rank)
                piece = self.board.piece_at(square)
                if piece and piece.piece_type != chess.KING and not self.board.piece_at(target):
                    moves.append((square, target, piece))

        for square, target, piece in moves:
            self.board.remove_piece_at(square)
            self.board.set_piece_at(target, piece)

        self.sanitize_after_mutation()
        return len(moves)

    def shift_friendly_pawns_right(self):
        # Snapshot valid moves from the original board so each pawn shifts at most one square.
        moves = []
        for file_index in range(0, 7):
            for rank in range(8):
                square = chess.square(file_index, rank)
                target = chess.square(file_index + 1, rank)
                piece = self.board.piece_at(square)
                if (
                    piece
                    and piece.color == self.board.turn
                    and piece.piece_type == chess.PAWN
                    and not self.board.piece_at(target)
                ):
                    moves.append((square, target, piece))

        for square, target, piece in moves:
            self.board.remove_piece_at(square)
            self.board.set_piece_at(target, piece)

        self.sanitize_after_mutation()
        return len(moves)

    def visible_squares(self, viewer_index):
        if self.variant_id != "fog" or viewer_index not in {0, 1}:
            return None

        color = self.player_color(viewer_index)
        visible = set()
        for square, piece in self.board.piece_map().items():
            if piece.color != color:
                continue
            visible.add(square)
            visible.update(self.board.attacks(square))

        for move in self.board.legal_moves:
            piece = self.board.piece_at(move.from_square)
            if piece and piece.color == color:
                visible.add(move.to_square)

        return visible

    def board_payload(self, viewer_index=None):
        pieces = {}
        visible = self.visible_squares(viewer_index)

        for square, piece in self.board.piece_map().items():
            if visible is not None and square not in visible:
                continue

            square_name = chess.square_name(square)
            pieces[square_name] = {
                "symbol": piece.symbol(),
                "color": "white" if piece.color == chess.WHITE else "black",
                "type": chess.piece_name(piece.piece_type),
            }

        return pieces

    def legal_moves_payload(self, viewer_index=None):
        moves = {}
        viewer_color = self.player_color(viewer_index) if viewer_index in {0, 1} else None

        for move in self.board.legal_moves:
            piece = self.board.piece_at(move.from_square)
            if viewer_color is not None and (not piece or piece.color != viewer_color):
                continue
            if self.variant_id == "dice" and piece and piece.piece_type != self.dice_piece:
                continue

            from_name = chess.square_name(move.from_square)
            moves.setdefault(from_name, []).append(
                {
                    "to": chess.square_name(move.to_square),
                    "promotion": chess.piece_symbol(move.promotion) if move.promotion else None,
                }
            )

        return moves

    def variant_payload(self):
        payload = {
            "id": self.variant_id,
            "label": self.variant["label"],
            "description": self.variant["description"],
        }

        if self.variant_id == "three_check":
            remaining = getattr(self.board, "remaining_checks", None)
            if remaining:
                payload["checks"] = {"white": 3 - remaining[0], "black": 3 - remaining[1]}

        if self.variant_id == "dice":
            payload["dicePiece"] = PIECE_NAMES[self.dice_piece] if self.dice_piece else None

        if self.variant_id == "thress":
            payload["pendingMutator"] = self.pending_mutator
            payload["activeMutators"] = self.active_mutators

        return payload

    def hidden_squares_payload(self, viewer_index):
        if self.variant_id != "fog" or viewer_index not in {0, 1}:
            return []
        visible = self.visible_squares(viewer_index)
        return [chess.square_name(sq) for sq in chess.SQUARES if sq not in visible]

    def snapshot(self, viewer_index=None):
        outcome = self.board.outcome(claim_draw=True)
        return {
            "kind": "chess",
            "gameState": self.game_state,
            "message": self.message,
            "board": self.board_payload(viewer_index),
            "hiddenSquares": self.hidden_squares_payload(viewer_index),
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "legalMoves": self.legal_moves_payload(viewer_index) if self.game_state == "playing" else {},
            "lastMove": self.last_move,
            "moveHistory": self.move_history,
            "mutatorHistory": self.mutator_history,
            "isCheck": self.board.is_check(),
            "isGameOver": self.game_state == "gameover",
            "result": self.board.result(claim_draw=True) if outcome else None,
            "termination": str(outcome.termination.name).lower() if outcome else None,
            "variant": self.variant_payload(),
        }


class Room:
    def __init__(self, code):
        self.code = code
        self.clients = [None, None]
        self.host_index = 0
        self.selected_game = "none"
        self.chess_game = None
        self.bot_difficulty = None

    def active_game(self):
        return self.chess_game

    def bot_enabled(self):
        return self.bot_difficulty in BOT_DIFFICULTIES

    def bot_payload(self):
        if not self.bot_enabled():
            return {"enabled": False, "difficulty": None, "label": None, "color": None}

        difficulty = BOT_DIFFICULTIES[self.bot_difficulty]
        return {
            "enabled": True,
            "difficulty": self.bot_difficulty,
            "label": difficulty["label"],
            "color": "black",
        }

    def players_payload(self):
        players = []
        for index, client in enumerate(self.clients):
            label = "White" if index == 0 else "Black"
            connected = client is not None
            if index == 1 and self.bot_enabled():
                label = BOT_DIFFICULTIES[self.bot_difficulty]["label"]
                connected = True
            players.append({"connected": connected, "label": label})
        return players

    def connected_count(self):
        return self.human_connected_count() + (1 if self.bot_enabled() else 0)

    def human_connected_count(self):
        return sum(client is not None for client in self.clients)

    def available_slot(self):
        if self.bot_enabled():
            return None

        for index, client in enumerate(self.clients):
            if client is None:
                return index
        return None

    def get_slot(self, ws):
        for index, client in enumerate(self.clients):
            if client is ws:
                return index
        return None

    def select_game(self, variant_id):
        if variant_id not in VARIANTS:
            return False

        self.selected_game = variant_id
        self.chess_game = ChessVariantGame(variant_id)
        self.sync_presence()
        return True

    def sync_presence(self):
        if self.human_connected_count() == 1:
            occupied = [index for index, client in enumerate(self.clients) if client is not None]
            self.host_index = occupied[0]

        if not self.chess_game:
            return

        if self.connected_count() < 2:
            self.chess_game.set_waiting("Waiting for another player to join this room.")
            return

        if self.chess_game.game_state in {"waiting", "ready"}:
            self.chess_game.set_ready()

    def empty_game_snapshot(self):
        return {
            "kind": "none",
            "gameState": "waiting",
            "message": "Create or join a room, then choose a chess variant.",
        }

    async def send_sync(self, ws):
        slot = self.get_slot(ws)
        payload = {
            "type": "sync",
            "roomCode": self.code,
            "selectedGame": self.selected_game,
            "availableGames": variants_payload(),
            "playerIndex": slot,
            "isHost": slot == self.host_index,
            "players": self.players_payload(),
            "bot": self.bot_payload(),
            "botDifficulties": bots_payload(),
            "game": self.chess_game.snapshot(slot) if self.chess_game else self.empty_game_snapshot(),
        }
        await ws.send_json(payload)

    async def broadcast_sync(self):
        for ws in self.clients:
            if ws is not None:
                await self.send_sync(ws)


class GameServer:
    def __init__(self):
        self.rooms = {}

    def create_room_code(self):
        while True:
            code = "".join(random.choice(string.digits) for _ in range(6))
            if code not in self.rooms:
                return code

    async def remove_from_room(self, ws):
        room = getattr(ws, "room", None)
        if room is None:
            return

        slot = room.get_slot(ws)
        if slot is not None:
            room.clients[slot] = None

        ws.room = None

        if room.human_connected_count() == 0:
            self.rooms.pop(room.code, None)
            return

        room.sync_presence()
        await room.broadcast_sync()

    async def create_room(self, ws):
        await self.remove_from_room(ws)

        if len(self.rooms) >= MAX_ROOMS:
            await ws.send_json({"type": "error", "message": "Server is at capacity. Try again later."})
            return

        code = self.create_room_code()
        room = Room(code)
        room.clients[0] = ws
        ws.room = room
        self.rooms[code] = room
        room.sync_presence()
        await room.broadcast_sync()

    async def create_bot_room(self, ws, difficulty):
        await self.remove_from_room(ws)

        if len(self.rooms) >= MAX_ROOMS:
            await ws.send_json({"type": "error", "message": "Server is at capacity. Try again later."})
            return

        if difficulty not in BOT_DIFFICULTIES:
            await ws.send_json({"type": "error", "message": "Choose a bot difficulty."})
            return

        code = self.create_room_code()
        room = Room(code)
        room.clients[0] = ws
        room.bot_difficulty = difficulty
        ws.room = room
        self.rooms[code] = room
        room.sync_presence()
        await room.broadcast_sync()

    async def join_room(self, ws, room_code):
        await self.remove_from_room(ws)

        room = self.rooms.get(room_code)
        if room is None:
            await ws.send_json({"type": "error", "message": "Room not found."})
            return

        slot = room.available_slot()
        if slot is None:
            await ws.send_json({"type": "error", "message": "Room is already full."})
            return

        room.clients[slot] = ws
        ws.room = room
        room.sync_presence()
        await room.broadcast_sync()

    async def play_bot_turns(self, room):
        active_game = room.active_game()
        if not room.bot_enabled() or active_game is None:
            return

        safety_turns = 0
        while (
            active_game.game_state == "playing"
            and active_game.player_index_for_turn() == 1
            and safety_turns < 4
        ):
            safety_turns += 1

            if active_game.variant_id == "thress" and active_game.pending_mutator:
                options = active_game.pending_mutator.get("options", [])
                if not options:
                    break
                active_game.choose_mutator(1, random.choice(options)["id"])
                await asyncio.sleep(0)
                continue

            if not active_game.bot_move(room.bot_difficulty):
                break
            await asyncio.sleep(0)

    async def handle_message(self, ws, payload):
        if not isinstance(payload, dict):
            await ws.send_json({"type": "error", "message": "Invalid message payload."})
            return

        message_type = payload.get("type")

        if message_type == "create_room":
            await self.create_room(ws)
            return

        if message_type == "create_bot_room":
            difficulty = str(payload.get("difficulty", "easy")).lower()
            await self.create_bot_room(ws, difficulty)
            return

        if message_type == "join_room":
            room_code = "".join(ch for ch in str(payload.get("roomCode", "")) if ch.isdigit())[:6]
            if not room_code:
                await ws.send_json({"type": "error", "message": "Enter a room code first."})
                return
            await self.join_room(ws, room_code)
            return

        room = getattr(ws, "room", None)
        if room is None:
            await ws.send_json({"type": "error", "message": "Join a room first."})
            return

        slot = room.get_slot(ws)
        is_host = slot == room.host_index
        active_game = room.active_game()

        if message_type == "leave_room":
            await self.remove_from_room(ws)
            await ws.send_json(
                lobby_sync_payload("You left the room. Create or join another one.")
            )
            return

        if message_type == "select_game":
            if not is_host:
                await ws.send_json({"type": "error", "message": "Only the host can choose the variant."})
                return
            if active_game and active_game.game_state in {"playing", "paused"}:
                await ws.send_json({"type": "error", "message": "Finish or restart before changing variants."})
                return
            if not room.select_game(str(payload.get("game", ""))):
                await ws.send_json({"type": "error", "message": "Choose a chess variant."})
                return
            await room.broadcast_sync()
            return

        if message_type == "chess_move":
            if not active_game:
                await ws.send_json({"type": "error", "message": "Choose a variant first."})
                return
            ok, message = active_game.move(
                slot,
                str(payload.get("from", "")),
                str(payload.get("to", "")),
                payload.get("promotion"),
            )
            if not ok:
                await ws.send_json({"type": "error", "message": message})
            elif room.bot_enabled():
                await self.play_bot_turns(room)
            await room.broadcast_sync()
            return

        if message_type == "choose_mutator":
            if not active_game:
                await ws.send_json({"type": "error", "message": "Choose a variant first."})
                return
            ok, message = active_game.choose_mutator(slot, str(payload.get("mutatorId", "")))
            if not ok:
                await ws.send_json({"type": "error", "message": message})
            elif room.bot_enabled():
                await self.play_bot_turns(room)
            await room.broadcast_sync()
            return

        if message_type == "start_game":
            if not is_host:
                await ws.send_json({"type": "error", "message": "Only the host can start the game."})
                return
            if room.connected_count() < 2:
                await ws.send_json({"type": "error", "message": "A second player must join first."})
                return
            if active_game is None:
                await ws.send_json({"type": "error", "message": "Choose a variant first."})
                return
            active_game.start()
            await self.play_bot_turns(room)
            await room.broadcast_sync()
            return

        if message_type == "toggle_pause":
            if is_host and active_game:
                active_game.toggle_pause()
                await room.broadcast_sync()
            return

        if message_type == "restart_game":
            if not is_host or active_game is None:
                return
            if room.connected_count() < 2:
                active_game.set_waiting("Waiting for another player to join this room.")
            else:
                active_game.restart()
                await self.play_bot_turns(room)
            await room.broadcast_sync()
            return

        if message_type == "return_to_games":
            if not is_host or active_game is None:
                return
            active_game.return_to_ready()
            await room.broadcast_sync()
            return


server = GameServer()


def variants_payload():
    return [
        {"id": key, "label": data["label"], "description": data["description"]}
        for key, data in VARIANTS.items()
    ]


def bots_payload():
    return [
        {"id": key, "label": data["label"], "description": data["description"]}
        for key, data in BOT_DIFFICULTIES.items()
    ]


def lobby_sync_payload(message="Create or join a room to begin."):
    return {
        "type": "sync",
        "roomCode": "",
        "selectedGame": "none",
        "availableGames": variants_payload(),
        "playerIndex": None,
        "isHost": False,
        "bot": {"enabled": False, "difficulty": None, "label": None, "color": None},
        "botDifficulties": bots_payload(),
        "players": [
            {"connected": False, "label": "White"},
            {"connected": False, "label": "Black"},
        ],
        "game": {
            "kind": "none",
            "gameState": "waiting",
            "message": message,
        },
    }


_CSP = (
    "default-src 'self'; "
    "connect-src 'self' ws: wss:; "
    "img-src 'self' data:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


@web.middleware
async def security_headers_middleware(request, handler):
    response = await handler(request)
    if response.prepared:
        return response
    response.headers["Content-Security-Policy"] = _CSP
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


def _client_ip(request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote or "unknown"


async def websocket_handler(request):
    client_ip = _client_ip(request)
    if _ip_connections.get(client_ip, 0) >= MAX_CONNECTIONS_PER_IP:
        raise web.HTTPTooManyRequests()

    _ip_connections[client_ip] = _ip_connections.get(client_ip, 0) + 1
    try:
        ws = web.WebSocketResponse(heartbeat=30, max_msg_size=MAX_MSG_SIZE)
        await ws.prepare(request)
        ws.room = None

        await ws.send_json(lobby_sync_payload())

        loop = asyncio.get_running_loop()
        msg_times: list[float] = []

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    now = loop.time()
                    msg_times.append(now)
                    cutoff = now - MSG_RATE_WINDOW
                    while msg_times and msg_times[0] < cutoff:
                        msg_times.pop(0)
                    if len(msg_times) > MSG_RATE_LIMIT:
                        await ws.close()
                        break

                    try:
                        payload = json.loads(msg.data)
                    except json.JSONDecodeError:
                        await ws.send_json({"type": "error", "message": "Invalid message payload."})
                        continue
                    await server.handle_message(ws, payload)
                elif msg.type == WSMsgType.ERROR:
                    break
        finally:
            await server.remove_from_room(ws)
    finally:
        count = _ip_connections.get(client_ip, 1) - 1
        if count <= 0:
            _ip_connections.pop(client_ip, None)
        else:
            _ip_connections[client_ip] = count

    return ws


async def serve_file(name, content_type):
    return web.Response(text=(ROOT / name).read_text(), content_type=content_type)


async def index_handler(_request):
    return await serve_file("index.html", "text/html")


async def js_handler(_request):
    return await serve_file("game.js", "text/javascript")


async def css_handler(_request):
    return await serve_file("styles.css", "text/css")


def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def make_app():
    app = web.Application(middlewares=[security_headers_middleware])
    app.router.add_get("/", index_handler)
    app.router.add_get("/index.html", index_handler)
    app.router.add_get("/game.js", js_handler)
    app.router.add_get("/styles.css", css_handler)
    app.router.add_get("/ws", websocket_handler)
    return app


if __name__ == "__main__":
    print(f"Local: http://localhost:{PORT}")
    print(f"LAN:   http://{local_ip()}:{PORT}")
    web.run_app(make_app(), host=HOST, port=PORT)
