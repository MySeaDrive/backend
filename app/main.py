from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.dives import dives_router
from .routers.media_items import media_items_router
from rq_dashboard_fast import RedisQueueDashboard

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myseadrive.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routes
app.include_router(dives_router)
app.include_router(media_items_router)

# Mount RQ dashboard
rq_dashboard = RedisQueueDashboard(prefix="/rq")
app.mount("/rq", rq_dashboard)


@app.get('/')
async def root():
    return {'hello': 'ocean'}

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