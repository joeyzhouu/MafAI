from flask_socketio import emit, join_room
from flask import request
from game.state_machine import MafiaGame, GameState
from routes.game_routes import games  # in-memory game store

# socketio will be injected from app.py
socketio = None
player_sessions = {}
players_continued = {}  # {game_id: set(player_id)}

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

    # ------------------- Player Ready Status -------------------
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

            print(f"Generating background story for game {game_id}...") 

            # Run state machine start_game (generates background story)
            result = game.start_game()
            story = result["background_story"]

            print(f"Background story generated: {story[:10]}...")

            # Switch to night phase
            game.start_night()

            # Broadcast game started + background story + state
            emit("game_started", {
                "background_story": story,
                "game_state": game.get_state()
            }, room=game_id)

        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)

    # ------------------- Player Continue Logic -------------------
    @socketio.on("player_continue")
    def handle_player_continue(data):
        game_id = data.get("game_id")
        player_id = data.get("player_id")

        if game_id not in games:
            emit("error", {"msg": "Game not found"})
            return

        if game_id not in players_continued:
            players_continued[game_id] = set()

        players_continued[game_id].add(player_id)

        # Notify everyone of updated continue status
        emit("player_continue_update", {
            "player_id": player_id,
            "players_continued": list(players_continued[game_id])
        }, room=game_id)

        # Check if all alive players have continued
        game = games[game_id]
        alive_player_ids = set(pid for pid, info in game.players.items() if info["alive"])
        
        if players_continued[game_id] >= alive_player_ids:
            current_state = game.state
            print(f"All players continued. Current game state: {current_state}")
            
            # Determine next phase based on current state
            if current_state == GameState.NIGHT:
                emit("all_players_continued", {
                    "next_phase": "night"
                }, room=game_id)
            elif current_state == GameState.DAY:
                emit("all_players_continued", {
                    "next_phase": "discussion"
                }, room=game_id)
            else:
                # Fallback
                emit("all_players_continued", {
                    "next_phase": "night"
                }, room=game_id)
            
            # Reset for next continue phase
            players_continued[game_id] = set()

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
                "msg": f"Action recorded for {player_id}",
                "state": game.get_state()
            }, room=game_id)

            # Check if all required night actions received
            if game.all_night_actions_received():
                print(f"All night actions received for game {game_id}, resolving...")
                
                # Resolve night phase
                result = game.resolve_night()
                emit("night_resolved", {
                    "result": result,
                    "game_state": game.get_state()
                }, room=game_id)

                # Optionally start day immediately

                print(f"Generating daytime story for game {game_id}...") 
                day_info = game.start_day()
                print(f"Background story generated: {day_info["story"][:10]}...")
                emit("day_started", {
                    "story": day_info["story"],
                    "game_state": game.get_state()
                }, room=game_id)
                
        except Exception as e:
            emit("error", {"msg": str(e)}, room=request.sid)

    # ------------------- Player Voting -------------------
    @socketio.on("cast_vote")
    def handle_cast_vote(data):
        game_id = data.get("game_id")
        voter_id = data.get("voter_id")
        target_id = data.get("target_id")

        if game_id not in games:
            emit("error", {"msg": "Game not found"}, room=request.sid)
            return

        game = games[game_id]

        if voter_id not in game.players or not game.players[voter_id]["alive"]:
            emit("error", {"msg": "Invalid or dead voter"}, room=request.sid)
            return

        if game.state != GameState.DISCUSSION:
            emit("error", {"msg": "Not in voting phase"}, room=request.sid)
            return

        # Record vote
        game.votes[voter_id] = target_id
        emit("vote_recorded", {"voter": voter_id, "target": target_id}, room=game_id)

        # ✅ Check if all alive players have voted
        if len(game.votes) == len(game.alive_players()):
            result = game.resolve_votes()
            socketio.emit(
                "votes_resolved",
                {
                    "result": result,
                    "round_number": game.round_number,
                    "story": result.get("story"),
                },
                room=game_id,
            )


    # ------------------- Manual Vote Resolution (fallback) -------------------
    @socketio.on("resolve_votes")
    def handle_resolve_votes(data):
        game_id = data.get("game_id")

        game = games.get(game_id)
        if not game:
            emit("error", {"msg": "Game not found"})
            return

        try:
            result = game.resolve_votes()
            emit("votes_resolved", {
                "result": result,
                "game_state": game.get_state()
            }, room=game_id)
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
                    # Clean up continue tracking
                    if game_id in players_continued:
                        del players_continued[game_id]
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