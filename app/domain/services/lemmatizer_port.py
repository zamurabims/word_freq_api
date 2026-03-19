from abc import ABC, abstractmethod
from typing import Iterable


class ILemmatizer(ABC):
    """Port: нормализация словоформ к лемме."""

    @abstractmethod
    def lemmatize(self, word: str) -> str: ...

    @abstractmethod
    def tokenize(self, text: str) -> Iterable[str]: ...
