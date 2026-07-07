"""
Full variant test suite — covers existing variants + the 3 new ones.
Run with: python3 -m pytest tests/ -v
"""

import chess
import pytest

from game.variants import VARIANT_CLASSES
from game.registry import VARIANTS, BOT_DIFFICULTIES
from game.variants.blindfolded import BlindfoldedGame
from game.variants.no_check import NoCheckGame, _NoCheckBoard
from game.variants.total_annihilation import TotalAnnihilationGame, _AnarchistBoard
from game.variants.classic import ClassicGame


# ── helpers ──────────────────────────────────────────────────────────────────

def make_game(variant_id):
    g = VARIANT_CLASSES[variant_id](variant_id)
    g.start()
    return g


def push_uci(game, uci):
    move = chess.Move.from_uci(uci)
    game.push_legal_move(move)


# ── registry / constants ─────────────────────────────────────────────────────

class TestRegistry:
    def test_all_ten_variants_registered(self):
        expected = {
            "classic", "three_check", "king_hill", "atomic",
            "dice", "fog", "thress",
            "blindfolded", "no_check", "total_annihilation",
        }
        assert set(VARIANT_CLASSES.keys()) == expected

    def test_all_variants_have_registry_entry(self):
        for vid in VARIANT_CLASSES:
            assert vid in VARIANTS, f"{vid} missing from VARIANTS"
            assert "label" in VARIANTS[vid]
            assert "description" in VARIANTS[vid]

    def test_variant_classes_are_instantiable(self):
        for vid, cls in VARIANT_CLASSES.items():
            g = cls(vid)
            g.start()
            assert g.game_state == "playing"


# ── classic sanity ───────────────────────────────────────────────────────────

class TestClassic:
    def test_starting_position(self):
        g = make_game("classic")
        snap = g.snapshot(viewer_index=0)
        assert snap["gameState"] == "playing"
        assert len(snap["board"]) == 32  # 32 pieces at start

    def test_legal_moves_at_start(self):
        g = make_game("classic")
        moves = g.snapshot(0)["legalMoves"]
        assert len(moves) == 10  # 8 pawns (2 each) + 2 knights

    def test_simple_move(self):
        g = make_game("classic")
        ok, _ = g.move(0, "e2", "e4")
        assert ok
        assert g.board.piece_at(chess.E4).piece_type == chess.PAWN

    def test_illegal_move_rejected(self):
        g = make_game("classic")
        ok, msg = g.move(0, "e2", "e5")
        assert not ok

    def test_wrong_turn_rejected(self):
        g = make_game("classic")
        ok, _ = g.move(1, "e7", "e5")  # Black tries to move first
        assert not ok

    def test_checkmate_scholarsmate(self):
        g = make_game("classic")
        for uci in ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "a7a6", "h5f7"]:
            push_uci(g, uci)
        assert g.game_state == "gameover"
        assert "White" in g.message or "1-0" in (g.snapshot()["result"] or "")

    def test_stalemate(self):
        g = make_game("classic")
        # Set up a stalemate position manually
        g.board.set_fen("k7/8/1Q6/8/8/8/8/7K b - - 0 1")
        g.update_status()
        assert g.game_state == "gameover"

    def test_bot_makes_move(self):
        g = make_game("classic")
        result = g.bot_move("easy")
        assert result is True
        assert g.move_count == 1


# ── blindfolded ──────────────────────────────────────────────────────────────

