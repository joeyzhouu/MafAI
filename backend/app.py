from flask import Flask
from flask_socketio import SocketIO
from routes.game_routes import game_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mafai-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# register routes
app.register_blueprint(game_bp, url_prefix="/api")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
