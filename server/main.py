import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from server.configuration import Settings
from server.mqtt_handler import MQTTHandler
from server.rest_handler import RestHandler
from server.sse_handler import SSEHandler
from server.message_processor import MessageProcessor
from server.logger import setup_logger
from server.database import Database

# Load configuration
settings = Settings()

# Setup logging
logger = setup_logger()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize components
db = Database(settings)
mqtt_handler = MQTTHandler(settings, db)
sse_handler = SSEHandler(settings)
rest_handler = RestHandler(settings, db, mqtt_handler)
message_processor = MessageProcessor(settings, db, mqtt_handler, sse_handler)

# Include routers
app.include_router(rest_handler.router)
app.include_router(sse_handler.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the server")
    await db.connect()
    await mqtt_handler.connect()
    asyncio.create_task(mqtt_handler.process_messages())
    asyncio.create_task(message_processor.process_messages())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down the server")
    await mqtt_handler.disconnect()
    await db.disconnect()
    await sse_handler.close_connections()

async def main():
    config = uvicorn.Config("main:app", host=settings.HOST, port=settings.PORT, reload=True)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())   