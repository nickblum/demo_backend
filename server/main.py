import asyncio
import os
import signal
import sys
import time
import socket
from watchgod import awatch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from server.configuration import Settings
from server.mqtt_handler import MQTTHandler
from server.rest_handler import RestHandler
from server.sse_handler import SSEHandler
from server.message_processor import MessageProcessor
from server.logger import setup_logger, get_logger
from server.database import Database

# Load configuration
settings = Settings()

# Setup logging
setup_logger()
logger = get_logger(__name__)

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

# Store background tasks
background_tasks = []

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    logger.info(f"Received exit signal {signal.name}...")
    
    try:
        logger.info("Closing database connections")
        await db.disconnect()
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
    
    try:
        logger.info("Closing MQTT connections")
        await mqtt_handler.disconnect()
    except Exception as e:
        logger.error(f"Error closing MQTT connections: {str(e)}")
    
    try:
        logger.info("Closing SSE connections")
        await sse_handler.close_connections()
    except Exception as e:
        logger.error(f"Error closing SSE connections: {str(e)}")
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Shutting down asyncio loop")
    loop.stop()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the server")
    try:
        await db.connect()
        await mqtt_handler.connect()
        background_tasks.append(asyncio.create_task(mqtt_handler.maintain_connection()))
        background_tasks.append(asyncio.create_task(message_processor.process_messages()))
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI shutdown event triggered")

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_server():
    retries = 5
    while retries > 0:
        if is_port_in_use(settings.PORT):
            logger.warning(f"Port {settings.PORT} is in use. Waiting for it to be free...")
            time.sleep(2)
            retries -= 1
        else:
            break
    
    if retries == 0:
        logger.error(f"Could not start server. Port {settings.PORT} is still in use after multiple attempts.")
        sys.exit(1)

    config = uvicorn.Config("server.main:app", host=settings.HOST, port=settings.PORT, reload=False)
    server = uvicorn.Server(config)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop)))
    
    reload_task = loop.create_task(watch_and_reload(loop, server))
    
    try:
        loop.run_until_complete(server.serve())
    except Exception as e:
        logger.error(f"Error running server: {str(e)}")
    finally:
        reload_task.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

async def watch_and_reload(loop, server):
    try:
        async for changes in awatch('server'):
            logger.info(f"Detected changes in {changes}. Reloading...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        logger.error(f"Error in file watcher: {str(e)}")

if __name__ == "__main__":
    start_server()