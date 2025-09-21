import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import { useParams, useLocation, useNavigate } from "react-router-dom";

export default function PlayerRoom() {
  const { id } = useParams();
  const { name, playerId, isHost } = useLocation().state || {};
  const navigate = useNavigate();

  const [players, setPlayers] = useState({});
  const [socket, setSocket] = useState(null);

  // Debug logging
  useEffect(() => {
    console.log("PlayerRoom - Current player info:", {
      name,
      playerId,
      isHost,
    });
  }, [name, playerId, isHost]);

  useEffect(() => {
    if (!name || !playerId) {
      navigate("/join"); // fallback if someone lands here without joining
      return;
    }

    const s = io("http://localhost:5001");
    setSocket(s);

    // Join the room
    console.log("Joining room with:", { game_id: id, player_id: playerId });
    s.emit("join", { game_id: id, player_id: playerId });

    // Listen for state updates
    s.on("state_update", (data) => {
      console.log("State update received:", data);
      if (data.players) {
        const playersObj = Array.isArray(data.players)
          ? Object.fromEntries(data.players.map((p) => [p.player_id, p]))
          : data.players;
        console.log("Updated players object:", playersObj);
        setPlayers(playersObj);
      }
    });

    s.on("error", (error) => {
      console.error("Socket error:", error);
    });

    s.on("player_left", (data) => {
      console.log("Player left:", data);
      if (data.players) {
        const playersObj = Array.isArray(data.players)
          ? Object.fromEntries(data.players.map((p) => [p.player_id, p]))
          : data.players;
        setPlayers(playersObj);
      }
    });

    s.on("game_ended", (data) => {
      console.log("Game ended:", data);
      alert("Game ended - returning to home");
      navigate("/");
    });

    return () => s.disconnect();
  }, [id, playerId, name, navigate]);

  const toggleReady = () => {
    if (!socket || !players[playerId]) {
      console.log("Cannot toggle ready:", {
        socket: !!socket,
        playerExists: !!players[playerId],
      });
      return;
    }

    console.log(
      "Toggling ready for player:",
      playerId,
      "Current ready:",
      players[playerId].ready
    );
    socket.emit("player_ready", {
      game_id: id,
      player_id: playerId,
      ready: !players[playerId].ready,
    });
  };

  const leaveGame = () => {
    if (!socket) return;

    socket.emit("leave_game", {
      game_id: id,
      player_id: playerId,
    });

    // Navigate back to home immediately
    navigate("/");
  };

  const currentReady = players[playerId]?.ready || false;

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="absolute top-6 left-6 text-white font-bold text-2xl">
        Lobby: {id} {isHost && "(HOST)"}
      </div>
      <div className="absolute top-6 right-6 text-white font-semibold text-lg">
        {name ? `Player: ${name}` : ""}
        <div className="text-sm text-gray-400">ID: {playerId}</div>
      </div>

      {/* Player list */}
      <div className="absolute top-20 right-6 w-1/3 bg-gray-900/60 rounded-xl p-4 text-white">
        <h3 className="font-semibold mb-2 text-lg">Players:</h3>
        <ul>
          {Object.values(players).map((p) => (
            <li key={p.player_id} className="flex justify-between mb-1">
              <span>
                {p.name} {p.player_id === playerId && "(You)"}
              </span>
              <span>{p.ready ? "✅" : "❌"}</span>
            </li>
          ))}
        </ul>
        <div className="text-xs text-gray-400 mt-2">
          Your player ID: {playerId}
        </div>
      </div>

      {/* Ready and Leave buttons */}
      <div className="absolute bottom-10 left-10 flex gap-4">
        <button
          onClick={toggleReady}
          disabled={!players[playerId]}
          className={`px-6 py-4 text-white font-semibold rounded-xl text-lg transition ${
            currentReady
              ? "bg-red-500 hover:bg-red-600"
              : "bg-green-500 hover:bg-green-600"
          }`}
        >
          {currentReady ? "Unready" : "Ready"}
        </button>

        <button
          onClick={leaveGame}
          className="px-6 py-4 bg-gray-600 hover:bg-gray-700 text-white font-semibold rounded-xl text-lg transition"
        >
          Leave Game
        </button>
      </div>
    </div>
  );
}
