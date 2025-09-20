from flask import Blueprint, request, jsonify
from game.state_machine import MafiaGame
from game.model import Player

game_bp = Blueprint("game", __name__)
games = {}   # in-memory game store {game_id: MafiaGame}

@game_bp.route("/create", methods=["POST"])
def create_game():
    data = request.json
    host_name = data.get("host_name")
    theme = data.get("theme")

    # Create host as a Player
    host_player = Player(name=host_name)

    game = MafiaGame(host_player, theme)
    games[game.id] = game

    return jsonify({
        "game_id": game.id,
        "host_id": host_player.player_id,
        "player_id": host_player.player_id, 
        "game_state": game.get_state()
    })

@game_bp.route("/join", methods=["POST"])
def join_game():
    data = request.json
    game_id = data["game_id"]
    name = data["name"]
    if game_id in games:
        game = games[game_id]
        new_player = Player(name=name)
        game.add_player(new_player)
        return jsonify({"status": "ok", "player_id": new_player.player_id, "game_state": game.get_state()})
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
