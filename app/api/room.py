from fastapi import APIRouter, Depends, HTTPException
from app.db.config import Config
from app.core.redis import RedisManager
from app.core.security import AuthJWT

from uuid import uuid4
import datetime
import json

from loguru import logger

room_router = APIRouter()

client = Config.get_db()

redis = RedisManager.get_instance().get_redis()


# create room by using redis
@room_router.post("/create")
async def create(name: str, has_key: bool = False, Authorize: AuthJWT = Depends()):
    """
    Create room endpoint for user
    :param name:
    :param Authorize:
    :return:
    """
    Authorize.jwt_required()

    # Create user list for room (in the beginning, only creator in the room)
    user_list = [Authorize.get_jwt_subject()]
    user_list = json.dumps(user_list)

    uuid = uuid4()
    room_data = {
        "id": str(uuid),
        "room": str(name),
        "has_key": 1 if has_key else 0,
        "secret_key": str(uuid4().hex) if has_key else None,
        "created_by": Authorize.get_jwt_subject(),
        "user_list": user_list,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    logger.info(room_data)

    # Create room
    room_key = f'room:{uuid}'
    result = redis.hmset(room_key, room_data)

    # Log the result
    logger.info(result)

    return HTTPException(status_code=200, detail=room_data)


@room_router.post("/list")
async def list_rooms(Authorize: AuthJWT = Depends()):
    """
    List rooms endpoint for user
    :param Authorize:
    :return:
    """
    Authorize.jwt_required()

    # List rooms
    rooms = []
    for key in redis.scan_iter("room:*"):
        room = redis.hgetall(key)
        rooms.append(room)

    return HTTPException(status_code=200, detail=rooms)
