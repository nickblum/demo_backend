""" REST API handler for the server. """
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, ValidationError
from server.configuration import Settings, get_settings
from server.database import Database
from server.mqtt_handler import MQTTHandler
from server.services import PacketService

router = APIRouter()

class Packet(BaseModel):
    device_id: int
    command: int

class RestHandler:
    def __init__(self, settings: Settings, db: Database, mqtt_handler: MQTTHandler):
        self.settings = settings
        self.db = db
        self.mqtt_handler = mqtt_handler
        self.router = APIRouter()
        self.packet_service = PacketService(db, mqtt_handler)
        self.setup_routes()

    def setup_routes(self):
        @self.router.post("/api/v1/packets", status_code=201)
        async def submit_packet(packet: Packet):
            """
            Submit a new packet.

            This endpoint accepts a packet with a device_id and command,
            stores it in the database, and publishes it to MQTT.

            Args:
                packet (Packet): The packet to be submitted.

            Returns:
                dict: A dictionary containing a success message and the ID of the submitted packet.

            Raises:
                HTTPException: If there's a validation error or any other exception occurs.
            """
            try:
                result = await self.packet_service.submit_packet(packet.dict())
                return {"message": "Packet submitted successfully", "id": result["id"]}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e

        @self.router.get("/ping")
        async def ping():
            """
            Ping endpoint to check if the server is running.

            Returns:
                dict: A dictionary containing the status and current timestamp.
            """
            return {
                "status": "OK",
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.router.get("/rereadenv")
        async def reread_env(settings: Settings = Depends(get_settings)):
            """
            Re-read environment variables.

            This endpoint updates the application settings by re-reading the environment variables.

            Returns:
                dict: A dictionary containing a success message.

            Raises:
                HTTPException: If there's an error updating the environment variables.
            """
            try:
                self.settings = settings
                return {"message": "Environment variables updated successfully"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to update environment variables: {str(e)}") from e

        @self.router.get("/api/v1/messages")
        async def get_messages(
            limit: int = Query(100, ge=1, le=1000),
            start_time: Optional[float] = Query(None, ge=0),
            end_time: Optional[float] = Query(None, ge=0),
            key: Optional[str] = None,
            value: Optional[str] = None
        ):
            """
            Get messages from the database.

            This endpoint retrieves messages from the database based on the provided filters.

            Args:
                limit (int): The maximum number of messages to retrieve (default: 100, min: 1, max: 1000).
                start_time (float, optional): The start timestamp for filtering messages.
                end_time (float, optional): The end timestamp for filtering messages.
                key (str, optional): The key to filter messages by in the payload.
                value (str, optional): The value to filter messages by in the payload.

            Returns:
                dict: A dictionary containing the list of messages and the total count.

            Raises:
                HTTPException: If there's an error retrieving the messages.
            """
            try:
                messages = await self.packet_service.get_messages(limit, start_time, end_time, key, value)
                return {
                    "messages": [
                        {
                            "id": msg["id"],
                            "topic": msg["topic"],
                            "payload": json.loads(msg["payload"]),
                            "timestamp": datetime.fromtimestamp(msg["timestamp"], tz=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S')
                        } for msg in messages
                    ],
                    "total_count": len(messages)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) from e