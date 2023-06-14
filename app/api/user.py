import json
import os
from uuid import uuid4
from hashlib import sha256

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Body, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from app.core.redis import RedisManager
from app.core.security import AuthJWT

from app.schemas.user import UserUpdate, UserDelete, UserRead

from app.db.config import Config

# user router
user_router = APIRouter()

# static files from root directory
templates = Jinja2Templates(directory='templates')

# get redis instance
redis = RedisManager.get_instance().get_redis()

# get database
db = Config.get_db()


@user_router.post("/login")
async def login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        Authorize: AuthJWT = Depends()):
    """
    Login endpoint for user

    :param request:
    :param password:
    :param username:
    :param Authorize:
    :return:
    """
    # get collection
    collection = db['users']

    # check if user exist
    result = await collection.find_one({'username': username})

    if result is None:
        return templates.TemplateResponse("index.html", {"request": request,
                                                         "error": "Username not found"})

    # hash password
    password = sha256(password.encode()).hexdigest()

    # check if password is correct
    if result['password'] != password:
        return templates.TemplateResponse("index.html", {"request": request,
                                                         "error": "Password is incorrect"})

    # Get id from user
    subject = {
        "id": str(result['_id']),
        "username": username
    }

    # Create access token
    access_token = Authorize.create_access_token(subject=json.dumps(subject))
    refresh_token = Authorize.create_refresh_token(subject=json.dumps(subject))

    logger.info(f'Client {username} connected')

    # Add user to online users
    add_online_user(username, subject['id'])

    # Redirect to chat page
    response = RedirectResponse(url='/chat', status_code=302)

    # Set username as a cookie
    response.set_cookie(key="username", value=username)
    response.set_cookie(key="id", value=subject['id'])

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token, response)
    Authorize.set_refresh_cookies(refresh_token, response)

    return response


@user_router.post("/register")
async def register(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        Authorize: AuthJWT = Depends()):
    """
    Register endpoint for user
    :param request:
    :param username:
    :param password:
    :param Authorize:
    :return:
    """
    # get collection
    collection = db['users']

    # check username length
    if len(username) < 3 or len(username) > 20:
        return templates.TemplateResponse("index.html", {"request": request,
                                                         "error": "Username must be between 3 and 20 characters"})

    # check if username is alphanumeric
    if not username.isalnum():
        return templates.TemplateResponse("index.html", {"request": request,
                                                         "error": "Username must be alphanumeric"})

    # check if user exist
    result = await collection.find_one({'username': username})

    if result is not None:
        return templates.TemplateResponse("index.html", {"request": request,
                                                         "error": "Username already exist"})

    # hash password
    password = sha256(password.encode()).hexdigest()

    # insert user
    user = await collection.insert_one({'username': username, 'password': password})

    # Get id from user
    subject = {
        "id": str(user.inserted_id),
        "username": username
    }

    logger.info(f'Client {subject} registered')

    # Create access token
    access_token = Authorize.create_access_token(subject=json.dumps(subject))
    refresh_token = Authorize.create_refresh_token(subject=json.dumps(subject))

    # Add user to online users
    add_online_user(username, subject['id'])

    # Redirect to chat page
    response = RedirectResponse(url='/chat', status_code=302)

    # Set username as a cookie
    response.set_cookie(key="username", value=username)

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token, response)
    Authorize.set_refresh_cookies(refresh_token, response)

    return response


@user_router.post("/update")
async def update(
        user: UserUpdate,
        Authorize: AuthJWT = Depends()):
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


@user_router.post("/logout")
async def logout(
        request: Request,
        Authorize: AuthJWT = Depends()
):
    """
    Logout endpoint for user
    :param request:
    :param Authorize:
    :return:
    """
    Authorize.jwt_required()

    response = templates.TemplateResponse("index.html", {"request": request, "message": "Logout successfully"})

    # Remove the JWT cookies from the response and set a new CSRF token in it's place
    Authorize.unset_jwt_cookies(response)

    payload = Authorize.get_jwt_subject()
    payload = json.loads(payload)

    username = payload['username']
    id = payload['id']

    # Remove user from online users
    remove_online_user(username, id)

    return response


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


def add_online_user(user, id):
    # add user to redis for online users
    if not redis.sismember('online_users', str(user)):
        redis.sadd('online_users', str(user))

    redis.hset(str(user), mapping={
        'id': id,
    })


def remove_online_user(user):
    """
    Remove user from online users
    :param user:
    :return:
    """
    # remove user from redis for online users
    if redis.sismember('online_users', str(user)):
        redis.srem('online_users', str(user))

    # remove user and id from user list in redis
    redis.delete(str(user))


def get_online_users():
        online_users = redis.smembers('online_users')

        online_user_list = []
        for user in online_users:
            online_user_list.append(str(user))

        data = {
            'online_users': online_user_list
        }

        return json.dumps(data)
