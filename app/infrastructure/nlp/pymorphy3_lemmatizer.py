import re
from typing import Iterable

import pymorphy3

from app.domain.services.lemmatizer_port import ILemmatizer

_TOKEN_RE = re.compile(r"[а-яёА-ЯЁa-zA-Z]+", re.UNICODE)


class Pymorphy3Lemmatizer(ILemmatizer):
    """Adapter: pymorphy3 для русскоязычных текстов."""

    def __init__(self) -> None:
        self._morph = pymorphy3.MorphAnalyzer()

    def lemmatize(self, word: str) -> str:
        parsed = self._morph.parse(word.lower())
        if not parsed:
            return word.lower()
        return parsed[0].normal_form

    def tokenize(self, text: str) -> Iterable[str]:
        return _TOKEN_RE.findall(text)
