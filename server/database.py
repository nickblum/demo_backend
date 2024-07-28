# import asyncio
import aiosqlite
import asyncpg
from server.configuration import Settings
from server.logger import get_logger

logger = get_logger(__name__)

class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pool = None
        self.sqlite_conn = None

    async def connect(self):
        if self.settings.DB_TYPE == 'sqlite':
            try:
                self.sqlite_conn = await aiosqlite.connect(self.settings.DB_NAME)
                await self.sqlite_conn.execute("PRAGMA journal_mode=WAL")
                logger.info("SQLite database connection established")
            except Exception as e:
                logger.error(f"Error connecting to SQLite database: {e}")
                raise
        else:  # PostgreSQL
            try:
                self.pool = await asyncpg.create_pool(
                    host=self.settings.DB_HOST,
                    port=self.settings.DB_PORT,
                    user=self.settings.DB_USER,
                    password=self.settings.DB_PASSWORD,
                    database=self.settings.DB_NAME,
                    min_size=5,
                    max_size=20
                )
                logger.info("PostgreSQL database connection pool created")
            except Exception as e:
                logger.error(f"Error creating PostgreSQL database connection pool: {e}")
                raise

    async def disconnect(self):
        if self.settings.DB_TYPE == 'sqlite':
            if self.sqlite_conn:
                await self.sqlite_conn.close()
                logger.info("SQLite database connection closed")
        else:
            if self.pool:
                await self.pool.close()
                logger.info("PostgreSQL database connection pool closed")

    async def execute(self, query: str, *args):
        if self.settings.DB_TYPE == 'sqlite':
            if not self.sqlite_conn:
                raise Exception("SQLite database connection not established")
            try:
                async with self.sqlite_conn.execute(query, args) as cursor:
                    await self.sqlite_conn.commit()
                    return cursor.rowcount
            except Exception as e:
                logger.error(f"Error executing SQLite database query: {e}")
                raise
        else:
            if not self.pool:
                raise Exception("PostgreSQL database connection not established")
            try:
                async with self.pool.acquire() as conn:
                    return await conn.execute(query, *args)
            except Exception as e:
                logger.error(f"Error executing PostgreSQL database query: {e}")
                raise

    async def fetch(self, query: str, *args):
        if self.settings.DB_TYPE == 'sqlite':
            if not self.sqlite_conn:
                raise Exception("SQLite database connection not established")
            try:
                async with self.sqlite_conn.execute(query, args) as cursor:
                    rows = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    dict_results = [dict(zip(columns, row)) for row in rows]
                    return dict_results
            except Exception as e:
                logger.error(f"Error fetching data from SQLite database: {e}")
                raise
        else:
            if not self.pool:
                raise Exception("PostgreSQL database connection not established")
            try:
                async with self.pool.acquire() as conn:
                    return await conn.fetch(query, *args)
            except Exception as e:
                logger.error(f"Error fetching data from PostgreSQL database: {e}")
                raise

    async def fetchrow(self, query: str, *args):
        if self.settings.DB_TYPE == 'sqlite':
            if not self.sqlite_conn:
                raise Exception("SQLite database connection not established")
            try:
                async with self.sqlite_conn.execute(query, args) as cursor:
                    return await cursor.fetchone()
            except Exception as e:
                logger.error(f"Error fetching row from SQLite database: {e}")
                raise
        else:
            if not self.pool:
                raise Exception("PostgreSQL database connection not established")
            try:
                async with self.pool.acquire() as conn:
                    return await conn.fetchrow(query, *args)
            except Exception as e:
                logger.error(f"Error fetching row from PostgreSQL database: {e}")
                raise

    async def insert_mqtt_message(self, topic: str, payload: str, timestamp: float):
        if self.settings.DB_TYPE == 'sqlite':
            query = """
            INSERT INTO mqtt_messages (topic, payload, timestamp)
            VALUES (?, ?, ?)
            """
            cursor = await self.sqlite_conn.execute(query, (topic, payload, timestamp))
            await self.sqlite_conn.commit()
            return cursor.lastrowid
        else:
            query = """
            INSERT INTO mqtt_messages (topic, payload, timestamp)
            VALUES ($1, $2, $3)
            RETURNING id
            """
            return await self.fetchrow(query, topic, payload, timestamp)

    async def get_unprocessed_messages(self, limit: int = 100):
        query = """
        SELECT id, topic, payload, timestamp
        FROM mqtt_messages
        WHERE processed = FALSE
        ORDER BY timestamp ASC
        LIMIT ?
        """
        if self.settings.DB_TYPE != 'sqlite':
            query = query.replace('?', '$1')

        return await self.fetch(query, limit)

    async def mark_message_as_processed(self, message_id: int):
        query = """
        UPDATE mqtt_messages
        SET processed = TRUE
        WHERE id = ?
        """
        if self.settings.DB_TYPE != 'sqlite':
            query = query.replace('?', '$1')
        await self.execute(query, message_id)

    async def initialize_database(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS mqtt_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            payload TEXT NOT NULL,
            timestamp REAL NOT NULL,
            processed BOOLEAN DEFAULT FALSE
        );
        """
        if self.settings.DB_TYPE != 'sqlite':
            create_table_query = create_table_query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            create_table_query = create_table_query.replace('REAL', 'DOUBLE PRECISION')
        await self.execute(create_table_query)
        logger.info("Database initialized")