import uuid

class Player:
    def __init__(self, name):
        """Initialize a player object."""
        self.player_id = str(uuid.uuid4())[:8]
        self.name = name
        self.role = None
        self.is_alive = True
        self.ready = False

    def get_info(self):
        """Return player information."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "role": self.role,
            "is_alive": self.is_alive,
            "ready": self.ready
        }

    def assign_role(self, role):
        """Assign a role to the player."""
        self.role = role

    def eliminate(self):
        """Eliminate the player from the game."""
        self.is_alive = False

    def revive(self):
        """Revive the player."""
        self.is_alive = True

    def set_ready(self, ready=True):
        self.ready = ready
   