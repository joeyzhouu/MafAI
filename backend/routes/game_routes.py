from flask import Blueprint, request, jsonify
from game.state_machine import MafiaGame

game_bp = Blueprint("game", __name__)
games = {}   # in-memory game store {game_id: MafiaGame}

@game_bp.route("/create", methods=["POST"])
def create_game():
    data = request.json
    host_id = data.get("host_id")
    theme = data.get("theme")
    game = MafiaGame(host_id, theme)
    games[game.id] = game
    return jsonify({"game_id": game.id})

@game_bp.route("/join", methods=["POST"])
def join_game():
    data = request.json
    game_id = data["game_id"]
    player_id = data["player_id"]
    name = data["name"]
    if game_id in games:
        game = games[game_id]
        game.add_player(player_id, name)
        return jsonify({"status": "ok"})
    return jsonify({"error": "Game not found"}), 404


@game_bp.route("/state/<game_id>", methods=["GET"])
def get_state(game_id):
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    game = games[game_id]
    return jsonify(game.get_state())


@game_bp.route("/start", methods=["POST"])
def start_game():
    data = request.json
    game_id = data["game_id"]
    host_id = data["host_id"]

    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    
    game = games[game_id]

    if host_id != game.host_id:
        return jsonify({"error": "Only host can start"}), 403

    game.assign_roles()
    return jsonify({"status": "started", "game_state": game.get_state()})


@game_bp.route("/action", methods=["POST"])
def player_action():
    data = request.json
    game_id = data["game_id"]
    player_id = data["player_id"]
    action = data["action"]   # e.g. {"type": "kill", "target": "p123"}

    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    game = games[game_id]
    # TODO: update game state machine based on action
    return jsonify({"status": "received", "game_state": game.get_state()})
