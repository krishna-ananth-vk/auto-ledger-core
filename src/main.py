import os
from typing import Union
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table, Column, Integer, String
from pydantic import BaseModel


DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    ""
)

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


metadata = MetaData()

test_table = Table(
    "test",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("uuid", String, index=True),
    Column("name", String, nullable=False),
    Column("year", Integer, nullable=False),
)

app = FastAPI()

async def get_db():
    async with async_session() as session:
        yield session

class TestCreate(BaseModel):
    name: str
    year: int


@app.on_event("startup")
async def startup():
    """Initialize the database connection."""
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

@app.on_event("shutdown")
async def shutdown():
    """Close the database connection."""
    await engine.dispose()

@app.get("/")
def read_root():
    return "Welcome to your personal garage"

@app.post("/test/", response_model=dict)
async def create_test(data: TestCreate, db: AsyncSession = Depends(get_db)):
    """Create a new entry in the test table."""
    query = test_table.insert().values(name=data.name, year=data.year)
    await db.execute(query)
    await db.commit()
    return {"message": "Data inserted successfully"}

@app.get("/test/")
async def get_all_tests(db: AsyncSession = Depends(get_db)):
    """Fetch all rows from the test table."""
    query = test_table.select()
    result = await db.execute(query)
    
    # Convert the result to a list of dictionaries
    rows = result.fetchall()
    data = [{"id": row.id, "uuid": row.uuid, "name": row.name, "year": row.year} for row in rows]
    
    return data