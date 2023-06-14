"""
This project is a simple chat application using FastAPI and SocketIO as
backend and using MongoDB as database to store chat history and user data.
Redis is used to store user session data.

- Author
    FFC12 (fatihsaika@gmail.com) - ![ffc12](github.com/ffc12)

- License
    MIT License

"""
import json

from fastapi import Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.base import app, asgi
from app.core.security import AuthJWT

from app.core.redis import RedisManager

# they need to be imported to register events (otherwise they won't be registered and won't work)
from app.chat.events import message, connect, disconnect, online_users

from app.db.config import Config

from app.api.user import user_router, get_online_users
from app.api.room import room_router

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

# get redis instance
redis = RedisManager.get_instance().get_redis()


@app.on_event("startup")
async def startup_event():
    """
    Startup event
    :return:
    """
    logger.info('🚀 The application is starting up...')

    # Initialize the database
    Config.init_db()

    # Clear all redis keys (for development)
    redis.flushall()


@app.get("/chat")
async def chat(
        request: Request,
        Authorize: AuthJWT = Depends()
):
    """
    chat.html page

    :param request:
    :param Authorize:
    :return:
    """
    Authorize.jwt_required()
    # TODO: Retrieve the last 100 messages from database for 'room' or 'user'

    messages = [
        {"sender": "System Message", "text": "Welcome to the Yet Another Simple Chat App!", 'attachment': False},
    ]

    # Get payload
    payload = Authorize.get_jwt_subject()

    # Convert payload to json
    payload = json.loads(payload)

    # Get username and id
    username = payload['username']
    id = payload['id']

    # Get online users
    online_users = get_online_users()

    return templates.TemplateResponse("chat.html", {"request": request,
                                                    "messages": messages,
                                                    "username": username,
                                                    "id": id,
                                                    "online_users": online_users})


@app.get("/")
async def index(
        request: Request,
        Authorize: AuthJWT = Depends()
):
    """
    index.html page

    :param request:
    :param Authorize:
    :return:
    """
    if not request.cookies.get('token'):
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        # Get username from token
        username = Authorize.get_jwt_subject()

        # redirect to chat page
        return templates.TemplateResponse("chat.html", {"request": request,
                                                        "username": username})
