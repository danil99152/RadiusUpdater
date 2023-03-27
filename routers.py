from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from settings import settings
from service.routers import router

services_router = APIRouter(prefix='')

services_router.include_router(router=router)
