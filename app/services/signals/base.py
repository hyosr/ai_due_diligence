from abc import ABC, abstractmethod

class BaseSignalExtractor(ABC):
    key: str
    weight: float

    @abstractmethod
    async def extract(self, company: dict, context: dict) -> dict:
        pass