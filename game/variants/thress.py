import random

import chess

from ..base import BaseGame
from ..constants import PIECE_NAMES, PIECE_VALUES
from ..registry import THRESS_MUTATORS


class ThressGame(BaseGame):
    board_class = chess.Board

    def __init__(self, variant_id):
        super().__init__(variant_id)
        self.pending_mutator = None
        self.active_mutators = []
        self.mutator_history = []

    def reset_board(self):
        super().reset_board()
        self.pending_mutator = None
        self.active_mutators = []
        self.mutator_history = []

    # ── Status ───────────────────────────────────────────────────────────────

    def _set_turn_message(self):
        if self.pending_mutator:
            self.message = f"{self.color_name()} must pick a mutator."
        else:
            self.message = f"{self.color_name()} to move. Thress cards appear every third move."

    # ── Move hooks ───────────────────────────────────────────────────────────

    def _pre_move_check(self, player_index):
        if self.pending_mutator:
            return False, "Pick a Thress mutator first."
        return True, None

    def _can_bot_move(self):
        return not self.pending_mutator

    def _after_push(self, move):
        if not self.board.outcome(claim_draw=True):
            self.maybe_offer_mutators()

    # ── Mutator selection ────────────────────────────────────────────────────

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
        if self.game_state != "playing":
            return False, "Start the game first."
        if not self.pending_mutator:
            return False, "There is no mutator to choose right now."
        if self.player_color(player_index) != self.board.turn:
            return False, "It is not your mutator choice."

        options = self.pending_mutator["options"]
        mutator = next((opt for opt in options if opt["id"] == mutator_id), None)
        if not mutator:
            return False, "Choose one of the offered mutators."

        applied = self.apply_mutator(mutator["id"])
        self.pending_mutator = None
        self.mutator_history.append({
            "ply": self.move_count + 1,
            "chooser": "white" if self.board.turn == chess.WHITE else "black",
            "id": mutator["id"],
            "name": mutator["name"],
            "description": mutator["description"],
            "message": applied,
        })
        self.active_mutators.insert(0, mutator)
        self.active_mutators = self.active_mutators[:8]
        self.update_status()
        self.message = applied or f"{mutator['name']} activated. {self.message}"
        return True, self.message

    # ── Mutator effects ──────────────────────────────────────────────────────

    def apply_mutator(self, mutator_id):
        if mutator_id == "march_pawns":
            changed = self.advance_all_pawns(capturing=False)
            return f"March of the Pawnguins moved {changed} pawn(s)."

        if mutator_id == "the_rumbling":
            changed = self.advance_all_pawns(capturing=True)
            return f"The Rumbling moved {changed} pawn(s)."

        if mutator_id == "they_deserved_it":
            candidates = [
                sq for sq in self.occupied_squares()
                if self.board.piece_at(sq).piece_type != chess.KING
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
                sq for sq in self.occupied_squares()
                if self.board.piece_at(sq).piece_type in {chess.BISHOP, chess.KNIGHT}
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
            if chess.square_rank(target) in {0, 7}:
                final_piece = chess.Piece(chess.QUEEN, piece.color)
            self.board.set_piece_at(target, final_piece)

        self.sanitize_after_mutation()
        return len(targets_written)

    def shift_files_left(self):
        # Snapshot first so each piece shifts at most one square.
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
        # Snapshot first so each pawn shifts at most one square.
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

    # ── Payload ──────────────────────────────────────────────────────────────

    def variant_payload(self):
        payload = super().variant_payload()
        payload["pendingMutator"] = self.pending_mutator
        payload["activeMutators"] = self.active_mutators
        return payload

    def mutator_history_payload(self):
        return self.mutator_history
