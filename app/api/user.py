import json
import os
from uuid import uuid4
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from loguru import logger

from app.core.redis import RedisManager
from app.core.security import AuthJWT

from app.schemas.user import UserCreate, UserUpdate, UserDelete, UserLogin, UserRead

from app.db.config import Config

user_router = APIRouter()

redis = RedisManager.get_instance().get_redis()

db = Config.get_db()


@user_router.post("/login")
async def login(user: UserLogin, Authorize: AuthJWT = Depends()):
    """
    Login endpoint for user
    :param user:
    :param passw:
    :param Authorize:
    :return:
    """
    # get collection
    collection = db['users']

    # check if user exist
    result = await collection.find_one({'username': user.username})

    if result is None:
        return HTTPException(status_code=401, detail="User not found")

    # hash password
    password = sha256(user.password.encode()).hexdigest()

    # check if password is correct
    if result['password'] != password:
        return HTTPException(status_code=401, detail="Wrong password")

    # Get id from user
    subject = result['_id']

    # Create access token
    create_access_token(Authorize, subject)

    logger.info(f'Client {user.username} connected')

    # Add user to online users
    add_online_user(user.username)

    return HTTPException(status_code=200, detail=get_online_users())


@user_router.post("/register")
async def register(user: UserCreate,  Authorize: AuthJWT = Depends()):
    """
    Register endpoint for user
    :param user:
    :param passw:
    :return:
    """
    # get collection
    collection = db['users']

    # check if user exist
    result = await collection.find_one({'username': user.username})

    if result is not None:
        return HTTPException(status_code=401, detail="Username already exist")

    # hash password
    password = sha256(user.password.encode()).hexdigest()

    # insert user
    user = await collection.insert_one({'username': user.username, 'password': password})

    # Get id from user
    user_id = user.inserted_id

    # Create access token
    create_access_token(Authorize, user_id)

    return HTTPException(status_code=200, detail="Register successfully")


@user_router.post("/update")
async def update(user: UserUpdate, Authorize: AuthJWT = Depends()):
    """
    Update endpoint for user
    :param user:
    :param passw:
    :param Authorize:
    :return:
    """
    Authorize.jwt_required()

    # get collection
    collection = db['users']

    # check if user exist
    result = await collection.find_one({'username': user.username})

    if result is None:
        return HTTPException(status_code=401, detail="User not found")

    # check if password is correct
    if result['password'] != user.password:
        return HTTPException(status_code=401, detail="Wrong password")

    # hash new password
    new_password = sha256(user.password.encode()).hexdigest()

    # update user
    await collection.update_one({'username': user.username}, {'$set': {'password': new_password}})

    return HTTPException(status_code=200, detail="Update successfully")


@user_router.delete("/logout")
async def logout(Authorize: AuthJWT = Depends()):
    """
    Logout endpoint for user
    :param Authorize:
    :return:
    """
    Authorize.jwt_required()

    # Remove the JWT cookies from the response and set a new CSRF token in it's place
    Authorize.unset_jwt_cookies()

    # Remove user from online users
    remove_online_user(Authorize.get_jwt_subject())

    return HTTPException(status_code=200, detail="Logout successfully")


@user_router.post("/refresh")
async def refresh(Authorize: AuthJWT = Depends()):
    """
    Refresh endpoint for user
    :param Authorize:
    :return:
    """
    Authorize.jwt_refresh_token_required()

    # Create the new access token
    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)

    # Set the JWT access cookie in the response
    Authorize.set_access_cookies(new_access_token)

    return HTTPException(status_code=200, detail="Refresh successfully")


# file upload endpoint from data form
@user_router.post("/upload")
async def upload(file: UploadFile = File(...), Authorize: AuthJWT = Depends()):
    """
    Upload endpoint for user
    :param file:
    :param Authorize:
    :return:
    """
    # check if folder exist
    if not os.path.exists('upload'):
        os.makedirs('upload')

    filename = str(uuid4())
    file.filename = f"{filename}.jpg"

    # full path of file
    file_path = f"upload/{file.filename}"

    # save file
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    # save the data to database
    collection = db['files']

    await collection.insert_one({
        'filename': file_path,
        'user': Authorize.get_jwt_subject()
    })

    return HTTPException(status_code=200, detail="Upload successfully")


# a protected endpoint which requires a valid access token for access
@user_router.get("/test_protected")
async def protected(Authorize: AuthJWT = Depends()):
    """
    Protected endpoint for user
    :param Authorize:
    :return:
    """
    Authorize.jwt_required()

    # Access the identity of the current user with get_jwt_identity
    current_user = Authorize.get_jwt_subject()

    return HTTPException(status_code=200, detail=f"Welcome {current_user}")


# -- helper functions --
def add_online_user(user):
    # add user to redis for online users
    if not redis.sismember('online_users', user):
        redis.sadd('online_users', str(user))


def remove_online_user(user):
    """
    Remove user from online users
    :param user:
    :return:
    """
    # Remove user from online users
    redis.srem('online_users', user)


def get_online_users():
    # broadcast online users
    online_users = redis.smembers('online_users')

    online_user_list = []
    for user in online_users:
        online_user_list.append(str(user))

    data = {
        'online_users': online_user_list
    }

    return json.dumps(data)


def create_access_token(auth, subject):
    # Create the tokens and passing to set_access_cookies or set_refresh_cookies
    access_token = auth.create_access_token(subject=subject)
    refresh_token = auth.create_refresh_token(subject=subject)

    # Set the JWT cookies in the response
    auth.set_access_cookies(access_token)
    auth.set_refresh_cookies(refresh_token)