from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import products
from app.database import init_db
from app.socket import sio_app

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api")
app.mount('/', sio_app)
