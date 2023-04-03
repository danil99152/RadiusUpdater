import hashlib
import os
import shutil
import signal
import subprocess
import zipfile
from http.client import HTTPException

import aiofiles as aiofiles
import requests
from fastapi import UploadFile, APIRouter, File

from settings import settings

UPLOAD_DIR = settings.UPLOAD_DIR
router = APIRouter(prefix='/file', tags=['file'])


@router.post("/upload/")
async def upload_files(checksum: str, fi: UploadFile = File(default=None)):
    try:
        await save_file(fi, UPLOAD_DIR)
    except Exception as e:
        # Delete all files if at least one file fails to load
        upload_path = os.path.join(UPLOAD_DIR, fi.filename)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise HTTPException("Failed to save one or more files to disk:", e)
    # Calculate the SHA512 hash of the uploaded file
    file_hash = hashlib.sha512(open(os.path.join(UPLOAD_DIR, 'radius_control_backend.zip'),'rb').read()).hexdigest()

    # Compare the calculated hash with the provided checksum
    if file_hash != checksum or not fi.filename.endswith('.zip'):
        upload_path = os.path.join(UPLOAD_DIR, fi.filename)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise ValueError(f"File {fi.filename} has an incorrect checksum or format")

    await updater()
    return {f"message": f"All files were successfully uploaded"}


async def save_file(file, path):
    async with aiofiles.open(os.path.join(path, 'radius_control_backend.zip'), 'wb') as out_file:
        # TODO change size of batch to check download speed
        while content := await file.read(1024):  # async read chunk
            await out_file.write(content)  # async write chunk



async def kill_services():
    kill_urls = [
            "http://127.0.0.1:5000/ad936x/kill-service/",
            "http://127.0.0.1:5000/control/kill-service/",
            "http://127.0.0.1:5000/relays_module/kill-service/",
            "http://127.0.0.1:5000/dsp/kill-service/",
            "http://127.0.0.1:5000/ocb/kill-service/",
            "http://127.0.0.1:5000/attenuators/kill-service/",
            "http://127.0.0.1:5000/services_module/kill-service/",
            "http://127.0.0.1:5000/automatic_control/kill-service/",
            "http://127.0.0.1:5000/server_integration/kill-service/",
            "http://127.0.0.1:5000/telemetry/kill-service/",
            "http://127.0.0.1:5000/killer/kill-service/",
        ]
    for url in kill_urls:
        try:
            requests.get(url)
        except:
            continue


async def restore_old_project():
    try:
        # Remove archive
        try:
            os.remove(os.path.join(UPLOAD_DIR, 'radius_control_backend.zip'))
        except Exception as e:
            print(e)
        # Remove directory of new project
        try:
            shutil.rmtree(os.path.join(UPLOAD_DIR, 'radius_control_backend/'))
        except Exception as e:
            print(e)
        # Rename old directory to radius_control_backend
        try:
            os.rename(os.path.join(UPLOAD_DIR, 'backup_radius_control_backend/'),
                      os.path.join(UPLOAD_DIR, 'radius_control_backend/'))
        except Exception as e:
            print(e)
        # Run old project
        try:
            os.system(f"chmod +x {os.path.join(UPLOAD_DIR, 'radius_control_backend/run.sh')}")
            subprocess.call(os.path.join(UPLOAD_DIR, 'radius_control_backend/run.sh'))
        except Exception as e:
            print(e)
    except Exception as e:
        raise HTTPException("Failed restore old project:", e)


async def updater():
    # Kill all project services
    await kill_services()
    try:
        os.rename(os.path.join(UPLOAD_DIR, 'radius_control_backend/'),
                  os.path.join(UPLOAD_DIR, 'backup_radius_control_backend/'))
    except Exception as e:
        print(e)

    try:
        # Unzipping new
        with zipfile.ZipFile(os.path.join(UPLOAD_DIR, 'radius_control_backend.zip'), 'r') as zip_ref:
            zip_ref.extractall(UPLOAD_DIR)
    except Exception as e:
        await restore_old_project()
        raise HTTPException("Failed extract new project:", e)

    try:
        # Run new project
        os.system(f"chmod +x {os.path.join(UPLOAD_DIR, 'radius_control_backend/run.sh')}")
        subprocess.call(os.path.join(UPLOAD_DIR, 'radius_control_backend/run.sh'))
    except Exception as e:
        await restore_old_project()
        raise HTTPException("Failed to run new project:", e)
    # Remove archive and directory of old project
    os.remove(os.path.join(UPLOAD_DIR, 'radius_control_backend.zip'))
    shutil.rmtree(os.path.join(UPLOAD_DIR, 'backup_radius_control_backend/'))
