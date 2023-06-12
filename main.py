"""
This project is a simple chat application using FastAPI and SocketIO as
backend and using MongoDB as database to store chat history and user data.
Redis is used to store user session data. The application is deployed using
Docker and docker-compose. The application is deployed to Heroku.

Also, this API is using by mobile application. You can check it out
from here: ![chat-app-mobile](github.com/ffc12/chat-app-mobile)

- Author
    FFC12 (fatihsaika@gmail.com) - ![ffc12](github.com/ffc12)

- License
    MIT License

"""
import os

from fastapi import Request, HTTPException

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.redis import RedisManager
from app.core.base import app, asgi, sio
from app.db.config import Config

from app.api.user import user_router
from app.api.room import room_router
from app.chat.events import connect, message, online_users, disconnect

from loguru import logger

# static files from root directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# templates from root directory
templates = Jinja2Templates(directory='templates')

# Mount the SocketIO to Fastapi app
app.mount("/ws", asgi)

# Include routers
app.include_router(user_router, prefix='/api/v1/user', tags=['user'])
app.include_router(room_router, prefix='/api/v1/room', tags=['room'])


@app.on_event("startup")
async def startup_event():
    """
    Startup event
    :return:
    """
    logger.info('🚀 The application is starting up...')

    # Initialize the database
    Config.init_db()


@app.get("/")
async def root():
    """
    Root page
    :return:
    """
    return {"message": "Hello World"}


@app.get("/chat")
async def index(request: Request):
    """
    chat.html page
    :return:
    """

    # Retrieve the last 100 messages from database
    messages = [
        {"sender": "System Message", "text": "Welcome to the Yet Another Simple Chat App!", 'attachment': False},
    ]

    return templates.TemplateResponse("chat.html", {"request": request, "messages": messages})


"""
@app.sio.on("join")
async def join(sid, *args, **kwargs):
    await app.sio.emit('lobby', 'user joined')



async def get_user(db):
    collection = db['chat']
    user = {
        'name': 'John Doe',
        'email': 'asdas'
    }
    result = await collection.insert_one(user)
    logger.debug(f'Insert user: {result.inserted_id}')

    # get user
    user = await collection.find_one({'_id': result.inserted_id})
    print(user)


async def main():
    redis_host = os.getenv('REDIS_HOST')
    redis_port = os.getenv('REDIS_PORT')
    redis_manager = RedisManager(host=redis_host, port=redis_port)
    redis = redis_manager.get_redis()
    redis.set('foo', 'bar')
    redis_manager.set_data('foo', 'bar')
    print(redis.get('foo'))

    db = Config.init_db()
    await get_user(db)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
"""