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
