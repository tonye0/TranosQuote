"""
AC Combiner Panel Quotation API

Run with:
    uvicorn app.main:app --reload --port 8000

Interactive docs available at /docs once running.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models.db import init_db
from routers import reference, quotation, admin

app = FastAPI(
    title="AC Combiner Panel Quotation API",
    description=(
        "API for generating BOM and technical specification documents for AC "
        "combiner panels. Allows sales teams to configure incomers, outgoings "
        "and accessories, then export an Excel BOM and Word spec sheet."
    ),
    version="1.0.0",
)

# Allow the frontend (running on a different port/origin during dev) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "service": "AC Combiner Panel Quotation API",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(reference.router)
app.include_router(quotation.router)
app.include_router(admin.router)
