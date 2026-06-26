import random
import time

import chess

from .constants import PIECE_NAMES, PIECE_VALUES, PROMOTION_MAP
from .registry import BOT_DIFFICULTIES, VARIANTS


class BaseGame:
    board_class = chess.Board
    pending_mutator = None  # class-level sentinel; ThressGame shadows with instance attr

    def __init__(self, variant_id):
        self.variant_id = variant_id
        self.variant = VARIANTS[variant_id]
        self.board = self.board_class()
        self.game_state = "waiting"
        self.message = "Choose a variant, wait for both players, then start."
        self.last_move = None
        self.move_count = 0
        self.move_history = []
        self.move_history_san = []
        self.timer_config = None          # {"minutes": int, "increment": int} or None
        self.remaining = [None, None]     # seconds remaining for [white, black]
        self.turn_started = None          # monotonic timestamp when current turn began

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def reset_board(self):
        self.board = self.board_class()
        self.last_move = None
        self.move_count = 0
        self.move_history = []
        self.move_history_san = []
        self.turn_started = None
        if self.timer_config:
            initial = float(self.timer_config["minutes"] * 60)
            self.remaining = [initial, initial]

    def set_timer(self, config):
        self.timer_config = config
        initial = float(config["minutes"] * 60)
        self.remaining = [initial, initial]

    def set_waiting(self, message="Waiting for another player to join this room."):
        self.reset_board()
        self.game_state = "waiting"
        self.message = message

    def set_ready(self):
        self.reset_board()
        self.game_state = "ready"
        self.message = f"{self.variant['label']} selected. Host can start."

    def start(self):
        self.reset_board()
        self.game_state = "playing"
        if self.timer_config:
            self.turn_started = time.monotonic()
        self.update_status()

    def restart(self):
        self.start()

    def return_to_ready(self):
        self.set_ready()

    def toggle_pause(self):
        if self.game_state == "playing":
            self.game_state = "paused"
            self.message = "Game paused by the host."
            if self.timer_config and self.turn_started is not None:
                elapsed = time.monotonic() - self.turn_started
                active = self.player_index_for_turn()
                self.remaining[active] = max(0.0, self.remaining[active] - elapsed)
                self.turn_started = None
        elif self.game_state == "paused":
            self.game_state = "playing"
            if self.timer_config:
                self.turn_started = time.monotonic()
            self.update_status()

    # ── Timer ────────────────────────────────────────────────────────────────

    def _apply_move_clock(self, mover_index):
        if self.timer_config is None or self.turn_started is None:
            return
        now = time.monotonic()
        elapsed = now - self.turn_started
        increment = self.timer_config.get("increment", 0)
        self.remaining[mover_index] = max(0.0, self.remaining[mover_index] - elapsed + increment)
        if self.remaining[mover_index] <= 0:
            loser = "White" if mover_index == 0 else "Black"
            winner = "Black" if mover_index == 0 else "White"
            self.game_state = "gameover"
            self.message = f"{loser} ran out of time. {winner} wins."
            self.turn_started = None
        else:
            self.turn_started = now

    def check_timeout(self):
        if self.timer_config is None or self.turn_started is None or self.game_state != "playing":
            return False
        active = self.player_index_for_turn()
        elapsed = time.monotonic() - self.turn_started
        if self.remaining[active] - elapsed <= 0:
            loser = "White" if active == 0 else "Black"
            winner = "Black" if active == 0 else "White"
            self.remaining[active] = 0.0
            self.game_state = "gameover"
            self.message = f"{loser} ran out of time. {winner} wins."
            self.turn_started = None
            return True
        return False

    def clock_snapshot(self):
        if self.timer_config is None:
            return None
        remaining = list(self.remaining)
        if self.game_state == "playing" and self.turn_started is not None:
            active = self.player_index_for_turn()
            elapsed = time.monotonic() - self.turn_started
            remaining[active] = max(0.0, remaining[active] - elapsed)
        return {
            "remaining": remaining,
            "initial": self.timer_config["minutes"] * 60,
            "increment": self.timer_config.get("increment", 0),
        }

    # ── Player helpers ───────────────────────────────────────────────────────

    def player_color(self, player_index):
        return chess.WHITE if player_index == 0 else chess.BLACK

    def player_index_for_turn(self):
        return 0 if self.board.turn == chess.WHITE else 1

    def color_name(self, color=None):
        active_color = self.board.turn if color is None else color
        return "White" if active_color == chess.WHITE else "Black"

    # ── Status ───────────────────────────────────────────────────────────────

    def update_status(self):
        outcome = self.board.outcome(claim_draw=True)
        if outcome:
            self.game_state = "gameover"
            self.message = "Draw." if outcome.winner is None else f"{self.color_name(outcome.winner)} wins."
            return
        self._set_turn_message()

    def _set_turn_message(self):
        if self.board.is_check():
            self.message = f"{self.color_name()} is in check."
        else:
            self.message = f"{self.color_name()} to move."

    # ── Move validation ──────────────────────────────────────────────────────

    def needs_promotion(self, from_square, to_square):
        piece = self.board.piece_at(from_square)
        if not piece or piece.piece_type != chess.PAWN:
            return False
        to_rank = chess.square_rank(to_square)
        return (piece.color == chess.WHITE and to_rank == 7) or (
            piece.color == chess.BLACK and to_rank == 0
        )

    def _pre_move_check(self, player_index):
        return True, None

    def _validate_piece_move(self, piece, from_square):
        return True, None

    def move(self, player_index, from_name, to_name, promotion=None):
        if self.game_state != "playing":
            return False, "Start the game first."
        if player_index is None or self.player_color(player_index) != self.board.turn:
            return False, "It is not your turn."

        ok, err = self._pre_move_check(player_index)
        if not ok:
            return False, err

        try:
            from_square = chess.parse_square(from_name)
            to_square = chess.parse_square(to_name)
        except ValueError:
            return False, "That square is not valid."

        piece = self.board.piece_at(from_square)
        if piece is None:
            return False, "There is no piece on that square."
        if piece.color != self.player_color(player_index):
            return False, "That is not your piece."

        ok, err = self._validate_piece_move(piece, from_square)
        if not ok:
            return False, err

        promotion_piece = None
        if self.needs_promotion(from_square, to_square):
            promotion_piece = PROMOTION_MAP.get(str(promotion or "q").lower(), chess.QUEEN)

        chess_move = chess.Move(from_square, to_square, promotion=promotion_piece)
        if chess_move not in self.board.legal_moves:
            return False, "That move is not legal."

        self.push_legal_move(chess_move)
        return True, self.message

    def candidate_moves(self):
        return list(self.board.legal_moves)

    def push_legal_move(self, move):
        mover_index = self.player_index_for_turn()
        san = self.board.san(move)
        self.board.push(move)
        self.move_count += 1
        self.last_move = {
            "from": chess.square_name(move.from_square),
            "to": chess.square_name(move.to_square),
            "promotion": chess.piece_symbol(move.promotion) if move.promotion else None,
        }
        self.move_history.append(move.uci())
        self.move_history_san.append(san)
        self._after_push(move)
        self._apply_move_clock(mover_index)
        if self.game_state != "gameover":
            self.update_status()

    def _after_push(self, move):
        pass

    # ── Mutator stub (overridden by ThressGame) ──────────────────────────────

    def choose_mutator(self, player_index, mutator_id):
        return False, "Thress is not selected."

    # ── Bot ──────────────────────────────────────────────────────────────────

    def _can_bot_move(self):
        return True

    def bot_move(self, difficulty):
        if self.game_state != "playing" or not self._can_bot_move():
            return False
        move = self.choose_bot_move(difficulty)
        if move is None:
            self.update_status()
            return False
        self.push_legal_move(move)
        return True

    def choose_bot_move(self, difficulty):
        moves = self.candidate_moves()
        if not moves:
            return None

        profile = BOT_DIFFICULTIES.get(difficulty, BOT_DIFFICULTIES["easy"])
        skill = profile.get("skill", 0.4)
        chaos = profile.get("chaos", 0.5)

        if random.random() < chaos * (1 - skill) * 0.72:
            return random.choice(moves)

        scored = [(self.score_bot_move(move, profile), move) for move in moves]
        scored.sort(key=lambda item: item[0], reverse=True)

        if profile.get("style") == "chaos":
            top_count = max(2, min(len(scored), 3 + int(chaos * 12)))
            return random.choice([move for _, move in scored[:top_count]])

        if skill < 0.35:
            top_count = max(1, min(len(scored), 8))
            return random.choice([move for _, move in scored[:top_count]])

        best_score = scored[0][0]
        tolerance = 4 + (1 - skill) * 90 + chaos * 45
        best_moves = [move for score, move in scored if score >= best_score - tolerance]
        return random.choice(best_moves)

    def score_bot_move(self, move, profile):
        bot_color = self.board.turn
        piece = self.board.piece_at(move.from_square)
        score = 0
        greed = profile.get("greed", 0.55)
        aggression = profile.get("aggression", 0.55)
        chaos = profile.get("chaos", 0.4)
        skill = profile.get("skill", 0.5)

        if move.promotion:
            score += PIECE_VALUES.get(move.promotion, 0)

        if self.board.is_capture(move):
            captured = self.board.piece_at(move.to_square)
            attacker = self.board.piece_at(move.from_square)
            if captured:
                score += PIECE_VALUES[captured.piece_type] * (0.9 + greed * 2.0)
            if attacker:
                score -= PIECE_VALUES[attacker.piece_type] * (0.22 - skill * 0.12)

        if piece:
            score += self.personality_piece_bonus(move, piece, profile)

        self.board.push(move)
        try:
            outcome = self.board.outcome(claim_draw=True)
            if outcome:
                if outcome.winner == bot_color:
                    score += 100000
                elif outcome.winner is None:
                    score += 10
                else:
                    score -= 100000
            else:
                score += self.material_score(bot_color) * (0.35 + skill * 0.85)
                if self.board.is_check():
                    score += 35 + aggression * 80
        finally:
            self.board.pop()

        # Small jitter keeps repeated bot games from feeling like one memorized script.
        return score + random.uniform(-10, 10 + chaos * 80)

    def personality_piece_bonus(self, move, piece, profile):
        score = 0
        style = profile.get("style")
        aggression = profile.get("aggression", 0.55)
        chaos = profile.get("chaos", 0.4)

        center = {chess.D4, chess.E4, chess.D5, chess.E5}
        extended_center = center | {
            chess.C3, chess.D3, chess.E3, chess.F3,
            chess.C6, chess.D6, chess.E6, chess.F6,
        }

        if move.to_square in center:
            score += 26
        elif move.to_square in extended_center:
            score += 11

        if self.board.gives_check(move):
            score += 45 + aggression * 75

        if self.board.is_castling(move):
            score += 34

        if piece.piece_type in {chess.KNIGHT, chess.BISHOP}:
            home_rank = 0 if piece.color == chess.WHITE else 7
            if chess.square_rank(move.from_square) == home_rank:
                score += 18

        if piece.piece_type == chess.QUEEN and len(self.board.move_stack) < 8:
            score -= 22 if style != "chaos" else 8

        if piece.piece_type == chess.KING and not self.board.is_castling(move):
            score -= 30 if style != "chaos" else 5

        if style == "chaos":
            if piece.piece_type in {chess.KNIGHT, chess.QUEEN, chess.KING}:
                score += 16
            if self.board.is_capture(move) or self.board.gives_check(move):
                score += 55

        if style == "greedy" and self.board.is_capture(move):
            score += 120

        if style == "attacker":
            if self.board.gives_check(move):
                score += 110
            if move.to_square in center:
                score += 20
            if piece.piece_type == chess.PAWN:
                score += 8

        if style == "coach":
            if piece.piece_type == chess.QUEEN and len(self.board.move_stack) < 10:
                score -= 30
            if self.board.is_capture(move) or self.board.gives_check(move):
                score += 35

        if style == "endboss":
            if move.to_square in center:
                score += 22
            if self.board.is_capture(move):
                score += 18
            score -= chaos * 10

        return score

    def material_score(self, color):
        score = 0
        for piece in self.board.piece_map().values():
            value = PIECE_VALUES[piece.piece_type]
            score += value if piece.color == color else -value
        return score

    # ── Board helpers used by ThressGame mutators ────────────────────────────

    def occupied_squares(self):
        return [square for square in chess.SQUARES if self.board.piece_at(square)]

    def empty_squares(self):
        return [square for square in chess.SQUARES if self.board.piece_at(square) is None]

    def random_empty_square(self):
        empties = self.empty_squares()
        return random.choice(empties) if empties else None

    def sanitize_after_mutation(self):
        self.board.castling_rights = self.board.clean_castling_rights()
        self.board.ep_square = None

    # ── Fog of War stubs (overridden by FogGame) ─────────────────────────────

    def visible_squares(self, viewer_index):
        return None

    def hidden_squares_payload(self, viewer_index):
        return []

    # ── Payload builders ─────────────────────────────────────────────────────

    def board_payload(self, viewer_index=None):
        pieces = {}
        visible = self.visible_squares(viewer_index)
        for square, piece in self.board.piece_map().items():
            if visible is not None and square not in visible:
                continue
            square_name = chess.square_name(square)
            pieces[square_name] = {
                "symbol": piece.symbol(),
                "color": "white" if piece.color == chess.WHITE else "black",
                "type": chess.piece_name(piece.piece_type),
            }
        return pieces

    def legal_moves_payload(self, viewer_index=None):
        moves = {}
        viewer_color = self.player_color(viewer_index) if viewer_index in {0, 1} else None
        for move in self.board.legal_moves:
            piece = self.board.piece_at(move.from_square)
            if viewer_color is not None and (not piece or piece.color != viewer_color):
                continue
            if not self._is_legal_move_visible(move, piece):
                continue
            from_name = chess.square_name(move.from_square)
            moves.setdefault(from_name, []).append({
                "to": chess.square_name(move.to_square),
                "promotion": chess.piece_symbol(move.promotion) if move.promotion else None,
            })
        return moves

    def _is_legal_move_visible(self, move, piece):
        return True

    def variant_payload(self):
        return {
            "id": self.variant_id,
            "label": self.variant["label"],
            "description": self.variant["description"],
        }

    def mutator_history_payload(self):
        return []

    def snapshot(self, viewer_index=None):
        outcome = self.board.outcome(claim_draw=True)
        return {
            "kind": "chess",
            "gameState": self.game_state,
            "message": self.message,
            "board": self.board_payload(viewer_index),
            "hiddenSquares": self.hidden_squares_payload(viewer_index),
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "legalMoves": self.legal_moves_payload(viewer_index) if self.game_state == "playing" else {},
            "lastMove": self.last_move,
            "moveHistory": self.move_history,
            "moveHistorySan": self.move_history_san,
            "mutatorHistory": self.mutator_history_payload(),
            "isCheck": self.board.is_check(),
            "isGameOver": self.game_state == "gameover",
            "result": self.board.result(claim_draw=True) if outcome else None,
            "termination": str(outcome.termination.name).lower() if outcome else None,
            "variant": self.variant_payload(),
            "clock": self.clock_snapshot(),
        }
