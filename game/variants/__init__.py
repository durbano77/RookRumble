from .atomic import AtomicGame
from .blindfolded import BlindfoldedGame
from .classic import ClassicGame
from .dice import DiceGame
from .fog import FogGame
from .king_hill import KingHillGame
from .no_check import NoCheckGame
from .three_check import ThreeCheckGame
from .thress import ThressGame
from .total_annihilation import TotalAnnihilationGame

VARIANT_CLASSES = {
    "classic": ClassicGame,
    "three_check": ThreeCheckGame,
    "king_hill": KingHillGame,
    "atomic": AtomicGame,
    "dice": DiceGame,
    "fog": FogGame,
    "thress": ThressGame,
    "blindfolded": BlindfoldedGame,
    "no_check": NoCheckGame,
    "total_annihilation": TotalAnnihilationGame,
}
