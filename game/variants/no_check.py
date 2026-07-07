import chess

from ..base import BaseGame


class _NoCheckBoard(chess.Board):
    @property
    def legal_moves(self):
        return self.pseudo_legal_moves

    def is_check(self):
        return False

    def is_checkmate(self):
        return False

    def is_stalemate(self):
        return False

    def outcome(self, claim_draw=False):
        return None


class NoCheckGame(BaseGame):
    board_class = _NoCheckBoard

    def __init__(self, variant_id):
        super().__init__(variant_id)
        self._result = None

    def _after_push(self, move):
        loser_color = self.board.turn  # turn has flipped: loser is who's next
        if not self.board.pieces(chess.KING, loser_color):
            winner = "White" if loser_color == chess.BLACK else "Black"
            self.game_state = "gameover"
            self.message = f"{winner} captured the king — {winner} wins!"
            self._result = "1-0" if loser_color == chess.BLACK else "0-1"

    def update_status(self):
        if self.game_state == "gameover":
            return
        self._set_turn_message()

    def _set_turn_message(self):
        self.message = f"{self.color_name()} to move."

    def score_bot_move(self, move, profile):
        target = self.board.piece_at(move.to_square)
        if target and target.piece_type == chess.KING:
            return 1_000_000
        return super().score_bot_move(move, profile)

    def snapshot(self, viewer_index=None):
        snap = super().snapshot(viewer_index)
        if self._result:
            snap["result"] = self._result
        return snap
