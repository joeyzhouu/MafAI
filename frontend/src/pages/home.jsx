import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createGame } from "../api/client";

export default function Home() {
  const navigate = useNavigate();
  const [name, setName] = useState("");

  const handleCreate = async () => {
    if (!name.trim()) return alert("Please enter a name");

    try {
      const res = await createGame(name);
      const gameId = res.data.game_id;
      const hostId = res.data.host_id;

      // Navigate to HOST room instead of regular room
      navigate(`/host/${gameId}`, {
        state: { name, playerId: hostId, isHost: true },
      });
    } catch (error) {
      console.error("Failed to create game:", error);
      alert("Failed to create game. Please try again.");
    }
  };

  const handleJoinPage = () => {
    if (!name.trim()) return alert("Please enter a name");
    navigate("/join", { state: { name } });
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="w-full max-w-md p-8 bg-gray-900/60 rounded-2xl shadow-xl backdrop-blur text-center">
        <h1 className="text-5xl font-extrabold text-white mb-8 tracking-wide">
          mafAI
        </h1>

        <input
          type="text"
          placeholder="Enter your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full mb-6 p-3 rounded-lg border border-gray-700 bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
        />

        <div className="space-y-4">
          <button
            onClick={handleCreate}
            className="w-full py-3 rounded-lg bg-green-500 hover:bg-green-600 text-white font-semibold text-lg transition"
          >
            Create Game
          </button>

          <button
            onClick={handleJoinPage}
            className="w-full py-3 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-semibold text-lg transition"
          >
            Join Game
          </button>
        </div>
      </div>
    </div>
  );
}
