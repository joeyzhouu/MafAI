import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import { useParams, useLocation, useNavigate } from "react-router-dom";

export default function HostRoom() {
  const { id } = useParams();
  const { name, playerId, isHost } = useLocation().state || {};
  const navigate = useNavigate();

  const [players, setPlayers] = useState({});
  const [socket, setSocket] = useState(null);
  const [gameSettings, setGameSettings] = useState({
    theme: "",
    mafia: 1,
    day_duration: 120,
    night_duration: 60,
  });

  // Redirect if not host
  useEffect(() => {
    if (!isHost) {
      navigate(`/room/${id}`, { state: { name, playerId, isHost: false } });
      return;
    }
  }, [isHost, navigate, id, name, playerId]);

  useEffect(() => {
    if (!name || !playerId || !isHost) {
      navigate("/");
      return;
    }

    const s = io("http://localhost:5001");
    setSocket(s);

    // Join the room
    console.log("Host joining room with:", {
      game_id: id,
      player_id: playerId,
    });
    s.emit("join", { game_id: id, player_id: playerId });

    // Listen for state updates
    s.on("state_update", (data) => {
      console.log("State update received:", data);
      if (data.players) {
        const playersObj = Array.isArray(data.players)
          ? Object.fromEntries(data.players.map((p) => [p.player_id, p]))
          : data.players;
        setPlayers(playersObj);
      }
      if (data.state && data.state.settings) {
        setGameSettings(data.state.settings);
      }
    });

    s.on("settings_updated", (data) => {
      setGameSettings(data.settings);
    });

    s.on("error", (error) => {
      console.error("Socket error:", error);
      alert(error.msg || "An error occurred");
    });

    s.on("player_left", (data) => {
      console.log("Player left:", data);
      if (data.players) {
        const playersObj = Array.isArray(data.players)
          ? Object.fromEntries(data.players.map((p) => [p.player_id, p]))
          : data.players;
        setPlayers(playersObj);
      }
      // Check if we're still the host
      if (data.new_host_id && data.new_host_id !== playerId) {
        alert("Host has changed - redirecting to player view");
        navigate(`/room/${id}`, { state: { name, playerId, isHost: false } });
      }
    });

    s.on("game_ended", (data) => {
      console.log("Game ended:", data);
      alert("Game ended - returning to home");
      navigate("/");
    });

    return () => s.disconnect();
  }, [id, playerId, name, navigate, isHost]);

  const updateSettings = (newSettings) => {
    if (!socket) return;

    const updatedSettings = { ...gameSettings, ...newSettings };
    setGameSettings(updatedSettings);

    socket.emit("update_settings", {
      game_id: id,
      host_id: playerId,
      settings: updatedSettings,
    });
  };

  const startGame = () => {
    const leaveGame = () => {
      if (!socket) return;

      if (
        confirm(
          "Are you sure you want to leave? This will end the game for all players."
        )
      ) {
        socket.emit("leave_game", {
          game_id: id,
          player_id: playerId,
        });

        // Navigate back to home immediately
        navigate("/");
      }
    };

    const playerCount = Object.keys(players).length;
    if (playerCount < 4) {
      alert("Need at least 4 players to start");
      return;
    }

    if (gameSettings.mafia >= Math.ceil(playerCount / 2)) {
      alert("Too many mafia for current player count");
      return;
    }

    if (!socket) return;

    socket.emit("start_game", {
      game_id: id,
      host_id: playerId,
    });
  };

  const playerCount = Object.keys(players).length;
  const canStart =
    playerCount >= 4 && gameSettings.mafia < Math.ceil(playerCount / 2);

  const leaveGame = () => {
    if (!socket) return;

    if (
      confirm(
        "Are you sure you want to leave? This will end the game for all players."
      )
    ) {
      socket.emit("leave_game", {
        game_id: id,
        player_id: playerId,
      });

      // Navigate back to home immediately
      navigate("/");
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="absolute top-6 left-6 text-white font-bold text-2xl">
        Lobby: {id} (HOST)
      </div>
      <div className="absolute top-6 right-6 text-white font-semibold text-lg">
        Host: {name}
      </div>

      {/* Settings Panel */}
      <div className="absolute top-20 left-6 w-1/3 bg-gray-900/60 rounded-xl p-4 text-white">
        <h3 className="font-semibold mb-4 text-lg">Game Settings</h3>

        {/* Theme */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Theme (Optional)
          </label>
          <input
            type="text"
            value={gameSettings.theme || ""}
            onChange={(e) => updateSettings({ theme: e.target.value })}
            placeholder="Custom theme or leave blank for random"
            className="w-full p-2 rounded border border-gray-700 bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Number of Mafia */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Number of Mafia (Max: {Math.floor(playerCount / 2)})
          </label>
          <select
            value={gameSettings.mafia}
            onChange={(e) =>
              updateSettings({ mafia: parseInt(e.target.value) })
            }
            className="w-full p-2 rounded border border-gray-700 bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {[1, 2, 3].map((num) => (
              <option
                key={num}
                value={num}
                disabled={num >= Math.ceil(playerCount / 2)}
              >
                {num} Mafia
              </option>
            ))}
          </select>
        </div>

        {/* Day Duration */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Day Duration: {Math.floor(gameSettings.day_duration / 60)}m{" "}
            {gameSettings.day_duration % 60}s
          </label>
          <input
            type="range"
            min="60"
            max="300"
            step="30"
            value={gameSettings.day_duration}
            onChange={(e) =>
              updateSettings({ day_duration: parseInt(e.target.value) })
            }
            className="w-full"
          />
        </div>

        {/* Night Duration */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">
            Night Duration: {Math.floor(gameSettings.night_duration / 60)}m{" "}
            {gameSettings.night_duration % 60}s
          </label>
          <input
            type="range"
            min="30"
            max="180"
            step="15"
            value={gameSettings.night_duration}
            onChange={(e) =>
              updateSettings({ night_duration: parseInt(e.target.value) })
            }
            className="w-full"
          />
        </div>
      </div>

      {/* Player list */}
      <div className="absolute top-20 right-6 w-1/3 bg-gray-900/60 rounded-xl p-4 text-white">
        <h3 className="font-semibold mb-2 text-lg">Players ({playerCount}):</h3>
        <ul className="mb-4">
          {Object.values(players).map((p) => (
            <li key={p.player_id} className="flex justify-between mb-1">
              <span>
                {p.name} {p.player_id === playerId && "(You)"}
              </span>
              <span>{p.ready ? "✅" : "❌"}</span>
            </li>
          ))}
        </ul>
        <div className="text-sm text-gray-400">
          Need at least 4 players to start
        </div>
      </div>

      {/* Host Controls: Ready and Leave buttons */}
      <div className="absolute bottom-10 left-10 flex gap-4">
        <button
          onClick={() => {
            if (!socket) return;
            const currentReady = players[playerId]?.ready || false;
            socket.emit("player_ready", {
              game_id: id,
              player_id: playerId,
              ready: !currentReady,
            });
          }}
          disabled={!players[playerId]}
          className={`px-6 py-4 text-white font-semibold rounded-xl text-lg transition ${
            players[playerId]?.ready
              ? "bg-red-500 hover:bg-red-600"
              : "bg-green-500 hover:bg-green-600"
          }`}
        >
          {players[playerId]?.ready ? "Unready" : "Ready"}
        </button>

        <button
          onClick={leaveGame}
          className="px-6 py-4 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded-xl text-lg transition"
        >
          Leave Game
        </button>
      </div>

      {/* Start Game Button */}
      <button
        onClick={startGame}
        disabled={!canStart}
        className={`absolute bottom-10 right-10 px-8 py-4 text-white font-semibold rounded-xl text-lg transition ${
          canStart
            ? "bg-blue-500 hover:bg-blue-600"
            : "bg-gray-600 cursor-not-allowed"
        }`}
      >
        {!canStart ? `Need ${4 - playerCount} more players` : "Start Game"}
      </button>
    </div>
  );
}
