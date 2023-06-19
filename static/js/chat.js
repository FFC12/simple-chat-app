// Note: This script is used to handle the chat functionality quick-and-dirty *not safest way*


// get all cookies
var cookies = document.cookie.split(';');

// get the username from the cookie
var username = null;
var id = null;
var accessToken = null;

console.log('Cookies: ' + cookies);

for(var i = 0; i < cookies.length; i++) {
    var cookie = cookies[i].trim();
    if(cookie.startsWith('username')) {
        username = cookie.split('=')[1];
    } else if(cookie.startsWith('id')) {
        id = cookie.split('=')[1];
    } else if(cookie.startsWith('accessToken')) {
        accessToken = cookie.split('=')[1];
    }
}

// Connect to the socket.io server
const socket = io.connect('http://' + document.domain + ':' + location.port, {
    "path": "/ws/socket.io",
    "forceNew": true,
    "reconnectionAttempts": 3,
    "timeout": 2000,
    "transports": ["websocket", "polling", "flashsocket"],
    "query": "username=" + username + "&id=" + id,
    "headers": {
        'Authorization': 'Bearer ' + accessToken,
    }
});

socket.emit('online_users', {});

// Call this every 30 seconds to keep the connection alive
setInterval(function () {
    while (onlineUsersList.firstChild) {
        onlineUsersList.removeChild(onlineUsersList.firstChild);
    }
    socket.emit('online_users', {});
}, 60000);

var messageContainer = document.getElementById('message-container');
var messageForm = document.getElementById('message-form');
var inputMessage = document.getElementById('input-message');
var onlineUsersList = document.getElementById('online-users-list');
var currentSelectedFile = null;
var selectedUser = null;

messageForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var message = inputMessage.value.trim();
    console.log(message);

    if(currentSelectedFile == null) {
       if (message !== '') {
            message = {
                'target': selectedUser,
                'message': message,
                'username': username,
                'timestamp': new Date().toLocaleString()
            }
            socket.emit('message', message);
            inputMessage.value = '';
        }
    } else {
        // upload the file to the server as HTTP POST request
        var reader = new FileReader();
        reader.readAsDataURL(currentSelectedFile);
        reader.onload = function () {
            var base64 = reader.result.split(',')[1];

            var formData = new FormData();
            formData.append('file', base64);
            formData.append('filename', currentSelectedFile.name);
            formData.append('filesize', currentSelectedFile.size);
            formData.append('filetype', currentSelectedFile.type);

            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload', true);
            xhr.onload = function () {
                if (this.status === 200) {
                    console.log('File uploaded successfully');
                } else {
                    console.log('File upload failed');
                }
            }
            currentSelectedFile = null;
        }
    }
});

function selectUser(element) {
    // Remove the 'selected' class from all users
    var userItems = document.getElementsByClassName('user-list-item');
    for (var i = 0; i < userItems.length; i++) {
        userItems[i].classList.remove('selected');
    }

    console.log("Selected user: " + element.innerText); // DEBUG
    selectedUser = element.innerText;

    // Select the clicked user
    element.classList.add('selected');

    // Show the message form
    var messageForm = document.getElementById('message-form');
    messageForm.style.display = 'block';
}

function validateAttachment(input) {
    const file = input.files[0];
    const maxSize = 10 * 1024 * 1024; // 10 MB
    const errorElement = document.getElementById('attachment-size-error');

    if (file.size > maxSize) {
        errorElement.style.display = 'block';
        input.value = ''; // Clear the selected file
    } else {
        errorElement.style.display = 'none';
        // add the file to the message
        var message = inputMessage.value.trim();
        message += ' ' + file.name;
        inputMessage.value = message;
        // focus the message input
        inputMessage.focus();
        // disable the message input
        inputMessage.disabled = true;

        // put a red button to the right of the message input to remove the attachment
        var button = document.createElement('button');
        button.classList.add('btn', 'btn-danger', 'btn-sm', 'ml-2');
        button.setAttribute('onclick', 'removeAttachment(this)');
        button.innerHTML = '<i class="fas fa-times"></i>';
        inputMessage.parentNode.appendChild(button);

        // disable input button
        input.disabled = true;

        // save the file
        currentSelectedFile = file;
    }
}

function removeAttachment(element) {
    // remove the cross icon
    element.parentNode.removeChild(element);
    // enable the message input
    inputMessage.disabled = false;
    // clear the message input
    inputMessage.value = '';

    // enable the attachment input
    var attachmentInput = document.getElementById('attachment-input');
    attachmentInput.disabled = false;

    // clear the attachment input
    attachmentInput.value = '';

    // clear the current selected file
    currentSelectedFile = null;
}

// HTML injection for online users
injectOnlineUsers = function (online_users) {
    // remove all 'li' elements
    if(onlineUsersList !== null) {
        while (onlineUsersList.firstChild) {
            onlineUsersList.removeChild(onlineUsersList.firstChild);
        }
    }

    for (var i = 0; i < online_users.length; i++) {
        var listItem = document.createElement('li');
        listItem.classList.add('user-list-item');

        if (online_users[i] !== username) {
            listItem.setAttribute('onclick', 'selectUser(this)');

            // add another element inside the 'li' element
            var spanItem = document.createElement('span');
            spanItem.classList.add('online-icon');
            listItem.appendChild(spanItem);

            listItem.innerText = online_users[i];
            onlineUsersList.appendChild(listItem);
        } else {
            // add another element inside the 'li' element
            var spanItem = document.createElement('span');
            spanItem.classList.add('online-icon');

            // make it strong
            var strongItem = document.createElement('strong');
            strongItem.innerText = online_users[i] + ' (You)';
            listItem.appendChild(strongItem);

            onlineUsersList.appendChild(listItem);
        }
    }
}

// Message event to receive messages from server and inject them into the chat
socket.on('message', function (data) {
    console.log(data);


    var messageElement = document.createElement('div');
    if(data.sender === username) {
        // float the message to the right add the style attribute
        messageElement.setAttribute('style', 'float: right;');
        messageElement.classList.add('message');
        messageElement.innerHTML = '<strong style="color: blue; ">' + data.sender + ':</strong> ' + data.text;
    } else {
        messageElement.classList.add('message');
        messageElement.innerHTML = '<strong>' + data.sender + ':</strong> ' + data.text;
    }
    messageContainer.appendChild(messageElement);
    messageContainer.scrollTop = messageContainer.scrollHeight;

    // get all user-list-item elements
    var userItems = document.getElementsByClassName('user-list-item');

    for(var i = 0; i < userItems.length; i++) {
        if(userItems[i].innerText === data.sender) {
            console.log('New message from ' + userItems[i].innerText)
            userItems[i].classList.add('new-message');
            // also add text to the user item inner text
            userItems[i].innerText += ' (+)';

        }
    }
});

// Online users event to receive online users from server and inject them into the chat
socket.on('online_users', function (data) {
    // parse data to JSON
    data = JSON.parse(data);

    online_users = data['online_users'];

    injectOnlineUsers(online_users);
});

// On disconnect event redirect to login page
socket.on('disconnect', function () {
    window.location.href = '/';
});