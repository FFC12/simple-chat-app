// Note: This script is used to handle the chat functionality quick-and-dirty *not safest way*

// get all cookies
var cookies = document.cookie.split(';');

// get the username from the cookie
var username = null;
var id = null;
var accessToken = null;

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

// Call this every 60 seconds to keep the online users list up-to-date
setInterval(function () {
    while (onlineUsersList.firstChild) {
        onlineUsersList.removeChild(onlineUsersList.firstChild);
    }
    socket.emit('online_users', {});
}, 60000);

// Elements and variables
var messageContainer = document.getElementById('message-container');
var messageForm = document.getElementById('message-form');
var inputMessage = document.getElementById('input-message');
var onlineUsersList = document.getElementById('online-users-list');
var currentSelectedFile = null;
var selectedUser = null;

// If message form is submitted send the message to the server
// If a file is selected, upload it to the server
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

    // Remove (+) from the element innerText
    selectedUser = element.innerText.replace('(+)', ' ');

    // Remove white spaces from the element innerText
    selectedUser = selectedUser.trim();

    // Select the clicked user
    element.classList.add('selected');

    // Show the message form
    var messageForm = document.getElementById('message-form');
    messageForm.style.display = 'block';

    // Get the message of the selected user from local storage if exists
    getMessages(selectedUser, (messages) => {
        for(var i = 0; i < messages.length; i++) {
            var message = messages[i];
            injectMessage(message);
        }
    });
}

// Validate the attachment size if it's bigger than 10 MB
// then show an error message
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

// Remove the attachment
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

function injectMessage(message) {
    data = message

    var messageElement = document.createElement('div');
    if(data.sender === username) {
        // add the message to the right
        messageElement.setAttribute('style', 'float: right; width: 100%; margin-bottom: 20px; text-align: right;');
        messageElement.classList.add('message');
        messageElement.innerHTML = '<strong style="color: blue; ">' + data.sender + ':</strong> ' + data.text;
    } else {
        // add the message to the left
        messageElement.setAttribute('style', 'float: left; width: 100%; margin-bottom: 20px; text-align: left;');
        messageElement.classList.add('message');
        messageElement.innerHTML = '<strong>' + data.sender + ':</strong> ' + data.text;
    }
    // append the message to the message container
    messageContainer.appendChild(messageElement);

    // add a space element
    var spaceElement = document.createElement('div');
    spaceElement.setAttribute('style', 'height: 20px;');
    messageContainer.appendChild(spaceElement);

    // scroll to the bottom of the message container
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

// HTTP request to get the messages from the server for the user
function requestMessages(username, func) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/messages/'+username, true);
    xhr.onload = function () {
        if(this.status === 200) {
            // save the messages to the local storage
            messages = JSON.parse(this.responseText);
            localStorage.setItem('messages', JSON.stringify(messages));
            func(messages);
        } else {
            console.log('Error: ' + this.status);
        }
    }
}

// get the messages from the server or local storage
function getMessages(username, fun) {
    // retrieve the last 100 messages from end point /messages
    if(localStorage.getItem('messages') === null) {
        // get the messages from the end point by XMLHttpRequest
        requestMessages(username, fun);
    } else {
        var messages = JSON.parse(localStorage.getItem('messages'));
        fun(messages[username]);
    }
}

// Message event to receive messages from server and inject them into the chat
socket.on('message', function (data) {
    console.log(data);

    // save the each incoming message to the messages array of sender
    // if the sender is not in the messages array, create a new array for him
    // if the sender is in the messages array, push the message to his array
    if(messages[data.sender] === undefined) {
        messages[data.sender] = [];
        messages[data.sender].push(data);
    } else {
        // it might be saved to the local storage already so check it
        if(localStorage.getItem('messages') !== null) {
            // it is saved to the local storage already so get it
            messages = JSON.parse(localStorage.getItem('messages'));

            // push the message to the messages array of sender
            messages[data.sender].push(data);
        } else {
            // it is not saved to the local storage yet
            messages[data.sender].push(data);

            // save the messages array to the local storage
            localStorage.setItem('messages', JSON.stringify(messages));
        }
    }

    // get all user-list-item elements
    var userItems = document.getElementsByClassName('user-list-item');

    // check if the message is from the selected user or not
    // if not, add a (+) to the user item
    // if yes, no need to add (+)
    for(var i = 0; i < userItems.length; i++) {
        if(userItems[i].innerText === data.sender
        && userItems[i].innerText !== selectedUser) {
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

    //TODO: Before injecting online users, check if has unread messages or not
    //TOOD: Before injecting online users, check if the user is logged in or not

    injectOnlineUsers(online_users);
});

// On disconnect event redirect to login page
socket.on('disconnect', function () {
    window.location.href = '/';
});