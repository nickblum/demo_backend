"""
This module contains the MessageProcessor class, 
which is responsible for processing messages from the database.
"""
import asyncio
import json
from server.configuration import Settings
from server.database import Database
from server.mqtt_handler import MQTTHandler
from server.sse_handler import SSEHandler
from server.logger import get_logger

logger = get_logger(__name__)

class MessageProcessor:
    def __init__(self, settings: Settings, db: Database, mqtt_handler: MQTTHandler, sse_handler: SSEHandler):
        self.settings = settings
        self.db = db
        self.mqtt_handler = mqtt_handler
        self.sse_handler = sse_handler

    async def process_messages(self):
        while True:
            try:
                messages = await self.db.get_unprocessed_messages()
                logger.info(messages)
                for message in messages:
                    await self.process_message(message)
                await asyncio.sleep(self.settings.MESSAGE_PROCESSING_INTERVAL)
            except Exception as e:
                logger.error("Error in message processing loop: %s", e)
                await asyncio.sleep(5)  # Wait a bit before retrying

    async def process_message(self, message):
        try:
            payload = json.loads(message['payload'])
            processed_data = self.process_payload(payload)

            # Send processed data via SSE
            await self.sse_handler.send_event(processed_data)

            # Publish processed data to MQTT if needed
            if self.should_publish_mqtt(processed_data):
                await self.mqtt_handler.publish(self.settings.MQTT_PUBLISH_TOPIC, processed_data)

            # Mark message as processed
            await self.db.mark_message_as_processed(message['id'])

            logger.info("Processed message %s", message['id'])
        except json.JSONDecodeError:
            logger.error("Invalid JSON in message %s", message['id'])
        except Exception as e:
            logger.error("Error processing message %s: %s", message['id'], e)

    def process_payload(self, payload):
        # This is where you would implement your business logic
        # For now, we'll just pass through the payload
        return payload

    def should_publish_mqtt(self, processed_data):
        # Implement your logic to decide if the processed data should be published via MQTT
        # For now, we'll always return True
        return True