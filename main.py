import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from settings import settings
from routers import services_router

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', encoding='utf-8', level=logging.DEBUG)

app = FastAPI(docs_url='/api/', redoc_url=None, title=settings.APP_TITLE, version=settings.APP_VERSION,
              swagger_ui_oauth2_redirect_url='/api/oauth2-redirect/')

origins = ['*']

app.add_middleware(middleware_class=CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=['*'],
                   allow_headers=['*'],
                   )

app.include_router(router=services_router)

if __name__ == '__main__':
    uvicorn.run(app=app, app_dir=settings.APP_PATH, host=settings.APP_HOST, port=settings.APP_PORT)
