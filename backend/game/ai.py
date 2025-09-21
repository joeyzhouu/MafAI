import warnings
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
my_api_key = os.getenv('GEMINI_API_KEY')

if not my_api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

genai.configure(api_key=my_api_key)
model = genai.GenerativeModel("gemini-2.5-flash")


def generate_background_story(theme: str):
    """
    Generate a background story for the Mafia game based on the theme.

    Args:
        theme: Theme of the game
    """
    prompt = f"""Given the {theme}:
                - briefly and explicitly welcome the players
                - write a background narrative for a Mafia game
                - keep it engaging, but don't use too many adjectives or any complicated vocabulary
                - briefly and explicitly wish the players good luck
                - keep it concise (2-3 sentences)"""
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9
        }
    )
    return response.text.strip()


def generate_mafia_story(night_actions: dict, special_actions: dict, round_number: int, theme: str = None):
    """
    Generate a story for the Mafia game based on night actions and special events.

    Args:
        night_actions: Dict of player_name -> {"role": str, "action": str}
        special_actions: Dict containing lists of player names for 'deaths' and 'revivals'.
        round_number: Current round number
        theme: Optional theme for story flavor

    Returns:
        str: Generated story text
    """
    theme_text = f"Theme: {theme}.\n" if theme else ""

    # Build a readable description of night actions
    actions_text = ""
    for player, act in night_actions.items():
        role = act.get("role", "unknown")
        action = act.get("action", "")
        actions_text += f"- {role} {player} performed {action}\n"

    # Include deaths and revivals
    deaths = special_actions.get("deaths", [])
    revivals = special_actions.get("revivals", [])
    special_text = ""
    if deaths:
        special_text += "Deaths occurred: " + ", ".join(deaths) + ".\n"
    if revivals:
        special_text += "Players revived: " + ", ".join(revivals) + ".\n"

    prompt = f"""
        You are a creative storyteller narrating a Mafia game.
        {theme_text}
        It was Night {round_number}. Players performed the following actions:
        {actions_text}
        {special_text}
        Write a narrative that:
        - Story should not reveal the exact roles and names of the players when describing actions
        - The story should not hint at the roles of players who are still alive
        - The only players mentioned by name should be those who died or were revived
        - If there was a revival, the doctor's action should not be mentioned. Just briefly mention the revival in the story.
        - Summarizes the night in an engaging way without complicating the story 
        - If there are deaths, describe them and include a hint about what the murderer was doing during their nighttime actions, but add one or two subtle random twists to mislead players (i.e. hint at another player's action)
        - Leaves hints for alive players to discuss during the day
        - Mentions deaths if any, but keeps suspense
        - Don't use overly complicated vocabulary or too much adjectives, but keep it suspenseful
        Return the story in one paragraph maximum suitable for all players.
    """

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9
        }
    )

    return response.text.strip()


# if __name__ == "__main__":
#     night_actions = {
#         "Alice": {"role": "villager", "action": "Visited the well alone."},
#         "Bob": {"role": "detective", "action": "Searched the forest for clues."},
#         "Charlie": {"role": "doctor", "action": "Stayed in his house to protect villagers."},
#         "David": {"role": "mafia", "action": "Worked the bakery night shift."},
#         "Eve": {"role": "villager", "action": "Took a walk at the beach to calm anxiety."}
#     }
#     special_actions = {
#         "deaths": ["David killed Eve"],
#         "revivals": ["Charlie revived Eve"]
#     }
#     round_number = 2
#     theme = "Haunted Village: Mass murderer manipulating and killing innocent villagers..."

#     story = generate_background_story(theme)

#     print("Generated story:\n", story)
