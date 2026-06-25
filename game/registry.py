VARIANTS = {
    "classic": {
        "label": "Classic",
        "description": "Regular chess, clean and familiar.",
    },
    "three_check": {
        "label": "Three-Check",
        "description": "Win by checking the enemy king three times.",
    },
    "king_hill": {
        "label": "King of the Hill",
        "description": "Win by marching your king into the center.",
    },
    "atomic": {
        "label": "Atomic",
        "description": "Captures explode nearby pieces.",
    },
    "dice": {
        "label": "Dice Chess",
        "description": "A die chooses which piece type must move.",
    },
    "fog": {
        "label": "Fog of War",
        "description": "You only see what your army can reach.",
    },
    "thress": {
        "label": "Thress",
        "description": "Every third move, pick one of three silly rule cards.",
    },
}

BOT_DIFFICULTIES = {
    "easy": {
        "label": "Easy Explorer",
        "description": "Mostly random legal moves while it learns what the pieces do.",
        "skill": 0.15,
        "chaos": 0.85,
        "aggression": 0.25,
        "greed": 0.35,
    },
    "medium": {
        "label": "Balanced Club Bot",
        "description": "A normal casual opponent that likes sensible tactics.",
        "skill": 0.55,
        "chaos": 0.38,
        "aggression": 0.55,
        "greed": 0.65,
    },
    "hard": {
        "label": "Hard Grinder",
        "description": "Low-chaos material play with sharper tactical priorities.",
        "skill": 0.82,
        "chaos": 0.14,
        "aggression": 0.58,
        "greed": 0.82,
    },
    "dougdoug": {
        "label": "Chaos Gremlin",
        "description": "Fearless, confused, and kind of hilarious. Treats every move as a speedrun.",
        "skill": 0.2,
        "chaos": 0.96,
        "aggression": 0.78,
        "greed": 0.55,
        "style": "chaos",
    },
    "greedy_goblin": {
        "label": "Greedy Goblin",
        "description": "If it can capture something, it probably will. Consequences are future goblin's problem.",
        "skill": 0.45,
        "chaos": 0.5,
        "aggression": 0.52,
        "greed": 1.0,
        "style": "greedy",
    },
    "coffeehouse": {
        "label": "Coffeehouse Attacker",
        "description": "Checks, threats, sacrifices, vibes. Hates quiet positions.",
        "skill": 0.58,
        "chaos": 0.48,
        "aggression": 1.0,
        "greed": 0.45,
        "style": "attacker",
    },
    "gotham": {
        "label": "The Coach",
        "description": "Tactical, instructive, and deeply offended by hanging pieces.",
        "skill": 0.72,
        "chaos": 0.22,
        "aggression": 0.72,
        "greed": 0.72,
        "style": "coach",
    },
    "magnus": {
        "label": "The Grandmaster",
        "description": "Calm, flexible, and annoyingly hard to trick.",
        "skill": 0.96,
        "chaos": 0.04,
        "aggression": 0.48,
        "greed": 0.68,
        "style": "endboss",
    },
}

THRESS_MUTATORS = [
    {
        "id": "march_pawns",
        "name": "March of the Pawnguins",
        "description": "Every pawn waddles one square forward if the square is empty.",
    },
    {
        "id": "the_rumbling",
        "name": "The Rumbling",
        "description": "Every pawn storms forward one square, deleting anything in front of it.",
    },
    {
        "id": "they_deserved_it",
        "name": "They Deserved It",
        "description": "One random non-king piece disappears.",
    },
    {
        "id": "going_woke",
        "name": "Going Woke",
        "description": "Pieces on files E-H slide one square toward the queenside if open.",
    },
    {
        "id": "horse_girl_summoning",
        "name": "Horse Girl Summoning",
        "description": "Your side gets a knight on a random empty square.",
    },
    {
        "id": "rook_market_crash",
        "name": "Rook Market Crash",
        "description": "All rooks turn into bishops. Diversification failed.",
    },
    {
        "id": "pawn_union",
        "name": "Pawn Union",
        "description": "Your pawns become queenside-to-kingside commuters and shift right if open.",
    },
    {
        "id": "minor_inconvenience",
        "name": "Minor Inconvenience",
        "description": "A random bishop or knight from either side becomes a pawn.",
    },
]


def variants_payload():
    return [
        {"id": key, "label": data["label"], "description": data["description"]}
        for key, data in VARIANTS.items()
    ]


def bots_payload():
    return [
        {"id": key, "label": data["label"], "description": data["description"]}
        for key, data in BOT_DIFFICULTIES.items()
    ]


def lobby_sync_payload(message="Create or join a room to begin."):
    return {
        "type": "sync",
        "roomCode": "",
        "selectedGame": "none",
        "availableGames": variants_payload(),
        "playerIndex": None,
        "isHost": False,
        "bot": {"enabled": False, "difficulty": None, "label": None, "color": None},
        "botDifficulties": bots_payload(),
        "players": [
            {"connected": False, "label": "White"},
            {"connected": False, "label": "Black"},
        ],
        "game": {
            "kind": "none",
            "gameState": "waiting",
            "message": message,
        },
    }
