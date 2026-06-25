import asyncio
import json
import os
import socket
from pathlib import Path

from aiohttp import WSMsgType, web

from game.lobby import GameServer
from game.registry import lobby_sync_payload

ROOT = Path(__file__).parent
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
MAX_CONNECTIONS_PER_IP = 6
MAX_MSG_SIZE = 16_384
MSG_RATE_LIMIT = 10
MSG_RATE_WINDOW = 1.0

_ip_connections: dict[str, int] = {}
game_server = GameServer()
ADS_ENABLED = os.environ.get("ADS_ENABLED", "").lower() in ("1", "true", "yes")

# ── Security middleware ───────────────────────────────────────────────────────

_CSP = (
    "default-src 'self'; "
    "connect-src 'self' ws: wss:; "
    "img-src 'self' data:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)

# Relaxed CSP used when ADS_ENABLED=true — allows AdSense script and iframe domains.
_CSP_WITH_ADS = (
    "default-src 'self'; "
    "script-src 'self' https://pagead2.googlesyndication.com; "
    "connect-src 'self' ws: wss: https://googleads.g.doubleclick.net; "
    "frame-src https://googleads.g.doubleclick.net https://tpc.googlesyndication.com; "
    "img-src 'self' data: https://pagead2.googlesyndication.com https://googleads.g.doubleclick.net; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


@web.middleware
async def security_headers_middleware(request, handler):
    response = await handler(request)
    if response.prepared:
        return response
    response.headers["Content-Security-Policy"] = _CSP_WITH_ADS if ADS_ENABLED else _CSP
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


def _client_ip(request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote or "unknown"


# ── WebSocket handler ─────────────────────────────────────────────────────────

async def websocket_handler(request):
    client_ip = _client_ip(request)
    if _ip_connections.get(client_ip, 0) >= MAX_CONNECTIONS_PER_IP:
        raise web.HTTPTooManyRequests()

    _ip_connections[client_ip] = _ip_connections.get(client_ip, 0) + 1
    try:
        ws = web.WebSocketResponse(heartbeat=30, max_msg_size=MAX_MSG_SIZE)
        await ws.prepare(request)
        ws.room = None

        await ws.send_json(lobby_sync_payload())

        loop = asyncio.get_running_loop()
        msg_times: list[float] = []

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    now = loop.time()
                    msg_times.append(now)
                    cutoff = now - MSG_RATE_WINDOW
                    while msg_times and msg_times[0] < cutoff:
                        msg_times.pop(0)
                    if len(msg_times) > MSG_RATE_LIMIT:
                        await ws.close()
                        break

                    try:
                        payload = json.loads(msg.data)
                    except json.JSONDecodeError:
                        await ws.send_json({"type": "error", "message": "Invalid message payload."})
                        continue
                    await game_server.handle_message(ws, payload)
                elif msg.type == WSMsgType.ERROR:
                    break
        finally:
            await game_server.remove_from_room(ws)
    finally:
        count = _ip_connections.get(client_ip, 1) - 1
        if count <= 0:
            _ip_connections.pop(client_ip, None)
        else:
            _ip_connections[client_ip] = count

    return ws


# ── Static file handlers ──────────────────────────────────────────────────────

async def serve_file(name, content_type):
    return web.Response(text=(ROOT / name).read_text(), content_type=content_type)


async def index_handler(_request):
    return await serve_file("index.html", "text/html")


async def css_handler(_request):
    return await serve_file("styles.css", "text/css")


async def ads_txt_handler(_request):
    return await serve_file("ads.txt", "text/plain")


async def manifest_handler(_request):
    return await serve_file("manifest.json", "application/manifest+json")


async def sw_handler(_request):
    return web.Response(
        text=(ROOT / "sw.js").read_text(),
        content_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )


async def assetlinks_handler(_request):
    return await serve_file(".well-known/assetlinks.json", "application/json")


# ── App factory ───────────────────────────────────────────────────────────────

async def _on_startup(app):
    asyncio.create_task(game_server.run_clock_checks())


def make_app():
    app = web.Application(middlewares=[security_headers_middleware])
    app.on_startup.append(_on_startup)
    app.router.add_get("/", index_handler)
    app.router.add_get("/index.html", index_handler)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_get("/styles.css", css_handler)
    app.router.add_get("/ads.txt", ads_txt_handler)
    app.router.add_get("/manifest.json", manifest_handler)
    app.router.add_get("/sw.js", sw_handler)
    app.router.add_get("/.well-known/assetlinks.json", assetlinks_handler)
    app.router.add_static("/js", ROOT / "js")
    app.router.add_static("/css", ROOT / "css")
    app.router.add_static("/icons", ROOT / "icons")
    return app


# ── Entry point ───────────────────────────────────────────────────────────────

def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


if __name__ == "__main__":
    print(f"Local: http://localhost:{PORT}")
    print(f"LAN:   http://{local_ip()}:{PORT}")
    web.run_app(make_app(), host=HOST, port=PORT)
