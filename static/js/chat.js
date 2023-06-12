// Note: This script is used to handle the chat functionality quick-and-dirty *not safest way*

// Connect to the socket.io server
const socket = io.connect('http://' + document.domain + ':' + location.port, {
    "path": "/ws/socket.io",
    "forceNew": true,
    "reconnectionAttempts": 3,
    "timeout": 2000,
    "transports": ["websocket", "polling", "flashsocket"]
});

// Call on page initialization
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

messageForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var message = inputMessage.value.trim();
    console.log(message);
    if (message !== '') {
        if(currentSelectedFile === null) {
            socket.emit('message', message);
            inputMessage.value = '';
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
    }
});

function selectUser(element) {
    // Remove the 'selected' class from all users
    var userItems = document.getElementsByClassName('user-list-item');
    for (var i = 0; i < userItems.length; i++) {
        userItems[i].classList.remove('selected');
    }

    console.log("Selected user: " + element.innerText); // DEBUG

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
        listItem.setAttribute('onclick', 'selectUser(this)');

        // add another element inside the 'li' element
        var spanItem = document.createElement('span');
        spanItem.classList.add('online-icon');
        listItem.appendChild(spanItem);

        listItem.innerText = online_users[i];
        onlineUsersList.appendChild(listItem);
    }
}

// Message event to receive messages from server and inject them into the chat
socket.on('message', function (data) {
    var messageElement = document.createElement('div');
    messageElement.classList.add('message');
    messageElement.innerHTML = '<strong>' + data.sender + ':</strong> ' + data.text;
    messageContainer.appendChild(messageElement);
    messageContainer.scrollTop = messageContainer.scrollHeight;
});

// Online users event to receive online users from server and inject them into the chat
socket.on('online_users', function (data) {
    // parse data to JSON
    data = JSON.parse(data);

    online_users = data['online_users'];

    injectOnlineUsers(online_users);
});