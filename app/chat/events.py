import asyncio
import json
from threading import Thread

from fastapi import Depends, Request

from app.core.base import sio
from app.core.redis import RedisManager
from app.db.config import Config
from app.core.security import AuthJWT

from loguru import logger

# get redis instance
redis = RedisManager.get_instance().get_redis()

# get database
db = Config.get_db()


@sio.event
async def connect(sid, environ):
    """
    Connect event
    :param sid:
    :param environ:
    :return:
    """
    logger.info(f'Client {sid} connected')

    # get headers
    cookies = environ['HTTP_COOKIE']

    # get JWT token 'Authorization Bearer <token>'
    cookies = cookies.split(';')

    # token, username and id
    token = 'null'
    username = 'null'
    id = 'null'

    # get token, username and id from cookies
    for cookie in cookies:
        # remove spaces
        cookie = cookie.strip()
        if cookie.startswith('access_token_cookie'):
            token = cookie.split('=')[1]
        elif cookie.startswith('username'):
            username = cookie.split('=')[1]
        elif cookie.startswith('id'):
            id = cookie.split('=')[1]

    # disconnect client if token, username or id is null
    if token == 'null' or username == 'null' or id == 'null':
        await sio.disconnect(sid)
        return

    # check if id matches with username
    collection = db['users']

    # get user
    user = await collection.find_one({'username': username})

    # disconnect client if user is not found
    if user is None:
        await sio.disconnect(sid)
        return

    # check if id matches
    if str(user['_id']) != id:
        await sio.disconnect(sid)
        return

    # verify token
    auth = AuthJWT()

    try:
        auth.jwt_required(auth_from='websocket', token=token)
    except Exception as e:
        logger.error(e)
        # disconnect client if token is invalid
        await sio.disconnect(sid)

    logger.info(f'Client {username} has connected successfully')

    # save session
    await sio.save_session(sid, {'username': username, 'id': id})


@sio.on("message")
async def message(sid, data):
    """
    Message event
    :param sid:
    :param data:
    :return:
    """
    session = await sio.get_session(sid)

    if session is None:
        # disconnect client if session is not found
        await sio.disconnect(sid)

    logger.info(f'Client {sid} sent message: {data}')

    target = data['target']
    username = data['username']
    text = data['message']
    timestamp = data['timestamp']

    data = {
        'sender': username,
        'to': target,
        'text': text,
        'timestamp': timestamp,
        'attachment': False
    }

    # private message
    if target != 'room':
        # get collection
        collection = db['users']

        # get user
        user = await collection.find_one({'username': target})

        # get user id
        user_id = str(user['_id'])

        # get user sid
        user_sid = redis.get(user_id)

        logger.info(f'User {target} sid: {user_sid}')

        # send private message
        await sio.emit('message', data, room=user_sid)
    #else:
    #    await sio.emit('message', data)


@sio.on("disconnect")
async def disconnect(sid):
    """
    Disconnect event
    :param sid:
    :return:
    """
    logger.info(f'Client {sid} disconnected')

    # remove user from online users
    redis.srem('online_users', sid)

    # session will be removed automatically

    # update online users
    await sio.emit('online_users', get_online_users())


@sio.on("online_users")
async def online_users(sid, data):
    """
    Online users event
    :param sid:
    :param data:
    :return:
    """
    logger.info(f'Client {sid} listen online users')

    # emit online users
    await sio.emit('online_users', get_online_users())


@sio.on("attachment")
async def attachment(sid, data):
    """
    Attachment event
    :param sid:
    :param data:
    :return:
    """
    logger.info(f'Client {sid} sent attachment: {data}')

    data = {
        'sender': sid,
        'text': data,
        'attachment': True,
        'warning': False,
    }

    data = check_data_type(data)
    
    # check data dict has image key
    if data['exist'] is False:
        data['text'] = 'This file format is not supported yet.'
        data['warning'] = True

    await sio.emit('message', data)


def check_data_type(data):
    # check if attachment is image
    if data['text'].endswith(('.png', '.jpg', '.jpeg', '.gif')):
        data['image'] = True
        data['exist'] = True

    # check if it is a video
    if data['text'].endswith(('.mp4', '.avi', '.mkv', '.mov')):
        data['video'] = True
        data['exist'] = False

    # check if it is a audio
    if data['text'].endswith(('.mp3', '.wav', '.ogg', '.flac')):
        data['audio'] = True
        data['exist'] = False

    # check if it is a document
    if data['text'].endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx')):
        data['document'] = True
        data['exist'] = False

    # check if it is a archive
    if data['text'].endswith(('.zip', '.rar', '.tar', '.gz', '.7z')):
        data['archive'] = True
        data['exist'] = False

    # check if it is a url
    if data['text'].startswith(('http://', 'https://')):
        # retrieve image from url if it is an image
        data['exist'] = True
        url = data['text']
        if url.endswith(('.png', '.jpg', '.jpeg', '.gif')):
            data['image'] = True
        else:
            # send request to url and get response
            import requests
            response = requests.get(url)

            # check if response is ok
            if response.status_code == 200:

                # check if response is an image
                if response.headers['content-type'].startswith(('image/png', 'image/jpeg', 'image/gif')):
                    data['image'] = True
                    data['url'] = True
                    data['image_data'] = response.content.decode('utf-8')

    return data


def get_online_users():
    # get online users
    users = redis.smembers('online_users')

    online_user_list = [str(user) for user in users]

    data = {
        'online_users': online_user_list
    }

    logger.info(f'Retrieved Online users: {data}')

    # data dict to json
    data = json.dumps(data)

    return data