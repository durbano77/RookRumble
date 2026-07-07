import chess

from ..base import BaseGame


class _AnarchistBoard(chess.Board):
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


class TotalAnnihilationGame(BaseGame):
    board_class = _AnarchistBoard

    def __init__(self, variant_id):
        super().__init__(variant_id)
        self._result = None

    def _after_push(self, move):
        opponent_color = self.board.turn  # turn has flipped: opponent is who's next
        if not any(p for p in self.board.piece_map().values() if p.color == opponent_color):
            winner = "White" if opponent_color == chess.BLACK else "Black"
            self.game_state = "gameover"
            self.message = f"Total annihilation — {winner} wins!"
            self._result = "1-0" if opponent_color == chess.BLACK else "0-1"

    def update_status(self):
        if self.game_state == "gameover":
            return
        self._set_turn_message()

    def _set_turn_message(self):
        pieces = self.board.piece_map().values()
        white_count = sum(1 for p in pieces if p.color == chess.WHITE)
        black_count = sum(1 for p in pieces if p.color == chess.BLACK)
        self.message = f"{self.color_name()} to move  —  ♔ {white_count}  ♚ {black_count}"

    def score_bot_move(self, move, profile):
        bot_color = self.board.turn
        target = self.board.piece_at(move.to_square)
        if target and target.color != bot_color:
            self.board.push(move)
            try:
                remaining = sum(1 for p in self.board.piece_map().values() if p.color != bot_color)
            finally:
                self.board.pop()
            if remaining == 0:
                return 1_000_000
        return super().score_bot_move(move, profile)

    def snapshot(self, viewer_index=None):
        snap = super().snapshot(viewer_index)
        if self._result:
            snap["result"] = self._result
        return snap
