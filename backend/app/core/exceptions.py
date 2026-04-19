from fastapi import HTTPException
from fastapi import status

class FileShouldBePDFException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Uploaded file format should be .pdf'
        )