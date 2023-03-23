from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from settings import settings
from service.routers import router

services_router = APIRouter(prefix='')

templates = Jinja2Templates(directory=f'{settings.APP_PATH}/templates')

# app.include_router(router=auth_router)
services_router.include_router(router=router)


@services_router.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})
