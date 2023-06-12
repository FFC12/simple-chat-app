import asyncio
import json
from threading import Thread

from app.core.base import sio
from app.core.redis import RedisManager

from loguru import logger

redis = RedisManager.get_instance().get_redis()


@sio.on("connect")
async def connect(sid, environ):
    """
    Connect event
    :param sid:
    :param environ:
    :return:
    """
    logger.info(f'Client {sid} connected')
    await sio.emit('lobby', 'user joined')


@sio.on("message")
async def message(sid, data):
    """
    Message event
    :param sid:
    :param data:
    :return:
    """
    logger.info(f'Client {sid} sent message: {data}')

    data = {
        'sender': sid,
        'text': data,
        'attachment': False
    }

    await sio.emit('message', data)


@sio.on("disconnect")
async def disconnect(sid):
    """
    Disconnect event
    :param sid:
    :return:
    """
    logger.info(f'Client {sid} disconnected')


@sio.on("online_users")
async def online_users(sid, data):
    """
    Online users event
    :param sid:
    :param data:
    :return:
    """
    logger.info(f'Client {sid} listen online users')

    # get online users
    online_users = redis.smembers('online_users')

    online_user_list = []
    for user in online_users:
        online_user_list.append(str(user))

    data = {
        'online_users': online_user_list
    }

    # data dict to json
    data = json.dumps(data)

    # emit online users
    await sio.emit('online_users', data)


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
