from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .routers.dives import dives_router
from .routers.media_items import media_items_router

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dives_router)
app.include_router(media_items_router)
app.mount('/uploads', StaticFiles(directory='uploads'), name='uploads')

@app.get('/')
async def root():
    return {'hello': 'world'}

def whale():
    whale = """
         .
        ":"
      ___:____     |"\/"|
    ,'        `.    \  /
    |  O        \___/  |
  ~^~^~^~^~^~^~^~^~^~^~^~^~
    """
    print(whale)

whale()