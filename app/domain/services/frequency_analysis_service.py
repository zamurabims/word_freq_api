from typing import Dict, Iterator
from app.domain.entities.word_frequency import WordFrequency
from app.domain.services.lemmatizer_port import ILemmatizer


class FrequencyAnalysisService:
    """Domain-сервис: накапливает статистику по леммам из потока строк."""

    def __init__(self, lemmatizer: ILemmatizer) -> None:
        self._lemmatizer = lemmatizer

    def analyze(
        self,
        lines: Iterator[str],
    ) -> tuple[Dict[str, WordFrequency], int]:
        """
        Обходит строки документа и возвращает:
          - словарь {лемма -> WordFrequency}
          - общее количество строк
        """
        stats: Dict[str, WordFrequency] = {}
        total_lines = 0

        for line_index, line in enumerate(lines):
            total_lines += 1
            for token in self._lemmatizer.tokenize(line):
                lemma = self._lemmatizer.lemmatize(token)
                if lemma not in stats:
                    stats[lemma] = WordFrequency(lemma=lemma)
                stats[lemma].add_occurrence(line_index)

        return stats, total_lines
