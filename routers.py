from fastapi import APIRouter

from service.routers import router

services_router = APIRouter(prefix='')

services_router.include_router(router=router)
