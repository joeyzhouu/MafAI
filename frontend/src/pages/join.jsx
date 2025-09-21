import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { joinGame } from "../api/client";

export default function Join() {
  const navigate = useNavigate();
  const location = useLocation();
  const { name } = location.state || {};
  const [gameCode, setGameCode] = useState("");

  const handleJoin = async () => {
    if (!name) return alert("Please go back and enter your name first.");
    if (!gameCode.trim()) return alert("Enter a game code");

    try {
      const response = await joinGame(gameCode, name);
      const { player_id } = response.data; // Get the actual player_id from backend

      navigate(`/room/${gameCode}`, {
        state: {
          name,
          playerId: player_id, // Use the backend-generated player_id
          isHost: false,
        },
      });
    } catch (error) {
      console.error("Failed to join game:", error);
      alert("Failed to join game. Please check the game code and try again.");
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 relative">
      {/* Player name in top-right */}
      <div className="absolute top-6 right-6 text-white text-xl font-semibold tracking-wide">
        {name ? `Player: ${name}` : ""}
      </div>

      {/* Back button in top-left */}
      <button
        onClick={() => navigate("/")}
        className="absolute top-6 left-6 bg-gray-700 hover:bg-gray-600 text-white px-4 py-2 rounded-lg shadow-md transition"
      >
        ← Back
      </button>

      <div className="w-full max-w-md p-8 bg-gray-900/60 rounded-2xl shadow-xl backdrop-blur text-center">
        <h2 className="text-3xl font-bold text-white mb-6">Join a Game</h2>

        <input
          type="text"
          placeholder="Enter Game Code"
          value={gameCode}
          onChange={(e) => setGameCode(e.target.value)}
          className="w-full mb-6 p-3 rounded-lg border border-gray-700 bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        <button
          onClick={handleJoin}
          className="w-full py-3 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-semibold text-lg transition"
        >
          Enter
        </button>
      </div>
    </div>
  );
}
