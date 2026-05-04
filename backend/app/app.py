from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from starlette.middleware.cors import CORSMiddleware

from app.services.seed_service import SeedService
from app.database.connection import session_local, init_db, engine
from app.routes.user import router as user_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan context to initialize DB and seed data."""
    await init_db()

    async with session_local() as db:
        seed_service = SeedService(db)
        await seed_service.seed_first_user()

    yield

    await engine.dispose()


# ✅ attach lifespan here
app = FastAPI(lifespan=lifespan)


origins = [
    "http://localhost:3000",
    "http://localhost:3030",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to Digital academic monitoring and engagement system"}


app.include_router(user_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)