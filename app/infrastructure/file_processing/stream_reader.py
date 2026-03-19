from typing import Iterator, AsyncIterator
import asyncio


def iter_lines_from_bytes(data: bytes, encoding: str = "utf-8") -> Iterator[str]:
    """Потоковое чтение строк из байтового потока без загрузки всего файла в память."""
    buffer = b""
    for chunk in _chunked(data, chunk_size=65536):
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            yield line.decode(encoding, errors="replace")
    if buffer:
        yield buffer.decode(encoding, errors="replace")


def _chunked(data: bytes, chunk_size: int):
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]


async def iter_lines_async(stream, chunk_size: int = 65536) -> AsyncIterator[str]:
    """Асинхронное потоковое чтение строк из UploadFile."""
    buffer = b""
    while True:
        chunk = await stream.read(chunk_size)
        if not chunk:
            break
        buffer += chunk
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            yield line.decode("utf-8", errors="replace")
        # Освобождаем управление event loop'у
        await asyncio.sleep(0)
    if buffer:
        yield buffer.decode("utf-8", errors="replace")