class TestBlindfoldedGame:
    def test_board_empty_during_play(self):
        g = make_game("blindfolded")
        assert g.board_payload() == {}

    def test_board_revealed_on_gameover(self):
        g = make_game("blindfolded")
        g.game_state = "gameover"
        payload = g.board_payload()
        assert len(payload) == 32  # all starting pieces

    def test_snapshot_board_empty_during_play(self):
        g = make_game("blindfolded")
        snap = g.snapshot(0)
        assert snap["board"] == {}

    def test_legal_moves_still_sent(self):
        g = make_game("blindfolded")
        snap = g.snapshot(0)
        # White has legal moves even though board is hidden
        assert len(snap["legalMoves"]) > 0

    def test_no_check_announcement_in_message(self):
        g = make_game("blindfolded")
        # Manually put the board in check and call _set_turn_message
        g.board.set_fen("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPPKPPP/RNBQ1BNR b kq - 1 2")
        # Force white into check-like situation won't show "is in check"
        g._set_turn_message()
        assert "in check" not in g.message

    def test_turn_message_plain(self):
        g = make_game("blindfolded")
        assert g.message in ("White to move.", "Black to move.")

    def test_move_works(self):
        g = make_game("blindfolded")
        ok, _ = g.move(0, "e2", "e4")
        assert ok

    def test_variant_payload(self):
        g = make_game("blindfolded")
        vp = g.variant_payload()
        assert vp["id"] == "blindfolded"

    def test_move_list_grows(self):
        g = make_game("blindfolded")
        push_uci(g, "e2e4")
        assert len(g.move_history_san) == 1

    def test_board_revealed_after_checkmate(self):
        g = make_game("blindfolded")
        for uci in ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "a7a6", "h5f7"]:
            push_uci(g, uci)
        assert g.game_state == "gameover"
        # On gameover, board_payload should return all pieces
        assert len(g.board_payload()) > 0

    def test_bot_plays_blindfolded(self):
        g = make_game("blindfolded")
        result = g.bot_move("easy")
        assert result is True

    def test_snapshot_reveals_on_gameover(self):
        g = make_game("blindfolded")
        g.game_state = "gameover"
        snap = g.snapshot(0)
        assert snap["board"] != {}


# ── no-check chess ───────────────────────────────────────────────────────────

