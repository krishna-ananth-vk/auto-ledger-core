import os
from typing import Union
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table, Column, Integer, String

DATABASE_URL = os.getenv("DATABASE_URL", "")

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

app = FastAPI()

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, nullable=False),
    Column("email", String, unique=True, index=True),
)

@app.on_event("startup")
async def startup():
    """Initialize the database connection."""
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    """Close the database connection."""
    await engine.dispose()

@app.get("/")
def read_root():
    return "Welcome to your personal garage"

@app.post("/test/")
async def create_user(name: str, email: str):
    """Create a new user."""
    async with async_session() as session:
        async with session.begin():
            new_user = {"name": name, "email": email}
            await session.execute(users.insert().values(new_user))
        return {"message": "User created successfully"}