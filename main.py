# fmt: off
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from responder import router
# fmt: on

logger = logging.getLogger("data_api_logger")
logger.setLevel(logging.INFO)

app = FastAPI()

origins = [
    "http://localhost:3000",  # Allow localhost for development
    "https://fleet.so",  # Add your frontend URL
    "*",
]

routers = [router]
for router in routers:
    app.include_router(router)


@app.get("/status")
async def read_status():
    return {"status": "ok"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.usefleet.ai",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    logging.info("Starting Github issues responder API on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
