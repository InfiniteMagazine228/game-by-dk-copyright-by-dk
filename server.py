import os
import json
from aiohttp import web, WSMsgType

routes = web.RouteTableDef()

players = {}


@routes.get("/")
async def index(request):
    return web.FileResponse("./static/index.html")


@routes.get("/ws")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player_id = str(id(ws))

    players[player_id] = {
        "x": 80,
        "y": 300,
        "color": "#2f80ed"
    }

    request.app["sockets"][player_id] = ws

    await broadcast(request.app)

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            try:
                data = json.loads(msg.data)

                if data.get("type") == "move":
                    if player_id in players:
                        players[player_id]["x"] = data.get("x", 80)
                        players[player_id]["y"] = data.get("y", 300)

                    await broadcast(request.app)

            except Exception:
                pass

        elif msg.type == WSMsgType.ERROR:
            break

    players.pop(player_id, None)
    request.app["sockets"].pop(player_id, None)

    await broadcast(request.app)

    return ws


async def broadcast(app):
    packet = json.dumps({
        "type": "players",
        "players": players
    })

    dead = []

    for player_id, socket in app["sockets"].items():
        if socket.closed:
            dead.append(player_id)
            continue

        try:
            await socket.send_str(packet)
        except Exception:
            dead.append(player_id)

    for player_id in dead:
        app["sockets"].pop(player_id, None)
        players.pop(player_id, None)


async def on_startup(app):
    app["sockets"] = {}


app = web.Application()
app.add_routes(routes)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
