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
    players[player_id] = {"x": 80, "y": 300}

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            data = json.loads(msg.data)

            if data["type"] == "move":
                players[player_id] = {
                    "x": data["x"],
                    "y": data["y"]
                }

                packet = json.dumps({
                    "type": "players",
                    "players": players
                })

                for socket in list(request.app["sockets"]):
                    if not socket.closed:
                        await socket.send_str(packet)

        elif msg.type == WSMsgType.ERROR:
            break

    players.pop(player_id, None)
    request.app["sockets"].discard(ws)
    return ws

async def on_startup(app):
    app["sockets"] = set()

@web.middleware
async def socket_middleware(request, handler):
    response = await handler(request)
    if isinstance(response, web.WebSocketResponse):
        request.app["sockets"].add(response)
    return response

app = web.Application(middlewares=[socket_middleware])
app.add_routes(routes)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
