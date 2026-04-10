from abc import ABC, abstractmethod


class BaseEntity(ABC):
    def __init__(self, id: str, position: tuple[float, float]) -> None:
        if len(position) != 2:
            raise ValueError(f"position must be a 2-tuple, got length {len(position)}")
        self.id = id
        self.position = position

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r}, position={self.position})"

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance entity state by dt seconds. Called once per simulation tick."""
        ...
