from typing import List, Union

import aiofiles as aiofiles
from fastapi import APIRouter, UploadFile, File, Form
from starlette.responses import JSONResponse

from service.api import ModelApi

router = APIRouter(prefix='/file', tags=['file'])
api = ModelApi()


@router.get('/ping', response_class=JSONResponse)
async def ping():
    response = api.ping()
    return response


@router.post('/upload-file/', response_class=JSONResponse)
async def upload_file(file: UploadFile = File(default=None)):
    try:
        out_file_path = '/home/debian/work/' + file.filename
        async with aiofiles.open(out_file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        response = await api.update(out_file_path)
        return response
    except Exception as e:
        return f'Exception at upload_matrix: {e}'
