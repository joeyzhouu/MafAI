from flask import Blueprint, request, jsonify
from game.state_machine import MafiaGame
from game.model import Player

game_bp = Blueprint("game", __name__)
games = {}   # in-memory game store {game_id: MafiaGame}


@game_bp.route("/create", methods=["POST"])
def create_game():
    data = request.json or {}
    host_name = data.get("host_name")
    theme = data.get("theme")

    if not host_name:
        return jsonify({"error": "host_name is required"}), 400

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
    data = request.json or {}
    game_id = data.get("game_id")
    name = data.get("name")

    if not game_id or not name:
        return jsonify({"error": "game_id and name are required"}), 400

    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    try:
        new_player = Player(name=name)
        game.add_player(new_player)
        return jsonify({
            "status": "ok",
            "player_id": new_player.player_id,
            "game_state": game.get_state()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@game_bp.route("/state/<game_id>", methods=["GET"])
def get_state(game_id):
    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(game.get_state())

@game_bp.route("/settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    game_id = data.get("game_id")
    host_id = data.get("host_id")
    new_settings = data.get("settings", {})

    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    try:
        updated = game.update_settings(host_id, new_settings)
        return jsonify({"status": "ok", "settings": updated})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@game_bp.route("/start", methods=["POST"])
def start_game():
    data = request.json or {}
    game_id = data.get("game_id")
    host_id = data.get("host_id")

    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    if host_id != game.host_id:
        return jsonify({"error": "Only host can start"}), 403

    try:
        game.start_game()
        return jsonify({"status": "started", "game_state": game.get_state()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ------------------- Player Night Action -------------------
@game_bp.route("/action", methods=["POST"])
def player_action():
    data = request.json or {}
    game_id = data.get("game_id")
    player_id = data.get("player_id")
    action = data.get("action")  # {"type": "kill", "target": "<pid>"}

    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # Only allow alive players to perform night actions
    player_info = game.players.get(player_id)
    if not player_info or not player_info["alive"]:
        return jsonify({"error": "Only alive players can perform night actions"}), 403

    try:
        game.record_action(player_id, action)

        if game.all_night_actions_received():
            result = game.resolve_night()
            return jsonify({"status": "resolved", "result": result, "game_state": game.get_state()})

        return jsonify({"status": "recorded", "game_state": game.get_state()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@game_bp.route("/day/<game_id>", methods=["GET"])
def start_day(game_id):
    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404
    try:
        result = game.start_day()
        return jsonify({"status": "ok", "result": result, "game_state": game.get_state()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@game_bp.route("/vote", methods=["POST"])
def vote():
    data = request.json or {}
    game_id = data.get("game_id")
    voter_id = data.get("voter_id")
    target_id = data.get("target_id")  # can be "skip"

    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # Only alive players can vote
    voter_info = game.players.get(voter_id)
    if not voter_info or not voter_info["alive"]:
        return jsonify({"error": "Only alive players can vote"}), 403

    try:
        game.record_vote(voter_id, target_id)
        return jsonify({"status": "recorded", "game_state": game.get_state()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@game_bp.route("/resolve_votes", methods=["POST"])
def resolve_votes():
    data = request.json or {}
    game_id = data.get("game_id")

    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    try:
        result = game.resolve_votes()
        return jsonify({"status": "resolved", "result": result, "game_state": game.get_state()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
