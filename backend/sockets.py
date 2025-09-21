from flask_socketio import emit, join_room
from flask import request
from game.state_machine import MafiaGame, GameState
from routes.game_routes import games  # in-memory game store

# socketio will be injected from app.py
socketio = None
player_sessions = {}

def init_socketio(sio):
    global socketio
    socketio = sio

    # ------------------- Join Game -------------------
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

        player_sessions[request.sid] = {"player_id": player_id, "game_id": game_id}
        emit("state_update", {
            "msg": f"{player_id} joined game {game_id}",
            "players": [
                {**v, "player_id": k} for k, v in game._serializable_players().items()
            ],
            "state": game.get_state()
        }, room=game_id)

    # ------------------- Player Ready Status (Your feature) -------------------
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

        # Emit full updated player list to everyone
        emit("state_update", {
            "players": [
                {**v, "player_id": k} for k, v in game._serializable_players().items()
            ],
            "msg": f"{player_id} ready: {ready_status}"
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
            # Assign roles and notify all players
            players_roles = game.assign_roles()
            emit("role_assigned", {"players": players_roles}, room=game_id)

            # Run state machine start_game (generates background story)
            result = game.start_game()
            background = result.get("background_story")

            # Switch to night phase
            game.start_night()

            # Broadcast game started + background story + state
            emit("game_started", {
                "background_story": background,
                "game_state": game.get_state()
            }, room=game_id)

        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)

    # ------------------- Player Night Action -------------------
    @socketio.on("player_action")
    def handle_action(data):
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        action = data.get("action")  # {"type": "...", "target": "<pid>", "activity": "..."}

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

    # ------------------- Player Voting -------------------
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

    # ------------------- Disconnect Handling -------------------
    @socketio.on("disconnect")
    def handle_disconnect():
        session_info = player_sessions.get(request.sid)
        if session_info:
            # Auto-leave the player
            handle_leave({
                "game_id": session_info["game_id"],
                "player_id": session_info["player_id"]
            })
            del player_sessions[request.sid]
        
    @socketio.on("leave_game") 
    def handle_leave(data):
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        
        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return
            
        game = games[game_id]
        
        try:
            if game.remove_player(player_id):
                # If no players left, clean up the game
                if not game.players:
                    del games[game_id]
                    emit("game_ended", {"msg": "Game ended - no players remaining"}, room=game_id)
                    return
                
                # Notify remaining players
                emit("player_left", {
                    "player_id": player_id,
                    "players": [
                        {**v, "player_id": k} for k, v in game._serializable_players().items()
                    ],
                    "new_host_id": game.host_id,
                    "game_state": game.get_state()
                }, room=game_id)
                
        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)