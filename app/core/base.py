import socketio
from fastapi import FastAPI

# get ip address of docker container
import socket


def get_ip_address():
    """
    Get ip address of docker container
    :return:
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("google.com", 80))
    ip_address = s.getsockname()[0]
    s.close()
    return ip_address


ip = get_ip_address()

# SocketIO manager instance
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=['*',
                                                                    f'http://{ip}:8000',
                                                                    'http://localhost:8000'])

# FastAPI instance
app = FastAPI()

# SocketIO app
asgi = socketio.ASGIApp(sio)


