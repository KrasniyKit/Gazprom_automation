import logging
from fastapi import APIRouter
from fastapi import UploadFile
from app.core.exceptions import FileShouldBePDFException
from app.utils.logs import log_execution_time


router = APIRouter(prefix="/api/v1", tags=["API"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/passport")
@log_execution_time
async def upload_passport(file: UploadFile):
    logger.info('Started uploading pdf file with filename=%s',file.filename)
    if not file.filename.endswith(".pdf"):
        logger.error('Error while downloading file: extension should be .pdf')
        raise FileShouldBePDFException()
    pdf_bytes = await file.read()
    # Здесь будет логика вызова сервиса по обработке PDF
    # Пример:
    # result = service.process_pdf()
    # logger.info('Successfully uploaded pdf file with filename=%s',file.filename)
    # return result
    return {'result': 'Hello world!'}




