from .variants import VARIANT_CLASSES


def create_game(variant_id: str):
    cls = VARIANT_CLASSES.get(variant_id)
    if cls is None:
        raise ValueError(f"Unknown variant: {variant_id}")
    return cls(variant_id)
