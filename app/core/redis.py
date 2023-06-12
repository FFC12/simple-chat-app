import os

from redis import Redis
from loguru import logger


class RedisManager:
    """
    It's a simple wrapper for redis client.
    It's using singleton pattern to create only one instance of RedisManager
    and Redis object (redis client).

    Here is an example of how to use it:
        redis_manager = RedisManager(host=redis_host, port=redis_port)
        redis_manager.set_data('foo', 'bar')
        print(redis_manager.get_data('foo'))
        redis_manager.delete_data('foo')

    """

    # Singleton instance
    _instance = None

    # Redis client
    _client = None

    def __new__(cls, host=None, port=None, *args, **kwargs):
        """
        Singleton pattern to create only one instance of redis client

        :param cls:
        :param host:
        :param port:
        :param args:
        :param kwargs:
        :return:
        """
        if not cls._instance:
            cls._instance = super(RedisManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, host=None, port=None, *args, **kwargs):
        """
        Initialize redis manager
        :param host:
        :param port:
        :param args:
        :param kwargs:
        """
        super(RedisManager, self).__init__(*args, **kwargs)

        if host is None:
            host = 'redis'
            logger.warning('Redis host is not set. Using default value: localhost')
        if port is None:
            port = 6379
            logger.warning('Redis port is not set. Using default value: 6379')

        self.host = host
        self.port = port

        # Get redis client (create if it's not created yet)
        self.get_redis()

    @staticmethod
    def get_instance():
        """
        Get redis manager instance
        :return:
        """
        if RedisManager._instance is None:
            logger.error('RedisManager is not initialized')
            raise Exception('RedisManager is not initialized')

        return RedisManager._instance

    def get_redis(self):
        """
        Get redis instance
        :return:
        """
        if not self.host or not self.port:
            logger.error('Redis host and port must be set')
            raise Exception('Redis host and port must be set')

        # Create redis client if it's not created yet
        if RedisManager._client is None:
            try:
                RedisManager._client = Redis(host=self.host, port=self.port, decode_responses=True)
            except Exception as e:
                logger.error(f'Could not connect to redis server: {e}')
                raise Exception(f'Could not connect to redis server: {e}')
            finally:
                logger.info(f'Connected to redis server: {self.host}:{self.port}')

        return RedisManager._client

    def get_redis_url(self):
        """
        Get redis url
        :return:
        """
        return f'redis://{self.host}:{self.port}'


# Initialize the redis
RedisManager(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'))
