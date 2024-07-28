""" REST API handler for the server. """
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ValidationError
from server.configuration import Settings
from server.database import Database
from server.mqtt_handler import MQTTHandler
import json

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
        self.setup_routes()

    def setup_routes(self):
        @self.router.post("/api/v1/packets", status_code=201)
        async def submit_packet(packet: Packet):
            try:
                # Validate packet against schema
                packet_dict = packet.dict()

                # Store in database
                timestamp = datetime.utcnow().timestamp()
                message_id = await self.db.insert_mqtt_message(
                    self.settings.MQTT_PUBLISH_TOPIC,
                    json.dumps(packet_dict),
                    timestamp
                )

                # Publish to MQTT
                await self.mqtt_handler.publish(self.settings.MQTT_PUBLISH_TOPIC, packet_dict)

                return {"message": "Packet submitted successfully", "id": message_id}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/ping")
        async def ping():
            return {
                "status": "OK",
                "timestamp": datetime.utcnow().isoformat()
            }

        @self.router.get("/rereadenv")
        async def reread_env():
            try:
                self.settings = Settings()
                return {"message": "Environment variables updated successfully"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to update environment variables: {str(e)}")

        @self.router.get("/api/v1/messages")
        async def get_messages(
            limit: int = Query(100, ge=1, le=1000),
            start_time: Optional[float] = Query(None, ge=0),
            end_time: Optional[float] = Query(None, ge=0),
            key: Optional[str] = None,
            value: Optional[str] = None
        ):
            try:
                query = """
                SELECT id, topic, payload, timestamp
                FROM mqtt_messages
                WHERE 1=1
                """
                params = []

                if start_time is not None:
                    query += " AND timestamp >= $1"
                    params.append(start_time)

                if end_time is not None:
                    query += f" AND timestamp <= ${len(params) + 1}"
                    params.append(end_time)

                if key is not None and value is not None:
                    query += f" AND payload::jsonb ->> ${len(params) + 1} = ${len(params) + 2}"
                    params.extend([key, value])

                query += f" ORDER BY timestamp DESC LIMIT ${len(params) + 1}"
                params.append(limit)

                messages = await self.db.fetch(query, *params)
                
                return {
                    "messages": [
                        {
                            "id": msg["id"],
                            "topic": msg["topic"],
                            "payload": json.loads(msg["payload"]),
                            "timestamp": msg["timestamp"]
                        } for msg in messages
                    ],
                    "total_count": len(messages)
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))