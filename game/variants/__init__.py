from .atomic import AtomicGame
from .classic import ClassicGame
from .dice import DiceGame
from .fog import FogGame
from .king_hill import KingHillGame
from .three_check import ThreeCheckGame
from .thress import ThressGame

VARIANT_CLASSES = {
    "classic": ClassicGame,
    "three_check": ThreeCheckGame,
    "king_hill": KingHillGame,
    "atomic": AtomicGame,
    "dice": DiceGame,
    "fog": FogGame,
    "thress": ThressGame,
}
