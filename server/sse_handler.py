""" Server-Sent Events (SSE) handler module """
import asyncio
import json
from typing import List
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from server.configuration import Settings
from server.logger import get_logger

logger = get_logger(__name__)

class SSEHandler:
    """ Server-Sent Events (SSE) handler """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.router = APIRouter()
        self.clients: List[asyncio.Queue] = []
        self.setup_routes()

    def setup_routes(self):
        """ Setup routes for the SSE handler """
        @self.router.get("/api/v1/sse")
        async def sse(request: Request):
            client_queue = asyncio.Queue()
            self.clients.append(client_queue)

            async def event_generator():
                try:
                    while True:
                        if await request.is_disconnected():
                            break

                        try:
                            payload = await asyncio.wait_for(client_queue.get(), timeout=1.0)
                            yield {
                                "event": "message",
                                "data": json.dumps(payload)
                            }
                        except asyncio.TimeoutError:
                            yield {
                                "event": "ping",
                                "data": ""
                            }
                finally:
                    self.clients.remove(client_queue)

            return EventSourceResponse(event_generator())

    async def send_event(self, payload: dict):
        """ Send an SSE event to all connected clients """
        for client in self.clients:
            await client.put(payload)
        logger.info("Sent SSE event to %s clients", len(self.clients))

    async def close_connections(self):
        """ Close all SSE connections """
        for client in self.clients:
            await client.put(None)
        self.clients.clear()
