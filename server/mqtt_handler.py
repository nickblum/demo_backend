import asyncio
import json
from queue import Queue
from paho.mqtt import client as mqtt_client
from server.configuration import Settings
from server.database import Database
from server.logger import get_logger

logger = get_logger(__name__)

class MQTTHandler:
    def __init__(self, settings: Settings, db: Database):
        self.settings = settings
        self.db = db
        self.client = None
        self.connected = False
        self.reconnect_interval = 1
        self.max_reconnect_interval = 60
        self.message_queue = Queue()
        self.processing_task = None
        self.reconnect_flag = asyncio.Event()

    async def connect(self):
        self.client = mqtt_client.Client()
        self.client.username_pw_set(self.settings.MQTT_USERNAME, self.settings.MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        await self.reconnect()

        self.processing_task = asyncio.create_task(self.process_messages())

    async def reconnect(self):
        while not self.connected:
            try:
                self.client.connect(self.settings.MQTT_BROKER, self.settings.MQTT_PORT)
                self.client.loop_start()
                await asyncio.sleep(1)  # Give time for the connection to establish
                if self.connected:
                    logger.info("Connected to MQTT broker")
                    await self.subscribe(self.settings.MQTT_SUBSCRIBE_TOPIC)
                    break
            except Exception as e:
                logger.error("Failed to connect to MQTT broker: %s", e)
                await asyncio.sleep(self.reconnect_interval)
                self.reconnect_interval = min(self.reconnect_interval * 2, self.max_reconnect_interval)

    async def process_messages(self):
        while True:
            try:
                message = await asyncio.get_event_loop().run_in_executor(None, self.message_queue.get)
                logger.info("Processing MQTT message: %s", message)
                topic, payload = message
                await self.handle_message(topic, payload)
            except Exception as e:
                logger.error("Error in message processing loop: %s", e)
                await asyncio.sleep(1)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
            self.reconnect_flag.set()
        else:
            logger.error("Failed to connect to MQTT broker with result code %s", rc)

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        logger.warning("Disconnected from MQTT broker")
        self.reconnect_flag.set()

    async def disconnect(self):
        if self.client:
            self.client.disconnect()
            self.client.loop_stop()
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        logger.info("Disconnected from MQTT broker")

    def on_message(self, client, userdata, msg):
        self.message_queue.put((msg.topic, msg.payload))

    async def handle_message(self, topic: str, payload: bytes):
        try:
            payload_str = payload.decode('utf-8')
            await self.db.insert_mqtt_message(topic, payload_str)
            logger.info("Received and stored MQTT message: %s", topic)
        except Exception as e:
            logger.error("Error handling MQTT message: %s", e)

    async def subscribe(self, topic: str):
        if self.connected:
            self.client.subscribe(topic)
            logger.info("Subscribed to topic: %s", topic)
        else:
            logger.warning("Cannot subscribe: Not connected to MQTT broker")

    async def publish(self, topic: str, payload: dict):
        if self.connected:
            try:
                json_payload = json.dumps(payload)
                self.client.publish(topic, json_payload)
                logger.info("Published message to topic: %s", topic)
            except Exception as e:
                logger.error("Error publishing MQTT message: %s", e)
        else:
            logger.warning("Cannot publish: Not connected to MQTT broker")

    def is_connected(self) -> bool:
        return self.connected

    async def maintain_connection(self):
        while True:
            await self.reconnect_flag.wait()
            self.reconnect_flag.clear()
            if not self.connected:
                await self.reconnect()
            await asyncio.sleep(1)