import chess

from ..base import BaseGame


class ClassicGame(BaseGame):
    board_class = chess.Board
