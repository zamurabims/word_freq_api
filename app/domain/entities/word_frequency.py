from dataclasses import dataclass, field
from typing import DefaultDict
from collections import defaultdict


@dataclass
class WordFrequency:
    lemma: str
    total_count: int = 0
    line_counts: DefaultDict[int, int] = field(default_factory=lambda: defaultdict(int))

    def add_occurrence(self, line_index: int) -> None:
        self.total_count += 1
        self.line_counts[line_index] += 1

    def line_counts_as_string(self, total_lines: int) -> str:
        return ",".join(str(self.line_counts.get(i, 0)) for i in range(total_lines))
