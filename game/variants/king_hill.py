import chess.variant

from ..base import BaseGame


class KingHillGame(BaseGame):
    board_class = chess.variant.KingOfTheHillBoard
