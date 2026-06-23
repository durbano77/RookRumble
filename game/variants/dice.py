import random

import chess

from ..base import BaseGame
from ..constants import PIECE_NAMES


class DiceGame(BaseGame):
    board_class = chess.Board

    def __init__(self, variant_id):
        super().__init__(variant_id)
        self.dice_piece = None

    def reset_board(self):
        super().reset_board()
        self.dice_piece = None
        self.roll_dice()

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
        possible = [p for p in choices if p in legal_piece_types]
        self.dice_piece = random.choice(possible)

    def _set_turn_message(self):
        if self.dice_piece is None:
            self.roll_dice()
        self.message = f"{self.color_name()} to move a {PIECE_NAMES[self.dice_piece]}."

    def _validate_piece_move(self, piece, from_square):
        if piece.piece_type != self.dice_piece:
            return False, f"The die says {PIECE_NAMES[self.dice_piece]}."
        return True, None

    def candidate_moves(self):
        moves = list(self.board.legal_moves)
        if self.dice_piece is not None:
            moves = [
                m for m in moves
                if self.board.piece_at(m.from_square)
                and self.board.piece_at(m.from_square).piece_type == self.dice_piece
            ]
        return moves

    def _after_push(self, move):
        if not self.board.outcome(claim_draw=True):
            self.roll_dice()

    def _is_legal_move_visible(self, move, piece):
        return bool(piece and piece.piece_type == self.dice_piece)

    def variant_payload(self):
        payload = super().variant_payload()
        payload["dicePiece"] = PIECE_NAMES[self.dice_piece] if self.dice_piece else None
        return payload
