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
        game_id = data["game_id"]
        player_id = data["player_id"]

        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return

        join_room(game_id)
        game = games[game_id]

        # Broadcast a state update to everyone in the room
        emit("state_update", {
            "msg": f"{player_id} joined game {game_id}",
            "players": list(game.players.values()),
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