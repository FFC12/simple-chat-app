import os
from motor import motor_asyncio
from loguru import logger
from traceback import print_exc


class Config:
    """
    Config class for database

    Attributes:
        MONGO_USERNAME: username for mongodb
        MONGO_PASSWORD: password for mongodb
        MONGO_DB: database name
        MONGO_HOST: host for mongodb
        MONGO_PORT: port for mongodb
        MONGO_URI: uri for mongodb

    """
    MONGO_USERNAME = os.getenv('MONGODB_USERNAME')
    MONGO_PASSWORD = os.getenv('MONGODB_PASSWORD')
    MONGO_DB = os.getenv('MONGODB_DB')
    MONGO_HOST = os.getenv('MONGODB_HOST')
    MONGO_PORT = os.getenv('MONGODB_PORT')
    
    MONGO_URI = f'mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin'

    # Client object to retrieve database instance (mongodb)
    _db_client = None

    @staticmethod
    def init_db() -> motor_asyncio.AsyncIOMotorDatabase:
        """
        Initialize database
        """
        try:
            db = Config._connect_db()
            logger.info('Connected to database')
        except Exception as e:
            logger.error(f'Cannot connect to database: {e}')
            # stacktrace
            print_exc()
            raise Exception(f'Cannot connect to database: {e}')

        return db

    @staticmethod
    def _connect_db():
        """
        Connect to database
        """
        client = motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)

        db_client = client[Config.MONGO_DB]
        return db_client

    @staticmethod
    def get_db():
        """
        Get database instance
        """
        if Config._db_client is None:
            Config._db_client = Config.init_db()
        return Config._db_client

