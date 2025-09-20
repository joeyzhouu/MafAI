from enum import Enum, auto
import uuid

class GameState(Enum):
    LOBBY = auto()
    ROLE_ASSIGNMENT = auto()
    NIGHT = auto()
    DAY = auto()
    END = auto()

class MafiaGame:
    def __init__(self, host_id, theme=None):
        self.id = str(uuid.uuid4())[:6]   # short join code
        self.state = GameState.LOBBY
        self.host_id = host_id
        self.theme = theme
        self.players = {}   # {player_id: {"name": str, "role": str, "alive": bool}}
        self.story_log = []
        self.round = 0
        self.settings = {"mafia": 1, "doctor": 1, "detective": 1}

    def add_player(self, player_id, name):
        if self.state != GameState.LOBBY:
            raise Exception("Game already started")
        self.players[player_id] = {"name": name, "role": None, "alive": True}

    def assign_roles(self):
        # TODO: implement role assignment logic
        self.state = GameState.ROLE_ASSIGNMENT

    def start_night(self):
        self.state = GameState.NIGHT
        self.round += 1

    def start_day(self):
        self.state = GameState.DAY

    def end_game(self, winners):
        self.state = GameState.END
        self.story_log.append({"event": "Game Over", "winners": winners})
