import chess.variant

from ..base import BaseGame


class AtomicGame(BaseGame):
    board_class = chess.variant.AtomicBoard
