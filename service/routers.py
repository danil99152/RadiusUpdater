import hashlib
import os
import shutil
import signal
import subprocess
import tarfile
from http.client import HTTPException
from tempfile import NamedTemporaryFile

import requests
from fastapi import UploadFile, APIRouter, File

UPLOAD_DIR = os.path.abspath('').replace('RadiusUpdater', '') + 'cicd/'
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
        await updater()
    except Exception as e:
        # Delete all files if at least one file fails to load
        upload_path = os.path.join(UPLOAD_DIR, fi.filename)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise HTTPException("Failed to save one or more files to disk:", e)

    return {f"message": f"All files were successfully uploaded"}


async def save_file(file, path):
    with NamedTemporaryFile(delete=False, suffix='.tar.gz', prefix='radius_control_backend', dir=path) as tmp:
        shutil.copyfileobj(file.file, tmp)
        os.rename(tmp.name, path+'radius_control_backend.tar.gz')


def check_int(pid) -> bool:
    return isinstance(pid, int)


def get_pids():
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


async def restore_old_project():
    try:
        os.remove(UPLOAD_DIR + 'radius_control_backend.tar.gz')
        shutil.rmtree(UPLOAD_DIR + 'radius_control_backend/')
        os.rename(UPLOAD_DIR + 'backup_radius_control_backend/', UPLOAD_DIR + 'radius_control_backend/')
        os.system(f"chmod +x {UPLOAD_DIR + 'radius_control_backend/run.sh'}")
        subprocess.call(UPLOAD_DIR + 'radius_control_backend/run.sh')
    except Exception as e:
        raise HTTPException("Failed restore old project:", e)


async def updater():
    try:
        pids = get_pids()
        [os.kill(eval(pid), signal.SIGTERM) for pid in pids]
        try:
            os.rename(UPLOAD_DIR + 'radius_control_backend/', UPLOAD_DIR + 'backup_radius_control_backend/')
        except Exception as e:
            print(e)
    except Exception as e:
        await restore_old_project()
        raise HTTPException("Failed to kill old service:", e)

    try:
        file = tarfile.open(UPLOAD_DIR + 'radius_control_backend.tar.gz')
        file.extractall('.')
        file.close()
    except Exception as e:
        await restore_old_project()
        raise HTTPException("Failed extract new project:", e)

    try:
        os.system(f"chmod +x {UPLOAD_DIR + 'radius_control_backend/run.sh'}")
        subprocess.call(UPLOAD_DIR + 'radius_control_backend/run.sh')
    except Exception as e:
        await restore_old_project()
        raise HTTPException("Failed to run new project:", e)

    shutil.rmtree(UPLOAD_DIR + 'radius_control_backend/')
    os.remove(UPLOAD_DIR + 'radius_control_backend.tar.gz')
