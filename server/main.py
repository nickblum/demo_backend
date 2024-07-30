import asyncio
import os
import signal
import sys
import time
import socket
from watchgod import awatch
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from server.configuration import Settings
from server.mqtt_handler import MQTTHandler
from server.rest_handler import RestHandler
from server.sse_handler import SSEHandler
from server.message_processor import MessageProcessor
from server.logger import setup_logger, get_logger
from server.database import Database
from server.error_handler import setup_error_handlers

# Load configuration
settings = Settings()

# Setup logging
setup_logger()
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Thistle Server API",
    description="API for the Thistle Server project",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Setup error handlers
setup_error_handlers(app)

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css">
            <title>Thistle Server API - Swagger UI</title>
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js"></script>
            <script>
                const ui = SwaggerUIBundle({
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout",
                    deepLinking: true
                })
            </script>
        </body>
        </html>
        """
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint():
    return get_openapi(
        title="Thistle Server API",
        version="1.0.0",
        description="API for the Thistle Server project",
        routes=app.routes,
    )

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    logger.info("Received exit signal %s...", signal.name)
    logger.info("Closing database connections")
    await db.disconnect()
    logger.info("Closing MQTT connections")
    await mqtt_handler.disconnect()
    logger.info("Closing SSE connections")
    await sse_handler.close_connections()

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]

    logger.info("Cancelling %d outstanding tasks", len(tasks))
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Shutting down asyncio loop")
    loop.stop()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the server")
    await db.connect()
    await mqtt_handler.connect()
    background_tasks.append(asyncio.create_task(mqtt_handler.maintain_connection()))
    background_tasks.append(asyncio.create_task(message_processor.process_messages()))

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
            logger.warning("Port %d is in use. Waiting for it to be free...", settings.PORT)
            time.sleep(2)
            retries -= 1
        else:
            break

    if retries == 0:
        logger.error("Could not start server. Port %d is still in use after multiple attempts.", settings.PORT)
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
    finally:
        reload_task.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

async def watch_and_reload(loop, server):
    async for changes in awatch('server'):
        logger.info("Detected changes in %s. Reloading...", changes)
        os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    start_server()