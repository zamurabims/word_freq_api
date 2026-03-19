from concurrent.futures import ProcessPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response

from app.api.dependencies.executor import get_executor
from app.application.use_cases.export_report import ExportReportUseCase
from app.infrastructure.file_processing.stream_reader import iter_lines_async

router = APIRouter(prefix="/public/report", tags=["report"])

ALLOWED_CONTENT_TYPES = {"text/plain", "application/octet-stream", "text/csv"}
MAX_FILENAME_LEN = 255


@router.post(
    "/export",
    summary="Частотный анализ текстового файла → xlsx",
    response_description="Excel-файл с частотной статистикой словоформ",
    responses={
        200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}},
        400: {"description": "Неверный формат файла"},
        413: {"description": "Файл слишком мал (пустой)"},
    },
    status_code=status.HTTP_200_OK,
)
async def export_report(
    file: UploadFile = File(..., description="Текстовый файл (UTF-8)"),
    executor: ProcessPoolExecutor = Depends(get_executor),
) -> Response:
    
    _validate_upload(file)

    use_case = ExportReportUseCase(executor=executor)
    try:
        xlsx_bytes = await use_case.execute(iter_lines_async(file))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки файла: {exc}",
        ) from exc

    filename = _safe_filename(file.filename)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}_report.xlsx"',
            "Content-Length": str(len(xlsx_bytes)),
        },
    )


def _validate_upload(file: UploadFile) -> None:
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый тип файла: {file.content_type}. "
                   f"Ожидается text/plain.",
        )


def _safe_filename(name: str | None) -> str:
    if not name:
        return "result"
    stem = name.rsplit(".", 1)[0]
    safe = "".join(c for c in stem if c.isalnum() or c in "-_")
    return safe[:50] or "result"
