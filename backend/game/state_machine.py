from enum import Enum, auto
import uuid
import random

THEMES = [
    "Space Crew vs. Aliens: A spaceship floating in deep space...",
    "Medieval Kingdom: Nobles secretly plotting to overthrow the king...",
    "Wild West: Bandits hiding among locals in a frontier town...",
]


class GameState(Enum):
    LOBBY = auto()
    ROLE_ASSIGNMENT = auto()
    NIGHT = auto()
    DAY = auto()
    END = auto()


class MafiaGame:
    def __init__(self, host_player, theme=None):
        """Initializes a new Mafia game instance."""
        self.id = str(uuid.uuid4())[:6]
        self.state = GameState.LOBBY
        self.host_id = host_player.get_info()['player_id']
        self.theme = theme or random.choice(THEMES)

        self.players = {}
        self.story_log = []
        self.round = 0

        # default settings
        self.settings = {
            "theme": theme,
            "day_duration": 120,  # seconds
            "night_duration": 60,
            "roles": {}       
        }
        
        self.pending_actions = {}
        self.detective_results = {}

        self.add_player(host_player)

    def add_player(self, player):
        """Adds a player to the game lobby."""
        if self.state != GameState.LOBBY:
            raise Exception("Game already started")
        info = player.get_info()
        self.players[info["player_id"]] = {
            "player_obj": player,
            "name": info["name"],
            "role": info["role"],
            "alive": info["is_alive"]
        }

    def _serializable_players(self):
        """Returns a serializable version of players info for JSON responses."""
        return {
            pid: {
                "name": info["name"],
                "role": info["role"],    # frontend should hide role from non-owners
                "alive": info["alive"]
            }
            for pid, info in self.players.items()
        }

    def get_state(self):
        """Returns the current game state in a serializable format."""
        return {
            "id": self.id,
            "state": self.state.name,
            "host_id": self.host_id,
            "theme": self.theme,
            "players": self._serializable_players(),
            "story_log": self.story_log,
            "round": self.round,
            "settings": self.settings,
            "pending_actions_count": len(self.pending_actions),
            "detective_results": self.detective_results,
        }

    def update_settings(self, host_id, new_settings):
        """Updates game settings if requested by the host and valid."""
        if host_id != self.host_id:
            raise Exception("Only host can change settings")
        if self.state != GameState.LOBBY:
            raise Exception("Settings can only be changed in the lobby")

        mafia_count = new_settings.get("mafia", self.settings["mafia"])
        num_players = len(self.players)
        if mafia_count > 3:
            raise Exception("Max mafia is 3")
        if mafia_count == 2 and num_players < 5:
            raise Exception("Need at least 5 players for 2 mafia")
        if mafia_count == 3 and num_players < 7:
            raise Exception("Need at least 7 players for 3 mafia")
        
        if "theme" in new_settings:
            theme = new_settings["theme"]

        if "day_duration" in new_settings:
            if not isinstance(new_settings["day_duration"], int) or new_settings["day_duration"] <= 0:
                raise ValueError("day_duration must be a positive integer")
        
        if "night_duration" in new_settings:
            if not isinstance(new_settings["night_duration"], int) or new_settings["night_duration"] <= 0:
                raise ValueError("night_duration must be a positive integer")

        self.settings.update(new_settings)
        return self.settings

    def assign_roles(self):
        """Randomly assigns roles to players based on current settings."""
        pids = list(self.players.keys())
        if len(pids) < 4:
            raise Exception("Not enough players to start (min 4)")
        if self.state != GameState.LOBBY:
            raise Exception("Game already started")

        roles = []
        roles += ["mafia"] * self.settings["mafia"]
        roles += ["doctor"] * self.settings["doctor"]
        roles += ["detective"] * self.settings["detective"]
        roles += ["villager"] * (len(pids) - len(roles))

        random.shuffle(roles)

        for pid, role in zip(pids, roles):
            self.players[pid]["player_obj"].assign_role(role)
            self.players[pid]["role"] = role

        self.state = GameState.ROLE_ASSIGNMENT
        self.story_log.append({"event": "Roles assigned.", "roles_count": self.settings})
        return self._serializable_players()

    def start_game(self):
        """Starts the game if in lobby state and enough players."""
        self.assign_roles()
        self.start_night()

    def alive_players(self):
        """Returns a list of player IDs who are currently alive."""
        return [pid for pid, info in self.players.items() if info["alive"]]

    def alive_by_role(self, role):
        """Returns a list of alive player IDs with the specified role."""
        return [pid for pid, info in self.players.items() if info["alive"] and info["role"] == role]

    def start_night(self):
        """Transitions the game to the NIGHT phase."""
        self.state = GameState.NIGHT
        self.round += 1
        self.pending_actions = {}
        self.story_log.append({"event": f"Night {self.round} begins."})

    def record_action(self, player_id, action):
        """Records a player's night action."""
        if self.state != GameState.NIGHT:
            raise Exception("Not in NIGHT phase")
        if player_id not in self.players or not self.players[player_id]["alive"]:
            raise Exception("Player not found or not alive")

        role = self.players[player_id]["role"]
        atype = action.get("type")
        if role == "mafia" and atype != "kill":
            raise Exception("Mafia must send kill action")
        if role == "doctor" and atype != "save":
            raise Exception("Doctor must send save action")
        if role == "detective" and atype != "investigate":
            raise Exception("Detective must send investigate action")
        if role not in ("mafia", "doctor", "detective"):
            raise Exception("Role has no night action")

        target = action.get("target")
        if target not in self.players:
            raise Exception("Invalid action target")

        self.pending_actions[player_id] = {"type": atype, "target": target}
        return True

    def all_night_actions_received(self):
        """Checks if all required night actions have been received."""
        needed = {pid for role in ("mafia", "doctor", "detective") for pid in self.alive_by_role(role)}
        return needed.issubset(self.pending_actions.keys())

    def resolve_night(self):
        """Resolves all night actions and transitions to DAY phase."""
        if self.state != GameState.NIGHT:
            raise Exception("Can only resolve during NIGHT")

        mafia_votes = {}
        for pid, act in self.pending_actions.items():
            if act["type"] == "kill" and self.players[pid]["role"] == "mafia":
                tgt = act["target"]
                mafia_votes[tgt] = mafia_votes.get(tgt, 0) + 1

        mafia_target = None
        if mafia_votes:
            max_votes = max(mafia_votes.values())
            top_targets = [t for t, v in mafia_votes.items() if v == max_votes]
            mafia_target = random.choice(top_targets)

        doctor_targets = [act["target"] for pid, act in self.pending_actions.items()
                          if act["type"] == "save" and self.players[pid]["role"] == "doctor"]
        saved = mafia_target in doctor_targets if mafia_target else False

        for pid, act in self.pending_actions.items():
            if act["type"] == "investigate" and self.players[pid]["role"] == "detective":
                target = act["target"]
                self.detective_results[pid] = {"target": target, "role": self.players[target]["role"]}
                self.story_log.append({"event": f"Detective {self.players[pid]['name']} investigated {self.players[target]['name']}.",
                                       "result_for": pid})

        if mafia_target and not saved:
            self.players[mafia_target]["player_obj"].eliminate()
            self.players[mafia_target]["alive"] = False
            self.story_log.append({"event": f"{self.players[mafia_target]['name']} was killed during Night {self.round}.",
                                   "player_id": mafia_target})
        elif mafia_target:
            self.story_log.append({"event": f"{self.players[mafia_target]['name']} was targeted but saved during Night {self.round}."})

        self.pending_actions = {}
        self.state = GameState.DAY
        self.story_log.append({"event": f"Day {self.round} begins."})

        winners = self.is_game_over()
        if winners:
            self.end_game(winners)

        return {"mafia_target": mafia_target, "saved": saved, "detective_results": self.detective_results}

    def eliminate_player(self, player_id):
        """Eliminates a player from the game (used for voting and killer)."""
        if player_id in self.players:
            self.players[player_id]["player_obj"].eliminate()
            self.players[player_id]["alive"] = False
            self.story_log.append({"event": f"Player Eliminated: {self.players[player_id]['name']}", "player_id": player_id})

    def is_game_over(self):
        """Checks if the game is over and returns the winning side if so."""
        alive = [info for info in self.players.values() if info["alive"]]
        mafia = [p for p in alive if p["role"] == "mafia"]
        villagers = [p for p in alive if p["role"] != "mafia"]

        if not mafia:
            return "villagers"
        if len(mafia) >= len(villagers):
            return "mafia"
        return None

    def end_game(self, winners):
        """Ends the game and records the winners."""
        if self.is_game_over() is None:
            raise Exception("Game is not over yet")
        self.state = GameState.END
        self.story_log.append({"event": "Game Over", "winners": winners})
