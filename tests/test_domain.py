"""
Юнит-тесты (запуск: pytest tests/)
Не требуют внешних зависимостей кроме стандартной библиотеки Python.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import unittest
from collections import defaultdict
from unittest.mock import MagicMock

from app.domain.entities.word_frequency import WordFrequency
from app.domain.services.frequency_analysis_service import FrequencyAnalysisService


class TestWordFrequency(unittest.TestCase):
    def test_add_occurrence_increments_total(self):
        wf = WordFrequency(lemma="житель")
        wf.add_occurrence(0)
        wf.add_occurrence(2)
        wf.add_occurrence(2)
        self.assertEqual(wf.total_count, 3)

    def test_line_counts_as_string(self):
        wf = WordFrequency(lemma="житель")
        wf.add_occurrence(0)
        wf.add_occurrence(2)
        wf.add_occurrence(2)
        result = wf.line_counts_as_string(total_lines=4)
        self.assertEqual(result, "1,0,2,0")

    def test_empty_word_frequency(self):
        wf = WordFrequency(lemma="тест")
        self.assertEqual(wf.line_counts_as_string(3), "0,0,0")


class TestFrequencyAnalysisService(unittest.TestCase):
    def _make_lemmatizer(self, lemma_map: dict):
        """Мок-лемматизатор: tokenize разбивает по пробелам, lemmatize по словарю."""
        lem = MagicMock()
        lem.tokenize.side_effect = lambda text: text.split()
        lem.lemmatize.side_effect = lambda word: lemma_map.get(word, word)
        return lem

    def test_basic_analysis(self):
        lemma_map = {"жителем": "житель", "житель": "житель", "город": "город"}
        service = FrequencyAnalysisService(self._make_lemmatizer(lemma_map))
        lines = iter(["житель город", "жителем"])
        stats, total_lines = service.analyze(lines)

        self.assertEqual(total_lines, 2)
        self.assertIn("житель", stats)
        self.assertEqual(stats["житель"].total_count, 2)
        self.assertEqual(stats["город"].total_count, 1)

    def test_line_index_tracking(self):
        lemma_map = {"слово": "слово"}
        service = FrequencyAnalysisService(self._make_lemmatizer(lemma_map))
        lines = iter(["слово", "нет", "слово слово"])
        stats, _ = service.analyze(lines)

        self.assertEqual(stats["слово"].line_counts[0], 1)
        self.assertEqual(stats["слово"].line_counts[1], 0)
        self.assertEqual(stats["слово"].line_counts[2], 2)

    def test_empty_file(self):
        service = FrequencyAnalysisService(self._make_lemmatizer({}))
        stats, total_lines = service.analyze(iter([]))
        self.assertEqual(total_lines, 0)
        self.assertEqual(stats, {})


if __name__ == "__main__":
    unittest.main()
