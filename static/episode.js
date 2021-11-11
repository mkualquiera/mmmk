comment_field = document.getElementById('comment');

var getJSON = function(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'json';
    xhr.onload = function() {
      var status = xhr.status;
      if (status === 200) {
        callback(null, xhr.response);
      } else {
        callback(status, xhr.response);
      }
    };
    xhr.send();
};

var postJSON = function(url, data, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.onload = function() {
        var status = xhr.status;
        if (status === 200) {
            callback(null, xhr.response);
        } else {
            callback(status, xhr.response);
        }
    };
    xhr.send(JSON.stringify(data));
};

current_url = window.location.href;
current_filename = current_url.split('/').pop();
// Also remove ?...
current_episode = current_filename.split('?')[0];

comment = function() {
    // Check if window.ethereum exists
    if (typeof window.ethereum !== 'undefined') {
        // Enable ethereum
        window.ethereum.enable();
        // Open a websocket to begin the sign transaction
        var ws = new WebSocket('ws://' + window.location.host + 
            "/api/v1/ws");
        ws.onopen = function() {
            // Send the sign transaction request
            var comment_text = comment_field.value;
            ws.send(JSON.stringify({
                'type': 'meta',
                'episode': current_episode,
                'text': comment_text,
                'address': window.ethereum.selectedAddress
            }));
        }
        ws.onmessage = function(event) {
            msg = JSON.parse(event.data)
            console.log(msg);
            // Check if the server wants a nickname
            if (msg.type === 'nickname') {
                console.log('nickname');
                var nickname = prompt('Please enter your nickname:');
                ws.send(JSON.stringify({
                    'type': 'nickname',
                    'nickname': nickname
                }));
            }
            // Check if the server wants to sign the comment
            else if (msg.type === 'sign') {
                provider = new ethers.providers.Web3Provider(window.ethereum);
                // Get the text to sign
                var text = msg.text;
                signer = provider.getSigner();
                // Sign the text
                signer.signMessage(text).then(function(signature) {
                    // Send the signature to the server
                    ws.send(JSON.stringify({
                        'type': 'signature',
                        'signature': signature
                    }));
                });
            }
            // Check if the comment was posted
            else if (msg.type === 'posted') {
                if (msg.success) {
                    comment.value = '';
                    // Reload the page
                    window.location.reload();
                }
                else {
                    alert('Something went wrong: ' + msg.error);
                }
            }
        }
    }
    else {
        // Request confirmation
        if (confirm("You don't have Metamask installed. Are you sure you want to comment anonymously? You will not be able to delete your comment.")) {
            var ws = new WebSocket('ws://' + window.location.host + 
                "/api/v1/ws");
            ws.onopen = function() {
                // Send the sign transaction request
                var comment_text = comment_field.value;
                console.log(comment_text);
                ws.send(JSON.stringify({
                    'type': 'meta',
                    'episode': current_episode,
                    'text': comment_text,
                    'address': '0x0'
                }));
            }
            ws.onmessage = function(event) {
                msg = JSON.parse(event.data)
                console.log(msg);
                // Check if the comment was posted
                if (msg.type === 'posted') {
                    if (msg.success) {
                        comment.value = '';
                        // Reload the page
                        window.location.reload();
                    }
                    else {
                        alert('Something went wrong: ' + msg.error);
                    }
                }
            }
        }
        return;
    }
}