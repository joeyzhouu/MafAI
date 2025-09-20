from flask_socketio import emit, join_room
from game.state_machine import GameState

# socketio will be injected from app.py
socketio = None  

def init_socketio(sio):
    global socketio
    socketio = sio

    @socketio.on("join")
    def handle_join(data):
        game_id = data["game_id"]
        player_id = data["player_id"]
        join_room(game_id)
        emit("state_update", {"msg": f"{player_id} joined game {game_id}"}, room=game_id)

    @socketio.on("player_action")
    def handle_action(data):
        game_id = data["game_id"]
        action = data["action"]
        # TODO: update MafiaGame state here
        emit("state_update", {"msg": f"Action received: {action}"}, room=game_id)
