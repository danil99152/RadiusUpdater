import hashlib
import os
import shutil
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
    file_hash = hashlib.sha512(open(os.path.join(UPLOAD_DIR, 'radius_control_backend.zip'), 'rb').read()).hexdigest()


    # Compare the calculated hash with the provided checksum
    if file_hash != checksum or not fi.filename.endswith('.zip'):
        upload_path = os.path.join(UPLOAD_DIR, fi.filename)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        raise ValueError(f"File {fi.filename} has an incorrect checksum or format")

    await updater(fi.filename)
    return {f"message": f"All files were successfully uploaded"}


async def save_file(file, path):
    async with aiofiles.open(os.path.join(path, 'radius_control_backend.zip'), 'wb') as out_file:
        # TODO change size of batch to check download speed
        while content := await file.read(1024):  # async read chunk
            await out_file.write(content)  # async write chunk



async def kill_services():
    kills = [
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_software_dma_server"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/ad936x/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/attenuators/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/automatic_control/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/control/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/dsp/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_frontend/main.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/killer/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/main.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/ocb/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/relays_module/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/services_module/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/telemetry/run.py"',
        'sudo pkill -SIGKILL -f "/home/debian/rcs/software/radius_control_backend/services/server_integration/run.py"'
    ]
    for cmd in kills:
        os.system(cmd)

    os.system(f'sudo sh {UPLOAD_DIR}software/radius_control_backend/common/third_party/stop_all_services.sh')


async def restore_old_project(filename):
    try:
        # Remove archive
        try:
            os.remove(os.path.join(UPLOAD_DIR, filename))
        except Exception as e:
            print(e)
        # Remove directory of new project and venv
        try:
            if os.path.exists(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_backend')):
                shutil.rmtree(os.path.join(UPLOAD_DIR, 'software/radius_control_backend/'))
                # Rename old directory to radius_control_ and venv
                try:
                    os.rename(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_backend/'),
                              os.path.join(UPLOAD_DIR, 'software/radius_control_backend/'))
                except Exception as e:
                    print(e)
            if os.path.exists(os.path.join(UPLOAD_DIR, 'backup_python3.10')):
                shutil.rmtree(os.path.join(UPLOAD_DIR, 'python3.10/'))
                try:
                    os.rename(os.path.join(UPLOAD_DIR, 'backup_python3.10/'),
                              os.path.join(UPLOAD_DIR, 'python3.10/'))
                except Exception as e:
                    print(e)
            if os.path.exists(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_frontend')):
                shutil.rmtree(os.path.join(UPLOAD_DIR, 'software/radius_control_frontend/'))
                try:
                    os.rename(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_frontend/'),
                              os.path.join(UPLOAD_DIR, 'software/radius_control_frontend/'))
                except Exception as e:
                    print(e)
            if os.path.exists(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_software_dma_server')):
                shutil.rmtree(os.path.join(UPLOAD_DIR, 'software/radius_control_software_dma_server'))
                try:
                    os.rename(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_software_dma_server'),
                              os.path.join(UPLOAD_DIR, 'software/radius_control_software_dma_server'))
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)
        # Run old project
        try:
            os.system(
                f"chmod +x {os.path.join(UPLOAD_DIR, 'software/radius_control_backend/common/third_party/start_all_services.sh')}")
            subprocess.call(
                os.path.join(UPLOAD_DIR, 'software/radius_control_backend/common/third_party/start_all_services.sh'), shell=True)
        except Exception as e:
            print(e)
    except Exception as e:
        raise HTTPException("Failed restore old project:", e)


async def updater(filename):
    # Kill all project services
    await kill_services()

    try:
        # Unzipping new
        with zipfile.ZipFile(os.path.join(UPLOAD_DIR, filename), 'r') as zip_ref:
            zip_ref.extractall(UPLOAD_DIR)
        if os.path.exists(os.path.join(UPLOAD_DIR, 'radius_control_backend')):
            try:
                os.rename(os.path.join(UPLOAD_DIR, 'software/radius_control_backend/'),
                          os.path.join(UPLOAD_DIR, 'software/backup_radius_control_backend/'))
            except Exception as e:
                # Exception is always in renaming, but it works
                print(e)
            shutil.move(os.path.join(UPLOAD_DIR, 'radius_control_backend'),
                        (os.path.join(UPLOAD_DIR, 'software/radius_control_backend')))
        if os.path.exists(os.path.join(UPLOAD_DIR, 'venv')):
            try:
                os.rename(os.path.join(UPLOAD_DIR, 'python3.10/'),
                          os.path.join(UPLOAD_DIR, 'backup_python3.10/'))
                os.rename(os.path.join(UPLOAD_DIR, 'venv/'),
                          os.path.join(UPLOAD_DIR, 'python3.10/'))
            except Exception as e:
                print(e)
        if os.path.exists(os.path.join(UPLOAD_DIR, 'radius_control_frontend')):
            try:
                os.rename(os.path.join(UPLOAD_DIR, 'software/radius_control_frontend/'),
                          os.path.join(UPLOAD_DIR, 'software/backup_radius_control_frontend/'))
            except Exception as e:
                # Exception is always in renaming, but it works
                print(e)
            shutil.move(os.path.join(UPLOAD_DIR, 'radius_control_frontend'),
                        (os.path.join(UPLOAD_DIR, 'software/radius_control_frontend')))
        if os.path.isfile(os.path.join(UPLOAD_DIR, 'radius_control_software_dma_server')):
            try:
                os.rename(os.path.join(UPLOAD_DIR, 'software/radius_control_software_dma_server'),
                          os.path.join(UPLOAD_DIR, 'software/backup_radius_control_software_dma_server'))
            except Exception as e:
                # Exception is always in renaming, but it works
                print(e)
            shutil.move(os.path.join(UPLOAD_DIR, 'radius_control_software_dma_server'),
                        (os.path.join(UPLOAD_DIR, 'software/radius_control_software_dma_server')))
    except Exception as e:
        os.remove(os.path.join(UPLOAD_DIR, filename))
        raise HTTPException("Failed extract new project:", e)

    try:
        # Run new project
        os.system(
            f"chmod +x {os.path.join(UPLOAD_DIR, 'software/radius_control_backend/common/third_party/start_all_services.sh')}")
        subprocess.call(os.path.join(UPLOAD_DIR,
                                     'software/radius_control_backend/common/third_party/start_all_services.sh'), shell=True)
    except Exception as e:
        await restore_old_project(filename)
        raise HTTPException("Failed to run new project:", e)
    # Remove archive and directory of old project
    os.remove(os.path.join(UPLOAD_DIR, filename))
    if os.path.exists(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_backend/')):
        shutil.rmtree(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_backend/'))
    if os.path.exists(os.path.join(UPLOAD_DIR, 'backup_python3.10/')):
        shutil.rmtree(os.path.join(UPLOAD_DIR, 'backup_python3.10/'))
    if os.path.exists(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_frontend/')):
        shutil.rmtree(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_frontend/'))
    if os.path.isfile(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_software_dma_server')):
        os.remove(os.path.join(UPLOAD_DIR, 'software/backup_radius_control_software_dma_server'))

    os.system('sudo chmod 777 -R /home/debian/rcs/')
    os.system("sudo reboot")