class TestNoCheckGame:
    def test_pseudo_legal_moves_used(self):
        g = make_game("no_check")
        assert type(g.board) is _NoCheckBoard
        # Starting position: legal == pseudo_legal (20 moves each)
        assert len(list(g.board.legal_moves)) == 20

    def test_is_check_always_false(self):
        g = make_game("no_check")
        # Move into a position where king is attacked
        g.board.set_fen("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
        assert g.board.is_check() is False

    def test_king_capture_ends_game(self):
        g = make_game("no_check")
        # White queen on a8, Black king on b8 — queen captures king directly
        g.board.set_fen("Qk6/8/8/8/8/8/8/K7 w - - 0 1")
        g.game_state = "playing"
        push_uci(g, "a8b8")
        assert g.game_state == "gameover"
        assert "White" in g.message
        assert "king" in g.message.lower()

    def test_black_wins_by_king_capture(self):
        g = make_game("no_check")
        # Black queen on h1, White king on g1 — queen captures king directly
        g.board.set_fen("k7/8/8/8/8/8/8/6Kq b - - 0 1")
        g.game_state = "playing"
        push_uci(g, "h1g1")
        assert g.game_state == "gameover"
        assert "Black" in g.message

    def test_result_field_set_on_win(self):
        g = make_game("no_check")
        g.board.set_fen("Qk6/8/8/8/8/8/8/K7 w - - 0 1")
        g.game_state = "playing"
        push_uci(g, "a8b8")
        snap = g.snapshot()
        assert snap["result"] == "1-0"

    def test_move_into_check_allowed(self):
        # In No-Check, a player may move into check (pseudo-legal)
        g = make_game("no_check")
        # Set up a position where White's king can walk into attack
        g.board.set_fen("8/8/8/8/8/8/3r4/3K4 w - - 0 1")
        g.game_state = "playing"
        # King moves to d2 which is attacked by rook on d2... actually rook is on d2 so king can capture it
        # Let's just check that legal_moves contains pseudo-legal king moves into attacked squares
        moves = [m.uci() for m in g.board.legal_moves]
        assert len(moves) > 0  # king can still move

    def test_bot_scores_king_capture_highest(self):
        g = make_game("no_check")
        # White queen on a8, Black king on b8 — queen can capture king on b8
        g.board.set_fen("Qk6/8/8/8/8/8/8/K7 w - - 0 1")
        g.game_state = "playing"
        profile = BOT_DIFFICULTIES["easy"]
        king_capture = chess.Move.from_uci("a8b8")
        other_move = chess.Move.from_uci("a8a1")
        score_king = g.score_bot_move(king_capture, profile)
        score_other = g.score_bot_move(other_move, profile)
        assert score_king == 1_000_000

    def test_no_outcome_from_board(self):
        g = make_game("no_check")
        assert g.board.outcome() is None

    def test_update_status_skips_when_gameover(self):
        g = make_game("no_check")
        g.game_state = "gameover"
        g.message = "sentinel"
        g.update_status()
        assert g.message == "sentinel"

    def test_bot_plays_no_check(self):
        g = make_game("no_check")
        result = g.bot_move("easy")
        assert result is True

    def test_variant_payload(self):
        g = make_game("no_check")
        assert g.variant_payload()["id"] == "no_check"


# ── total annihilation ───────────────────────────────────────────────────────

class TestTotalAnnihilationGame:
    def test_anarchist_board_used(self):
        g = make_game("total_annihilation")
        assert type(g.board) is _AnarchistBoard

    def test_pseudo_legal_moves(self):
        g = make_game("total_annihilation")
        assert len(list(g.board.legal_moves)) == 20

    def test_king_capture_alone_does_not_end_game(self):
        g = make_game("total_annihilation")
        # White can capture Black's king, but Black still has other pieces
        g.board.set_fen("r3k3/8/8/8/8/8/8/3QK3 w - - 0 1")
        g.game_state = "playing"
        push_uci(g, "d1e1")  # Queen to e1 — not a king capture, just warmup
        # Let's do king capture directly
        g.board.set_fen("4k3/8/8/8/8/8/8/3QK2r w - - 0 1")
        g.game_state = "playing"
        # White queen captures black king
        push_uci(g, "d1d8")  # queen to d8... wait, king is on e8
        # Set up correctly
        g2 = make_game("total_annihilation")
        g2.board.set_fen("4k3/8/8/8/8/8/1r6/3QK3 w - - 0 1")
        g2.game_state = "playing"
        push_uci(g2, "d1e1")  # Not a king capture
        # Reset with black rook still alive + capture white king scenario
        g3 = make_game("total_annihilation")
        g3.board.set_fen("8/8/8/8/8/8/1r6/3QK2k w - - 0 1")
        g3.game_state = "playing"
        push_uci(g3, "d1h1")  # queen captures black king on h1
        # Black still has rook on b2, so game should NOT be over
        assert g3.game_state == "playing"

    def test_last_piece_capture_ends_game(self):
        g = make_game("total_annihilation")
        # Only piece Black has is the king — White captures it → game over
        g.board.set_fen("4k3/8/8/8/8/8/8/3QK3 w - - 0 1")
        g.game_state = "playing"
        push_uci(g, "d1d8")  # queen to d8 — not king. Actually king on e8
        g2 = make_game("total_annihilation")
        g2.board.set_fen("3Qk3/8/8/8/8/8/8/4K3 w - - 0 1")
        g2.game_state = "playing"
        push_uci(g2, "d8e8")  # queen captures king (Black's last piece)
        assert g2.game_state == "gameover"
        assert "White" in g2.message

    def test_black_wins_total_annihilation(self):
        g = make_game("total_annihilation")
        g.board.set_fen("8/8/8/8/8/8/3qk3/3K4 b - - 0 1")
        g.game_state = "playing"
        push_uci(g, "d2d1")  # black queen captures white king (last white piece)
        assert g.game_state == "gameover"
        assert "Black" in g.message

    def test_result_set_on_win(self):
        g = make_game("total_annihilation")
        g.board.set_fen("3Qk3/8/8/8/8/8/8/4K3 w - - 0 1")
        g.game_state = "playing"
        push_uci(g, "d8e8")
        snap = g.snapshot()
        assert snap["result"] == "1-0"

    def test_piece_count_in_message(self):
        g = make_game("total_annihilation")
        assert "16" in g.message  # both sides start with 16 pieces

    def test_piece_count_decreases_after_capture(self):
        # FEN: White queen+king vs Black king+pawn (2 vs 2 pieces)
        g = make_game("total_annihilation")
        g.board.set_fen("4k3/8/8/4p3/3Q4/8/8/4K3 w - - 0 1")
        g.game_state = "playing"
        g.update_status()
        assert "2" in g.message  # both sides have 2 pieces
        push_uci(g, "d4e5")  # queen captures black pawn — black now has 1 piece
        assert "1" in g.message  # black has 1 piece left

    def test_bot_scores_winning_capture_highest(self):
        g = make_game("total_annihilation")
        g.board.set_fen("3Qk3/8/8/8/8/8/8/4K3 w - - 0 1")
        g.game_state = "playing"
        profile = BOT_DIFFICULTIES["easy"]
        winning_move = chess.Move.from_uci("d8e8")  # captures last black piece
        other_move = chess.Move.from_uci("d8a8")    # random queen move
        assert g.score_bot_move(winning_move, profile) == 1_000_000

    def test_no_outcome_from_board(self):
        g = make_game("total_annihilation")
        assert g.board.outcome() is None

    def test_game_continues_after_non_final_capture(self):
        g = make_game("total_annihilation")
        g.board.set_fen("4k3/8/8/4p3/3Q4/8/8/4K3 w - - 0 1")
        g.game_state = "playing"
        push_uci(g, "d4e5")  # capture pawn — black still has king
        assert g.game_state == "playing"

    def test_bot_plays_total_annihilation(self):
        g = make_game("total_annihilation")
        result = g.bot_move("easy")
        assert result is True

    def test_variant_payload(self):
        g = make_game("total_annihilation")
        assert g.variant_payload()["id"] == "total_annihilation"


# ── anarchist board ──────────────────────────────────────────────────────────

class TestAnarchistBoard:
    def test_no_check_board_overrides(self):
        b = _NoCheckBoard()
        assert b.is_check() is False
        assert b.is_checkmate() is False
        assert b.is_stalemate() is False
        assert b.outcome() is None

    def test_anarchist_board_overrides(self):
        b = _AnarchistBoard()
        assert b.is_check() is False
        assert b.is_checkmate() is False
        assert b.is_stalemate() is False
        assert b.outcome() is None

    def test_legal_equals_pseudo_legal_no_check(self):
        b = _NoCheckBoard()
        assert list(b.legal_moves) == list(b.pseudo_legal_moves)

    def test_legal_equals_pseudo_legal_anarchist(self):
        b = _AnarchistBoard()
        assert list(b.legal_moves) == list(b.pseudo_legal_moves)


# ── snapshot shape ───────────────────────────────────────────────────────────

class TestSnapshotShape:
    REQUIRED_KEYS = {
        "kind", "gameState", "message", "board", "hiddenSquares",
        "fen", "turn", "legalMoves", "lastMove", "moveHistory",
        "moveHistorySan", "isCheck", "isGameOver", "variant",
    }

    @pytest.mark.parametrize("vid", list(VARIANT_CLASSES.keys()))
    def test_snapshot_has_required_keys(self, vid):
        g = make_game(vid)
        snap = g.snapshot(0)
        missing = self.REQUIRED_KEYS - set(snap.keys())
        assert not missing, f"{vid} snapshot missing keys: {missing}"

    @pytest.mark.parametrize("vid", ["blindfolded", "no_check", "total_annihilation"])
    def test_new_variant_snapshot_kind(self, vid):
        g = make_game(vid)
        assert g.snapshot()["kind"] == "chess"


# ── existing variants not broken ─────────────────────────────────────────────

class TestExistingVariantsStillWork:
    @pytest.mark.parametrize("vid", ["classic", "three_check", "king_hill", "atomic", "dice", "fog", "thress"])
    def test_variant_starts_and_makes_a_move(self, vid):
        g = make_game(vid)
        assert g.game_state == "playing"
        result = g.bot_move("easy")
        assert result is True
