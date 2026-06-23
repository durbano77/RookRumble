import asyncio
import random
import string

from .registry import BOT_DIFFICULTIES
from .room import Room

MAX_ROOMS = 1000


class GameServer:
    def __init__(self):
        self.rooms: dict[str, Room] = {}

    def create_room_code(self):
        while True:
            code = "".join(random.choice(string.digits) for _ in range(6))
            if code not in self.rooms:
                return code

    async def remove_from_room(self, ws):
        room = getattr(ws, "room", None)
        if room is None:
            return

        slot = room.get_slot(ws)
        if slot is not None:
            room.clients[slot] = None
        ws.room = None

        if room.human_connected_count() == 0:
            self.rooms.pop(room.code, None)
            return

        room.sync_presence()
        await room.broadcast_sync()

    async def create_room(self, ws):
        await self.remove_from_room(ws)

        if len(self.rooms) >= MAX_ROOMS:
            await ws.send_json({"type": "error", "message": "Server is at capacity. Try again later."})
            return

        code = self.create_room_code()
        room = Room(code)
        room.clients[0] = ws
        ws.room = room
        self.rooms[code] = room
        room.sync_presence()
        await room.broadcast_sync()

    async def create_bot_room(self, ws, difficulty):
        await self.remove_from_room(ws)

        if len(self.rooms) >= MAX_ROOMS:
            await ws.send_json({"type": "error", "message": "Server is at capacity. Try again later."})
            return

        if difficulty not in BOT_DIFFICULTIES:
            await ws.send_json({"type": "error", "message": "Choose a bot difficulty."})
            return

        code = self.create_room_code()
        room = Room(code)
        room.clients[0] = ws
        room.bot_difficulty = difficulty
        ws.room = room
        self.rooms[code] = room
        room.sync_presence()
        await room.broadcast_sync()

    async def join_room(self, ws, room_code):
        await self.remove_from_room(ws)

        room = self.rooms.get(room_code)
        if room is None:
            await ws.send_json({"type": "error", "message": "Room not found."})
            return

        slot = room.available_slot()
        if slot is None:
            await ws.send_json({"type": "error", "message": "Room is already full."})
            return

        room.clients[slot] = ws
        ws.room = room
        room.sync_presence()
        await room.broadcast_sync()

    async def play_bot_turns(self, room):
        active_game = room.active_game()
        if not room.bot_enabled() or active_game is None:
            return

        safety_turns = 0
        while (
            active_game.game_state == "playing"
            and active_game.player_index_for_turn() == 1
            and safety_turns < 4
        ):
            safety_turns += 1

            if active_game.pending_mutator:
                options = active_game.pending_mutator.get("options", [])
                if not options:
                    break
                active_game.choose_mutator(1, random.choice(options)["id"])
                await asyncio.sleep(0)
                continue

            if not active_game.bot_move(room.bot_difficulty):
                break
            await asyncio.sleep(0)

    async def handle_message(self, ws, payload):
        if not isinstance(payload, dict):
            await ws.send_json({"type": "error", "message": "Invalid message payload."})
            return

        message_type = payload.get("type")

        if message_type == "create_room":
            await self.create_room(ws)
            return

        if message_type == "create_bot_room":
            difficulty = str(payload.get("difficulty", "easy")).lower()
            await self.create_bot_room(ws, difficulty)
            return

        if message_type == "join_room":
            room_code = "".join(ch for ch in str(payload.get("roomCode", "")) if ch.isdigit())[:6]
            if not room_code:
                await ws.send_json({"type": "error", "message": "Enter a room code first."})
                return
            await self.join_room(ws, room_code)
            return

        room = getattr(ws, "room", None)
        if room is None:
            await ws.send_json({"type": "error", "message": "Join a room first."})
            return

        slot = room.get_slot(ws)
        is_host = slot == room.host_index
        active_game = room.active_game()

        if message_type == "leave_room":
            from .registry import lobby_sync_payload
            await self.remove_from_room(ws)
            await ws.send_json(lobby_sync_payload("You left the room. Create or join another one."))
            return

        if message_type == "select_game":
            if not is_host:
                await ws.send_json({"type": "error", "message": "Only the host can choose the variant."})
                return
            if active_game and active_game.game_state in {"playing", "paused"}:
                await ws.send_json({"type": "error", "message": "Finish or restart before changing variants."})
                return
            if not room.select_game(str(payload.get("game", ""))):
                await ws.send_json({"type": "error", "message": "Choose a chess variant."})
                return
            await room.broadcast_sync()
            return

        if message_type == "chess_move":
            if not active_game:
                await ws.send_json({"type": "error", "message": "Choose a variant first."})
                return
            ok, message = active_game.move(
                slot,
                str(payload.get("from", "")),
                str(payload.get("to", "")),
                payload.get("promotion"),
            )
            if not ok:
                await ws.send_json({"type": "error", "message": message})
            elif room.bot_enabled():
                await self.play_bot_turns(room)
            await room.broadcast_sync()
            return

        if message_type == "choose_mutator":
            if not active_game:
                await ws.send_json({"type": "error", "message": "Choose a variant first."})
                return
            ok, message = active_game.choose_mutator(slot, str(payload.get("mutatorId", "")))
            if not ok:
                await ws.send_json({"type": "error", "message": message})
            elif room.bot_enabled():
                await self.play_bot_turns(room)
            await room.broadcast_sync()
            return

        if message_type == "start_game":
            if not is_host:
                await ws.send_json({"type": "error", "message": "Only the host can start the game."})
                return
            if room.connected_count() < 2:
                await ws.send_json({"type": "error", "message": "A second player must join first."})
                return
            if active_game is None:
                await ws.send_json({"type": "error", "message": "Choose a variant first."})
                return
            active_game.start()
            await self.play_bot_turns(room)
            await room.broadcast_sync()
            return

        if message_type == "toggle_pause":
            if is_host and active_game:
                active_game.toggle_pause()
                await room.broadcast_sync()
            return

        if message_type == "restart_game":
            if not is_host or active_game is None:
                return
            if room.connected_count() < 2:
                active_game.set_waiting("Waiting for another player to join this room.")
            else:
                active_game.restart()
                await self.play_bot_turns(room)
            await room.broadcast_sync()
            return

        if message_type == "return_to_games":
            if not is_host or active_game is None:
                return
            active_game.return_to_ready()
            await room.broadcast_sync()
            return
