import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import AsyncIterator

from app.domain.services.frequency_analysis_service import FrequencyAnalysisService
from app.domain.services.lemmatizer_port import ILemmatizer
from app.infrastructure.excel.excel_report_builder import ExcelReportBuilder
from app.infrastructure.nlp.pymorphy3_lemmatizer import Pymorphy3Lemmatizer


def _analyze_in_worker(lines: list[str]) -> tuple[dict, int]:
    """
    Запускается в отдельном процессе (ProcessPoolExecutor),
    чтобы не блокировать event loop при CPU-интенсивной лемматизации.
    """
    lemmatizer = Pymorphy3Lemmatizer()
    service = FrequencyAnalysisService(lemmatizer)
    stats, total_lines = service.analyze(iter(lines))
    # Конвертируем в сериализуемый формат для передачи между процессами
    serializable = {
        lemma: (wf.total_count, dict(wf.line_counts))
        for lemma, wf in stats.items()
    }
    return serializable, total_lines


class ExportReportUseCase:
    """
    Use-case: принимает поток строк файла, запускает анализ в фоне,
    возвращает готовый xlsx как байты.

    Тяжёлая CPU-работа (лемматизация) вынесена в ProcessPoolExecutor,
    что позволяет FastAPI обрабатывать другие запросы параллельно.
    """

    CHUNK_LINES = 5_000  # строк в одном батче

    def __init__(self, executor: ProcessPoolExecutor) -> None:
        self._executor = executor
        self._excel_builder = ExcelReportBuilder()

    async def execute(self, line_stream: AsyncIterator[str]) -> bytes:
        loop = asyncio.get_running_loop()

        # Собираем строки батчами и отправляем в процесс
        all_serialized: dict[str, tuple[int, dict[int, int]]] = {}
        total_lines = 0
        batch: list[str] = []

        async for line in line_stream:
            batch.append(line)
            if len(batch) >= self.CHUNK_LINES:
                partial, n = await loop.run_in_executor(
                    self._executor, _analyze_in_worker, batch
                )
                self._merge(all_serialized, partial, total_lines)
                total_lines += n
                batch = []

        if batch:
            partial, n = await loop.run_in_executor(
                self._executor, _analyze_in_worker, batch
            )
            self._merge(all_serialized, partial, total_lines)
            total_lines += n

        # Десериализуем обратно в WordFrequency для построения отчёта
        from app.domain.entities.word_frequency import WordFrequency
        from collections import defaultdict

        stats = {}
        for lemma, (total, line_counts_dict) in all_serialized.items():
            wf = WordFrequency(lemma=lemma)
            wf.total_count = total
            wf.line_counts = defaultdict(int, {int(k): v for k, v in line_counts_dict.items()})
            stats[lemma] = wf

        # Генерация xlsx — в отдельном потоке (I/O bound)
        xlsx_bytes = await loop.run_in_executor(
            None, self._excel_builder.build, stats, total_lines
        )
        return xlsx_bytes

    @staticmethod
    def _merge(
        target: dict[str, tuple[int, dict[int, int]]],
        source: dict[str, tuple[int, dict[int, int]]],
        line_offset: int,
    ) -> None:
        """Объединяет батч-результаты, корректируя индексы строк."""
        for lemma, (count, line_counts) in source.items():
            adjusted = {k + line_offset: v for k, v in line_counts.items()}
            if lemma not in target:
                target[lemma] = (count, adjusted)
            else:
                old_count, old_lc = target[lemma]
                merged_lc = dict(old_lc)
                for idx, cnt in adjusted.items():
                    merged_lc[idx] = merged_lc.get(idx, 0) + cnt
                target[lemma] = (old_count + count, merged_lc)
