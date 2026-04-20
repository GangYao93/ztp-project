from contextlib import asynccontextmanager

from fastapi import FastAPI
from database.database import init_database
from api import deviceApi
from tools.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):

    # ===== startup =====
    setup_logging()
    await init_database()
    # inspector = inspect(engine)
    # tables = inspector.get_table_names()

    # print("DB Tables:", tables)

    yield

    # ===== shutdown =====
    print("shutting down ZTP controller")


app = FastAPI(lifespan=lifespan)
app.include_router(deviceApi.router)




