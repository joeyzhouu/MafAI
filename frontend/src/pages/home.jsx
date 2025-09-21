import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createGame, joinGame } from "../api/client";
import { v4 as uuidv4 } from "uuid";

export default function Home() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [joinId, setJoinId] = useState("");
  const [joining, setJoining] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) return alert("Please enter a name");
    const res = await createGame(name);
    const gameId = res.data.game_id;
    const hostId = res.data.host_id;
    navigate(`/room/${gameId}`, {
      state: { name, playerId: hostId, isHost: true },
    });
  };

  const handleJoin = async () => {
    if (!name.trim()) return alert("Please enter a name");
    if (!joinId.trim()) return alert("Enter a Game ID to join");
    const playerId = uuidv4();
    await joinGame(joinId, playerId, name);
    navigate(`/room/${joinId}`, { state: { name, playerId } });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800">
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

        {/* Action buttons */}
        <div className="space-y-4">
          <button
            onClick={handleCreate}
            className="w-full py-3 rounded-lg bg-green-500 hover:bg-green-600 text-white font-semibold text-lg transition"
          >
            Create Game
          </button>

          {/* Join game toggle */}
          {!joining ? (
            <button
              onClick={() => setJoining(true)}
              className="w-full py-3 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-semibold text-lg transition"
            >
              Join Game
            </button>
          ) : (
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Enter Game ID"
                value={joinId}
                onChange={(e) => setJoinId(e.target.value)}
                className="w-full p-3 rounded-lg border border-gray-700 bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleJoin}
                className="w-full py-3 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-semibold text-lg transition"
              >
                Join Now
              </button>
              <button
                onClick={() => setJoining(false)}
                className="w-full py-2 text-gray-300 text-sm underline"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
