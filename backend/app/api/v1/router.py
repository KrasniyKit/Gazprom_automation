import logging
from fastapi import APIRouter
from fastapi import UploadFile, HTTPException
from app.services.extract import process_passport_bytes, ExtractionError
from app.core.exceptions import FileShouldBePDFException
from app.utils.logs import log_execution_time


router = APIRouter(prefix="/api/v1", tags=["API"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/passport")
@log_execution_time(logger)
async def upload_passport(file: UploadFile):
    logger.info('Started uploading pdf file with filename=%s',file.filename)
    if not file.filename.endswith(".pdf"):
        logger.error('Error while downloading file: extension should be .pdf')
        raise FileShouldBePDFException()
    
    pdf_bytes = await file.read()

    try:
        result = process_passport_bytes(pdf_bytes, filename=file.filename)
        logger.info('Successfully extracted data from pdf file with filename=%s', file.filename)
        return result
    
    except ExtractionError as e:
        logger.error('Extraction failed for filename=%s: %s', file.filename, str(e))
        error_text = str(e)
        raise HTTPException(status_code=422, detail=f"Ошибка оцифровки документа: {error_text}")
    
    except Exception as e:
        logger.exception('Unexpected error for filename=%s', file.filename)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
