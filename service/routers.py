import hashlib
import os
import subprocess
from http.client import HTTPException

from fastapi import UploadFile, APIRouter, File

UPLOAD_DIR = os.path.abspath('').replace('RadiusUpdater', '')+'cicd/radius_control_backend.tar.gz'
router = APIRouter(prefix='/file', tags=['file'])


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

    try:
        await save_file(fi, UPLOAD_DIR)
        os.system(f"chmod +x {os.path.abspath('service/updater.sh')}")
        exit_code = subprocess.call(os.path.abspath('service/updater.sh'))
    except Exception as e:
        # Delete all files if at least one file fails to load
        upload_path = os.path.join(UPLOAD_DIR, fi.filename)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise HTTPException("Failed to save one or more files to disk:", e)

    return {f"message": f"All files were successfully uploaded and {exit_code}"}


async def save_file(file, path):
    with open(path, 'wb') as f:
        while True:
            chunk = await file.read(8192)
            if not chunk:
                break
            f.write(chunk)
