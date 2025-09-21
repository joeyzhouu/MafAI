from flask_socketio import emit, join_room
from game.state_machine import MafiaGame, GameState
from routes.game_routes import games  # import the in-memory games dict

# socketio will be injected from app.py
socketio = None  

def init_socketio(sio):
    global socketio
    socketio = sio

    @socketio.on("join")
    def handle_join(data):
        print("Join event received:", data)
        game_id = data["game_id"]
        player_id = data["player_id"]
        print(f"{player_id} joining room {game_id}")

        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return

        join_room(game_id)
        print(f"Rooms: {socketio.server.manager.rooms}")
        game = games[game_id]

        # Broadcast a state update to everyone in the room
        emit("state_update", {
            "msg": f"{player_id} joined game {game_id}",
            "players": [
                {**v, "player_id": k} for k, v in game._serializable_players().items()
            ],
            "state": game.get_state()
        }, room=game_id)

    @socketio.on("player_action")
    def handle_action(data):
        game_id = data["game_id"]
        action = data["action"]

        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return

        # (Later: update MafiaGame logic here)
        emit("state_update", {
            "msg": f"Action received: {action}",
            "state": games[game_id].get_state()
        }, room=game_id)

    @socketio.on("player_ready")
    def handle_ready(data):
        print("Ready event received:", data)
        game_id = data["game_id"]
        player_id = data["player_id"]
        ready_status = data.get("ready", True)

        game = games.get(game_id)
        if not game:
            emit("error", {"msg": "Game not found"})
            return

        player_info = game.players.get(player_id)
        if player_info:
            player_info["player_obj"].set_ready(ready_status)

        # Emit full updated player list to everyone
        emit("state_update", {
            "players": [
                {**v, "player_id": k} for k, v in game._serializable_players().items()
            ],
            "msg": f"{player_id} ready: {ready_status}"
        }, room=game_id)