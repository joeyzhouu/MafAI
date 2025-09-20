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

    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    
    game = games[game_id]
    player = Player(name)
    game.add_player(player)

    return jsonify({
        "status": "ok",
        "player_id": player.player_id,
        "game_state": game.get_state()
    })


