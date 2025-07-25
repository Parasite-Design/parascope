from fastapi import FastAPI
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.v1.router import api_router

app = FastAPI(
    title="Bookstore API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Event handlers
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Include routers
app.include_router(api_router, prefix="/api/v1")