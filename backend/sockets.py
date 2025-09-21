from flask_socketio import emit, join_room
from flask import request
from game.state_machine import MafiaGame, GameState
from routes.game_routes import games  # in-memory game store

socketio = None  

def init_socketio(sio):
    global socketio
    socketio = sio

    @socketio.on("join")
    def handle_join(data):
        print("Join event received:", data)
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        print(f"{player_id} joining room {game_id}")

        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return

        join_room(game_id)
        print(f"Rooms: {socketio.server.manager.rooms}")
        game = games[game_id]

        emit("state_update", {
            "msg": f"{player_id} joined game {game_id}",
            "players": [
                {**v, "player_id": k} for k, v in game._serializable_players().items()
            ],
            "state": game.get_state()
        }, room=game_id)

    @socketio.on("player_ready")
    def handle_ready(data):
        print("Ready event received:", data)
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        ready_status = data.get("ready", True)

        game = games.get(game_id)
        if not game:
            emit("error", {"msg": "Game not found"})
            return

        player_info = game.players.get(player_id)
        if player_info:
            player_info["player_obj"].set_ready(ready_status)

        emit("state_update", {
            "players": [
                {**v, "player_id": k} for k, v in game._serializable_players().items()
            ],
            "msg": f"{player_id} ready: {ready_status}"
        }, room=game_id)

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

            game.start_night()
            emit("game_started", {"game_state": game.get_state()}, room=game_id)
        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)

    @socketio.on("player_action")
    def handle_action(data):
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        action = data.get("action")

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

            # Resolve night if all required actions received
            if game.all_night_actions_received():
                result = game.resolve_night()
                emit("night_resolved", {
                    "result": result,  # includes night_activities
                    "game_state": game.get_state()
                }, room=game_id)

                # Optionally start day immediately
                day_info = game.start_day()
                emit("day_started", {
                    "story": day_info["story"],
                    "game_state": game.get_state()
                }, room=game_id)
        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)

    @socketio.on("cast_vote")
    def handle_vote(data):
        game_id = data.get("game_id")
        voter_id = data.get("voter_id")
        target_id = data.get("target_id")  # can be "skip"

        game = games.get(game_id)
        if not game:
            emit("error", {"msg": "Game not found"})
            return

        try:
            game.record_vote(voter_id, target_id)
            emit("vote_recorded", {"voter": voter_id, "target": target_id}, room=game_id)
        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)

    @socketio.on("resolve_votes")
    def handle_resolve_votes(data):
        game_id = data.get("game_id")
        
        game = games.get(game_id)
        if not game:
            emit("error", {"msg": "Game not found"})
            return

        try:
            result = game.resolve_votes()
            emit("votes_resolved", {"result": result, "game_state": game.get_state()}, room=game_id)
        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)