class Player:
    def __init__(self, player_id, name):
        """Initialize a player object."""
        self.player_id = player_id
        self.name = name
        self.role = None
        self.is_alive = True

    def get_info(self):
        """Return player information."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "role": self.role,
            "is_alive": self.is_alive
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
    
   