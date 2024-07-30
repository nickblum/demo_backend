from typing import List, Optional
from server.database import Database
from server.mqtt_handler import MQTTHandler
from server.sse_handler import SSEHandler
from server.configuration import Settings
from server.logger import get_logger

logger = get_logger(__name__)

class MessageService:
    def __init__(self, db: Database, mqtt_handler: MQTTHandler, sse_handler: SSEHandler, settings: Settings):
        self.db = db
        self.mqtt_handler = mqtt_handler
        self.sse_handler = sse_handler
        self.settings = settings

    async def process_message(self, message):
        """Process a single message."""
        try:
            processed_data = self.process_payload(message['payload'])
            if self.should_publish_mqtt(processed_data):
                await self.mqtt_handler.publish(self.settings.MQTT_PUBLISH_TOPIC, processed_data)
            await self.sse_handler.send_event(processed_data)
            await self.db.mark_message_as_processed(message['id'])
        except Exception as e:
            logger.error("Error processing message: %s", str(e), extra={"message_id": message['id']})

    def process_payload(self, payload: str) -> dict:
        """Process the payload of a message."""
        # Implement your payload processing logic here
        # This is a placeholder implementation
        return {"processed": payload}

    def should_publish_mqtt(self, processed_data: dict) -> bool:
        """Determine if the processed data should be published via MQTT."""
        # Implement your logic to decide whether to publish via MQTT
        # This is a placeholder implementation
        return True

class PacketService:
    def __init__(self, db: Database, mqtt_handler: MQTTHandler):
        self.db = db
        self.mqtt_handler = mqtt_handler

    async def submit_packet(self, packet_data: dict) -> dict:
        """Submit a new packet."""
        # Implement your packet submission logic here
        # This is a placeholder implementation
        await self.mqtt_handler.publish("packet_topic", packet_data)
        return {"status": "submitted", "packet": packet_data}

    async def get_messages(
        self,
        limit: int = 100,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        key: Optional[str] = None,
        value: Optional[str] = None,
    ) -> List:
        
        """Get unprocessed messages."""
        messages = await self.db.get_messages(limit, start_time, end_time)
        
        if key and value:
            messages = [msg for msg in messages if key in msg['payload'] and msg['payload'][key] == value]

        return messages