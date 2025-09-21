from flask_socketio import emit, join_room
from game.state_machine import MafiaGame, GameState
from routes.game_routes import games  # in-memory game store
from flask import request

# socketio will be injected from app.py
socketio = None  

def init_socketio(sio):
    global socketio
    socketio = sio

    # ------------------- Join Game -------------------
    @socketio.on("join")
    def handle_join(data):
        game_id = data.get("game_id")
        player_id = data.get("player_id")

        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return

        join_room(game_id)
        game = games[game_id]

        # Broadcast state to everyone in the room
        emit("state_update", {
            "msg": f"{player_id} joined game {game_id}",
            "players": game._serializable_players(),
            "state": game.get_state()
        }, room=game_id)

    # ------------------- Update Settings -------------------
    @socketio.on("update_settings")
    def handle_update_settings(data):
        game_id = data.get("game_id")
        host_id = data.get("host_id")
        new_settings = data.get("settings")

        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return

        game = games[game_id]
        try:
            updated = game.update_settings(host_id, new_settings)
            emit("settings_updated", {"settings": updated}, room=game_id)
        except Exception as e:
            emit("error", {"msg": str(e)})

    # ------------------- Start Game -------------------
    @socketio.on("start_game")
    def handle_start_game(data):
        game_id = data.get("game_id")
        host_id = data.get("host_id")

        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return

        game = games[game_id]

        if host_id != game.host_id:
            emit("error", {"msg": "Only host can start"}, room=request.sid)
            return

        try:
            players_roles = game.assign_roles()
            emit("role_assigned", {"players": players_roles}, room=game_id)

            # Immediately start night 1
            game.start_night()
            emit("game_started", {"game_state": game.get_state()}, room=game_id)
        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)

    # ------------------- Player Night Action -------------------
    @socketio.on("player_action")
    def handle_action(data):
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        action = data.get("action")  # {"type": "...", "target": "<player_id>"}

        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return

        game = games[game_id]

        try:
            game.record_action(player_id, action)
            emit("state_update", {
                "msg": f"Action recorded: {action}",
                "state": game.get_state()
            }, room=game_id)

            # If all special-role players have acted, resolve the night automatically
            if game.all_night_actions_received():
                result = game.resolve_night()
                emit("night_resolved", {
                    "result": result,
                    "game_state": game.get_state()
                }, room=game_id)
        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)
