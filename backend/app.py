from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from routes.game_routes import game_bp
from sockets import init_socketio   # import your socket handlers

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mafai-secret'
CORS(app, resources={r"/*": {"origins": "*"}})

# Create socketio instance
socketio = SocketIO(app, cors_allowed_origins="*")

# Register HTTP routes
app.register_blueprint(game_bp, url_prefix="/api")

# Register socket.io handlers
init_socketio(socketio)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
