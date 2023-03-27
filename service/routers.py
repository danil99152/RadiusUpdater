import asyncio
import hashlib
import os
import subprocess
from http.client import HTTPException

import aiofiles
from fastapi import UploadFile, APIRouter, File

from settings import settings

UPLOAD_DIR = settings.APP_PATH + "/files/"
router = APIRouter(prefix='/file', tags=['file'])


# class FileInput(BaseModel):
#     file: UploadFile = File(default=None)
#     checksum: str


@router.post("/upload/")
async def upload_files(checksum: str, fi: UploadFile = File(default=None)):
    # Calculate the SHA256 hash of the uploaded file
    sha512_hash = hashlib.sha512()
    while True:
        chunk = await fi.read(8192)
        if not chunk:
            break
        sha512_hash.update(chunk)
    file_hash = sha512_hash.hexdigest()

    # Compare the calculated hash with the provided checksum
    if file_hash != checksum or not fi.filename.endswith('.tar.gz'):
        raise ValueError(f"File {fi.filename} has an incorrect checksum or format")

    # All files passed the checksum test, so we can save them to the upload directory
    upload_path = os.path.join(UPLOAD_DIR, fi.filename)

    try:
        await save_file(fi, upload_path)
        exit_code = subprocess.call('./updater.sh')
    except Exception:
        # Delete all files if at least one file fails to load
        upload_path = os.path.join(UPLOAD_DIR, fi.filename)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise HTTPException("Failed to save one or more files to disk")

    return {f"message": f"All files were successfully uploaded and {exit_code}"}


async def save_file(file, path):
    async with aiofiles.open(path, "wb") as f:
        while True:
            chunk = await file.read(8192)
            if not chunk:
                break
            await f.write(chunk)
