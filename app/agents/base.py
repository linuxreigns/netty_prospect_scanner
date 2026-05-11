from abc import ABC, abstractmethod

from .schemas import ProspectContext


class BaseAgent(ABC):
    name: str

    @abstractmethod
    def run(self, ctx: ProspectContext) -> ProspectContext:
        raise NotImplementedError
