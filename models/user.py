from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vehicule import Vehicule


class User:
    name: str
    
    def __init__(self, name: str) -> None:
        self.name = name
