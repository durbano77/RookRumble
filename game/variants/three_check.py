import chess.variant

from ..base import BaseGame


class ThreeCheckGame(BaseGame):
    board_class = chess.variant.ThreeCheckBoard

    def _set_turn_message(self):
        remaining = getattr(self.board, "remaining_checks", None)
        if remaining:
            used = [3 - remaining[0], 3 - remaining[1]]
            self.message = f"{self.color_name()} to move. Checks: White {used[0]}/3, Black {used[1]}/3."
            return
        super()._set_turn_message()

    def variant_payload(self):
        payload = super().variant_payload()
        remaining = getattr(self.board, "remaining_checks", None)
        if remaining:
            payload["checks"] = {"white": 3 - remaining[0], "black": 3 - remaining[1]}
        return payload
