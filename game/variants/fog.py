import chess

from ..base import BaseGame


class FogGame(BaseGame):
    board_class = chess.Board

    def visible_squares(self, viewer_index):
        if viewer_index not in {0, 1}:
            return None

        color = self.player_color(viewer_index)
        visible = set()
        for square, piece in self.board.piece_map().items():
            if piece.color != color:
                continue
            visible.add(square)
            visible.update(self.board.attacks(square))

        for move in self.board.legal_moves:
            piece = self.board.piece_at(move.from_square)
            if piece and piece.color == color:
                visible.add(move.to_square)

        return visible

    def hidden_squares_payload(self, viewer_index):
        if viewer_index not in {0, 1}:
            return []
        visible = self.visible_squares(viewer_index)
        return [chess.square_name(sq) for sq in chess.SQUARES if sq not in visible]
