from enum import Enum, auto
import uuid
import random, time
from ai import generate_mafia_story, generate_background_story

THEMES = [
    "Space Crew vs. Aliens: A spaceship floating in deep space...",
    "Medieval Kingdom: Nobles secretly plotting to overthrow the king...",
    "Wild West: Bandits hiding among locals in a frontier town...",
    "Haunted Village: Mass murderers manipulating and killing innocent villagers...",
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

    # ------------------- Game Setup & Player Management -------------------

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
                "alive": info["alive"],
                "ready": info["player_obj"].ready
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
        if self.state != GameState.WAITING:
            raise Exception("Game already started")

        self.state = GameState.NIGHT
        self.round = 1

        # Generate intro narrative
        background = generate_background_story(self.theme)
        self.story_log.append({"event": "Game Start", "story": background})

        return {"background_story": background}


    def alive_players(self):
        """Returns a list of player IDs who are currently alive."""
        return [pid for pid, info in self.players.items() if info["alive"]]

    def alive_by_role(self, role):
        """Returns a list of alive player IDs with the specified role."""
        return [pid for pid, info in self.players.items() if info["alive"] and info["role"] == role]
    
    # ------------------- Night Phase -------------------

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

        self.pending_actions[player_id] = {
                                            "type": atype,
                                            "target": target,
                                            "activity": action.get("activity", "")
                                        }

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

        winners = self.check_game_over()[1]
        if winners:
            self.end_game(winners)

        return {"mafia_target": mafia_target, "saved": saved, "detective_results": self.detective_results}
    
    # ------------------- Day Phase -------------------

    def start_day(self):
        if self.state != GameState.DAY:
            raise Exception("Not in DAY phase")

        # Build night actions dict
        night_actions = {}
        for pid, act in self.pending_actions.items():
            player = self.players[pid]
            night_actions[player["name"]] = {
                "role": player["role"],
                "action": act.get("activity", "")
            }

        # Build special actions
        special_actions = {"deaths": [], "revivals": []}
        for pid, info in self.players.items():
            if not info["alive"] and "eliminated_in_round" in info and info["eliminated_in_round"] == self.round:
                special_actions["deaths"].append(info["name"])
            # (If you add revival logic later, populate special_actions["revivals"])

        # Generate story
        story_text = generate_mafia_story(night_actions, special_actions, self.round, self.theme)

        # Save story in log
        self.story_log.append({
            "event": f"Day {self.round} AI story",
            "story": story_text
        })

        self.state = GameState.DISCUSSION
        self.pending_actions = {}

        return {"story": story_text, "night_activities": night_actions}


    def record_vote(self, voter_id, target_id):
        """Records a vote. Only alive players can vote."""
        if self.state != GameState.DISCUSSION:
            raise Exception("Not in DISCUSSION phase")
        if voter_id not in self.players or not self.players[voter_id]["alive"]:
            raise Exception("Only alive players can vote")

        if not hasattr(self, "votes"):
            self.votes = {}

        self.votes[voter_id] = target_id
        return True

    def all_votes_received(self):
        """Check if all alive players have voted."""
        alive_players = [p for p in self.players.values() if p.alive]
        return len(self.votes) == len(alive_players)

    def resolve_votes(self):
        """Counts votes and eliminates player if needed."""
        if self.state != GameState.DISCUSSION:
            raise Exception("Not in DISCUSSION phase")
        if not hasattr(self, "votes"):
            return {"message": "No votes cast"}

        vote_counts = {}
        for v in self.votes.values():
            vote_counts[v] = vote_counts.get(v, 0) + 1

        num_alive = len(self.alive_players())
        majority = num_alive // 2 + 1

        # Determine result
        eliminated = None
        if "skip" in vote_counts and vote_counts["skip"] >= majority:
            outcome = "skip_majority"
        else:
            # Get player with most votes
            top_votes = [pid for pid, cnt in vote_counts.items() if cnt == max(vote_counts.values())]
            eliminated = random.choice(top_votes)
            self.eliminate_player(eliminated)
            outcome = "player_eliminated"

        # Clear votes for next round
        self.votes = {}
        self.state = GameState.NIGHT  # back to night

        # Check if game over
        winners = self.is_game_over()
        if winners:
            self.end_game(winners)

        return {
            "outcome": outcome,
            "eliminated": eliminated,
            "vote_counts": vote_counts,
            "game_over": self.state == GameState.END
        }


    def eliminate_player(self, player_id):
        """Eliminates a player from the game (used for voting and killer)."""
        if player_id in self.players:
            self.players[player_id]["player_obj"].eliminate()
            self.players[player_id]["alive"] = False
            self.story_log.append({"event": f"Player Eliminated: {self.players[player_id]['name']}", "player_id": player_id})
    
    def check_game_over(self):
        """Return (game_over: bool, winner: str|None)."""
        alive_mafia = sum(1 for p in self.players.values() if p.alive and p.role == "mafia")
        alive_town = sum(1 for p in self.players.values() if p.alive and p.role != "mafia")

        if alive_mafia == 0:
            return True, "town"
        elif alive_mafia >= alive_town:
            return True, "mafia"
        return False, None

    def end_game(self):
        """Ends the game and records the winners."""
        game_over, winners = self.check_game_over()
        if not game_over:
            raise Exception("Game is not over yet")
        else:
            self.state = GameState.END
            mafias = [p["name"] for p in self.players.values() if p["role"] == "mafia"]
            docter = [p["name"] for p in self.players.values() if p["role"] == "doctor"]
            detective = [p["name"] for p in self.players.values() if p["role"] == "detective"]
            self.story_log.append({"event": "Game Over", "winners": winners, "mafia(s)": mafias, "doctor": docter, "detective": detective})
