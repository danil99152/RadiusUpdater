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

UPLOAD_DIR = os.path.abspath('').replace('RadiusUpdater', '') + 'cicd/'
router = APIRouter(prefix='/file', tags=['file'])


@router.post("/upload/")
async def upload_files(checksum: str, fi: UploadFile = File(default=None)):
    # Calculate the SHA512 hash of the uploaded file
    sha512_hash = hashlib.sha512()
    while True:
        chunk = await fi.read(8192)
        if not chunk:
            break
        sha512_hash.update(chunk)
    file_hash = sha512_hash.hexdigest()

    # Compare the calculated hash with the provided checksum
    if file_hash != checksum or not fi.filename.endswith('.zip'):
        raise ValueError(f"File {fi.filename} has an incorrect checksum or format")

    try:
        await save_file(fi, UPLOAD_DIR)
        await updater()
    except Exception as e:
        # Delete all files if at least one file fails to load
        upload_path = os.path.join(UPLOAD_DIR, fi.filename)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise HTTPException("Failed to save one or more files to disk:", e)

    return {f"message": f"All files were successfully uploaded"}


async def save_file(file, path):
    async with aiofiles.open(os.path.join(path, 'radius_control_backend.zip'), 'wb') as out_file:
        while content := await file.read(1024):  # async read chunk
            await out_file.write(content)  # async write chunk


def check_int(pid) -> bool:
    return isinstance(pid, int)


def get_pids():
    try:
        return list(filter(check_int, [
            requests.get("http://0.0.0.0:5000/ad936x/get-pid/").text,
            requests.get("http://0.0.0.0:5000/control/get-pid/").text,
            requests.get("http://0.0.0.0:5000/relays_module/get-pid/").text,
            requests.get("http://0.0.0.0:5000/dsp/get-pid/").text,
            requests.get("http://0.0.0.0:5000/ocb/get-pid/").text,
            requests.get("http://0.0.0.0:5000/attenuators/get-pid/").text,
            requests.get("http://0.0.0.0:5000/services_module/get-pid/").text,
            requests.get("http://0.0.0.0:5000/automatic_control/get-pid/").text,
            requests.get("http://0.0.0.0:5000/server_integration/get-pid/").text,
            requests.get("http://0.0.0.0:5000/telemetry/get-pid/").text,
            requests.get("http://0.0.0.0:5000/killer/get-pid/").text,
        ]))
    finally:
        return []


async def restore_old_project():
    try:
        # Remove archive
        os.remove(os.path.join(UPLOAD_DIR, 'radius_control_backend.zip'))
        # Remove directory of new project
        shutil.rmtree(os.path.join(UPLOAD_DIR, 'radius_control_backend/'))
        # Rename old directory to radius_control_backend
        os.rename(os.path.join(UPLOAD_DIR, 'backup_radius_control_backend/'),
                  os.path.join(UPLOAD_DIR, 'radius_control_backend/'))
        # Run old project
        os.system(f"chmod +x {os.path.join(UPLOAD_DIR, 'radius_control_backend/run.sh')}")
        subprocess.call(os.path.join(UPLOAD_DIR, 'radius_control_backend/run.sh'))
    except Exception as e:
        raise HTTPException("Failed restore old project:", e)


async def updater():
    try:
        # Kill all project services
        pids = get_pids()
        [os.kill(eval(pid), signal.SIGTERM) for pid in pids]
        try:
            os.rename(os.path.join(UPLOAD_DIR, 'radius_control_backend/'),
                      os.path.join(UPLOAD_DIR, 'backup_radius_control_backend/'))
        except Exception as e:
            print(e)
    except Exception as e:
        await restore_old_project()
        raise HTTPException("Failed to kill old service:", e)

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
