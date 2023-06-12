## Simple Chat Application

This project is a simple chat application developed using Python 3.11. It is built with FastAPI, MongoDB, Redis, and Socket.io. Users can register and log in to the application, allowing them to privately message each other through the user-friendly interface. Online users are displayed in real-time. The backend flow is managed using Docker and docker-compose. The application is deployed on Heroku.

#### Key Features:

* User registration and login functionality
* User authentication using JWT (JSON Web Tokens)
* Secure password hashing for user accounts
* Storage of user chat data in MongoDB for chat history
* User session management using Redis for efficient handling of user sessions
* Automatic expiry of user sessions for enhanced security
* User session logout feature
* User session refresh for extending session duration
* Private messaging capability between users
* Real-time sending and receiving of messages
* Real-time sending and receiving of pictures
* Real-time sending and receiving of emojis
* Real-time sending and receiving of videos (to be implemented)
* Real-time sending and receiving of files (to be implemented)
* Display of online users in the chat application
* Indication of unread messages for improved user experience
* Display of the last message exchanged between users
* Display of the timestamp of the last message

To test the application: 
https://simple-chat-app-fastapi.herokuapp.com/