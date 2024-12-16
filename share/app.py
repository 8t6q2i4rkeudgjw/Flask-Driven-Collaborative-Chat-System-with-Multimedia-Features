from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, send, emit
import os

# Initialize Flask and SocketIO with a larger buffer size for handling larger files
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, max_http_buffer_size=50 * 1024 * 1024)  # 50 MB limit

# Directory to store uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Store users for tracking online status
users = {}

# Handle user joining the chat
@socketio.on('join')
def handle_join(username):
    users[request.sid] = username
    emit('user_event', f"{username} has joined the chat.", broadcast=True)
    emit('update_online_count', len(users), broadcast=True)

# Handle user disconnecting
@socketio.on('disconnect')
def handle_disconnect():
    username = users.pop(request.sid, "A user")
    emit('user_event', f"{username} has left the chat.", broadcast=True)
    emit('update_online_count', len(users), broadcast=True)

# Handle text messages
@socketio.on('message')
def handle_message(data):
    username = data.get("username", "Anonymous")
    message = data.get("message", "")
    send(f"{username}: {message}", broadcast=True)

# Handle file uploads with binary data
@socketio.on('file')
@socketio.on('file')
def handle_file(data):
    username = users.get(request.sid, 'Unknown')  # Get the username from `users`
    file_name = data['fileName']
    file_data = data['fileData']

    # Save the uploaded binary file
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    with open(file_path, 'wb') as f:
        f.write(file_data)

    # Emit the file message with username
    file_url = f"/uploads/{file_name}"
    emit('file', {'username': username, 'fileUrl': file_url, 'fileName': file_name}, broadcast=True)

# Handle location sharing
@socketio.on('location')
def handle_location(location_url):
    emit('location', location_url, broadcast=True)

# Serve the main chat page
@app.route('/')
def index():
    return render_template('index.html')


# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Run the app with debug mode disabled to prevent restarts
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5007)