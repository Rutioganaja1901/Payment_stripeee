from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .payments import router as payments_router
from .db import init_db

app = FastAPI(title="Stripe + FastAPI Demo")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# init DB if needed
init_db()

app.include_router(payments_router)

@app.get("/")
def root():
    return {"message": "Stripe FastAPI running"}
