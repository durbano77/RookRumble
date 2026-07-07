import chess

from ..base import BaseGame


class BlindfoldedGame(BaseGame):
    board_class = chess.Board

    def board_payload(self, viewer_index=None):
        if self.game_state == "gameover":
            return super().board_payload(viewer_index)
        return {}

    def _set_turn_message(self):
        self.message = f"{self.color_name()} to move."
