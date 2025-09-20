from enum import Enum, auto
import uuid
import random

THEMES = ["Space Crew vs. Aliens: A spaceship floating in deep space, some crew members are secretly aliens trying to sabotage the mission",
          "Medieval Kingdom: A kingdom where some nobles are secretly plotting to overthrow the king",
          "Whild West: A dusty frontier town where bandits hide among the locals, plotting to take over.",]

class GameState(Enum):
    LOBBY = auto()
    ROLE_ASSIGNMENT = auto()
    NIGHT = auto()
    DAY = auto()
    END = auto()

class MafiaGame:
    def __init__(self, host_player, theme=None):
        self.id = str(uuid.uuid4())[:6]   # short join code
        self.state = GameState.LOBBY
        self.host_id = host_player.get_info['player_id']  # track host’s player_id
        self.theme = theme
        self.players = {}   # {player_id: {"name": str, "role": str, "alive": bool}}
        self.story_log = []
        self.round = 0
        self.settings = {"mafia": 1, "doctor": 1, "detective": 1}

        self.add_player(host_player)

    def add_player(self, player):
        """Add a player to the game lobby."""
        if self.state != GameState.LOBBY:
            raise Exception("Game already started")

        info = player.get_info()
        self.players[info["player_id"]] = {
            "name": info["name"],
            "role": info["role"],
            "alive": info["is_alive"]
        }
    
    def get_lobby_players(self):
        """Return list of players in the lobby."""
        return [{"player_id": pid, "name": info["name"]} for pid, info in self.players.items()]
    
    def game_state(self):
        """Return current game state."""
        return {
            "id": self.id,
            "state": self.state.name,
            "host_id": self.host_id,
            "theme": self.theme,
            "players": self.players,
            "story_log": self.story_log,
            "round": self.round,
            "settings": self.settings
        }

    def assign_roles(self):
        # TODO: implement role assignment logic
        self.state = GameState.ROLE_ASSIGNMENT

    def eliminate_player(self, player_id):
        """Eliminate a player from the game."""
        if player_id in self.players:
            self.players[player_id]["player_obj"].eliminate()
            self.story_log.append({
                                    "event": f"Player Eliminated: {self.players[player_id]['name']}",
                                    "player_id": player_id
                                })

    
    def is_game_over(self):
        """Check win condition (simplified)."""
        alive = [p for p in self.players.values() if p["alive"]]
        mafia = [p for p in alive if p["role"] == "mafia"]
        villagers = [p for p in alive if p["role"] != "mafia"]

        if not mafia:
            return "villagers"
        if len(mafia) >= len(villagers):
            return "mafia"
        return None

    def start_night(self):
        """Transition to night phase."""
        self.state = GameState.NIGHT
        self.round += 1

    def start_day(self):
        """Transition to day phase."""
        self.state = GameState.DAY

    def end_game(self, winners):
        """End the game and declare winners."""
        self.state = GameState.END
        self.story_log.append({"event": "Game Over", "winners": winners})
