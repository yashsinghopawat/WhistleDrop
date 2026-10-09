from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

import app.models  # noqa: F401  (makes sure all tables are registered)
from app.api.routes import auth, moderation, reports, users
from app.database.base import Base
from app.database.connection import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # creates the tables if they don't exist yet
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="WhistleDrop",
    description="Backend for an anonymous reporting system. Reporters submit reports without "
                "an account and track them with a case code. Moderators log in to review reports.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(reports.router)
app.include_router(moderation.router)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    # don't leak database details to the client
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on the server"})


@app.get("/", tags=["Health"])
def root():
    return {"message": "WhistleDrop API is running. Open /docs for Swagger."}
