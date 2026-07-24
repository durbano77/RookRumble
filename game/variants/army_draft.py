import random
import time

import chess

from ..base import BaseGame

DRAFT_BUDGET = 39

DRAFT_PIECE_TYPES = {
    "pawn": chess.PAWN,
    "knight": chess.KNIGHT,
    "bishop": chess.BISHOP,
    "rook": chess.ROOK,
    "queen": chess.QUEEN,
}

DRAFT_POINT_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
}

WHITE_DRAFT_RANKS = {0, 1}  # ranks "1" and "2"
BLACK_DRAFT_RANKS = {6, 7}  # ranks "7" and "8"


class ArmyDraftGame(BaseGame):
    board_class = chess.Board

    def __init__(self, variant_id):
        super().__init__(variant_id)
        self.drafts = [None, None]  # per player: list of (square, piece_type) once submitted

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def reset_board(self):
        self.board = chess.Board(None)
        self.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
        self.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
        self.board.turn = chess.WHITE
        self.board.castling_rights = chess.BB_EMPTY
        self.board.ep_square = None
        self.last_move = None
        self.move_count = 0
        self.move_history = []
        self.move_history_san = []
        self.turn_started = None
        self.drafts = [None, None]
        if self.timer_config:
            initial = float(self.timer_config["minutes"] * 60)
            self.remaining = [initial, initial]

    def start(self):
        self.reset_board()
        self.game_state = "drafting"
        self.message = f"Both players are drafting their armies ({DRAFT_BUDGET}-point budget)."

    def restart(self):
        self.start()

    def _set_turn_message(self):
        self.message = f"{self.color_name()} to move."

    # ── Draft helpers ────────────────────────────────────────────────────────

    def _draft_ranks(self, color):
        return WHITE_DRAFT_RANKS if color == chess.WHITE else BLACK_DRAFT_RANKS

    def _king_square(self, color):
        return chess.E1 if color == chess.WHITE else chess.E8

    def validate_draft(self, color, placements):
        if not isinstance(placements, list):
            return False, "Malformed army submission.", None

        allowed_ranks = self._draft_ranks(color)
        king_square = self._king_square(color)
        seen_squares = set()
        total_points = 0
        parsed = []

        for entry in placements:
            if not isinstance(entry, dict):
                return False, "Malformed placement.", None
            kind = str(entry.get("type", "")).lower()
            if kind not in DRAFT_PIECE_TYPES:
                return False, f"Unknown piece type '{kind}'.", None
            try:
                square = chess.parse_square(str(entry.get("square", "")))
            except ValueError:
                return False, "Invalid square.", None
            if chess.square_rank(square) not in allowed_ranks:
                return False, "Units must be placed on your own first two ranks.", None
            if square == king_square:
                return False, "That square is reserved for your king.", None
            if square in seen_squares:
                return False, "Two units can't share a square.", None
            seen_squares.add(square)
            piece_type = DRAFT_PIECE_TYPES[kind]
            total_points += DRAFT_POINT_VALUES[piece_type]
            parsed.append((square, piece_type))

        if total_points > DRAFT_BUDGET:
            return False, f"Army costs {total_points} points — budget is {DRAFT_BUDGET}.", None

        return True, None, parsed

    def submit_draft(self, player_index, placements):
        if self.game_state != "drafting":
            return False, "Drafting isn't open right now."
        if player_index not in (0, 1):
            return False, "Join a room first."
        if self.drafts[player_index] is not None:
            return False, "You already locked in your army."

        color = self.player_color(player_index)
        ok, err, parsed = self.validate_draft(color, placements)
        if not ok:
            return False, err

        self.drafts[player_index] = parsed
        for square, piece_type in parsed:
            self.board.set_piece_at(square, chess.Piece(piece_type, color))

        self.message = f"{self.color_name(color)} locked in their army."

        if self.drafts[0] is not None and self.drafts[1] is not None:
            self.board.turn = chess.WHITE
            self.game_state = "playing"
            if self.timer_config:
                self.turn_started = time.monotonic()
            self.update_status()
        else:
            self.message += " Waiting for the opponent to finish drafting."

        return True, self.message

    def _random_draft(self, color):
        allowed_squares = [
            sq for sq in chess.SQUARES
            if chess.square_rank(sq) in self._draft_ranks(color) and sq != self._king_square(color)
        ]
        random.shuffle(allowed_squares)

        budget = DRAFT_BUDGET
        kinds = list(DRAFT_PIECE_TYPES.items())
        placements = []
        for square in allowed_squares:
            affordable = [(name, pt) for name, pt in kinds if DRAFT_POINT_VALUES[pt] <= budget]
            if not affordable:
                break
            name, piece_type = random.choice(affordable)
            budget -= DRAFT_POINT_VALUES[piece_type]
            placements.append({"type": name, "square": chess.square_name(square)})
            if budget <= 0:
                break
        return placements

    def bot_needs_predraft(self):
        return self.game_state == "drafting" and self.drafts[1] is None

    def bot_predraft(self, difficulty):
        self.submit_draft(1, self._random_draft(chess.BLACK))

    # ── Payload ──────────────────────────────────────────────────────────────

    def board_payload(self, viewer_index=None):
        if self.game_state != "drafting":
            return super().board_payload(viewer_index)

        payload = {}
        for square, piece in self.board.piece_map().items():
            if piece.piece_type == chess.KING or (
                viewer_index in (0, 1) and piece.color == self.player_color(viewer_index)
            ):
                payload[chess.square_name(square)] = {
                    "symbol": piece.symbol(),
                    "color": "white" if piece.color == chess.WHITE else "black",
                    "type": chess.piece_name(piece.piece_type),
                }
        return payload

    def variant_payload(self):
        payload = super().variant_payload()
        payload["draftBudget"] = DRAFT_BUDGET
        payload["draftPieceValues"] = {name: DRAFT_POINT_VALUES[pt] for name, pt in DRAFT_PIECE_TYPES.items()}
        payload["draftReady"] = [self.drafts[0] is not None, self.drafts[1] is not None]
        return payload
