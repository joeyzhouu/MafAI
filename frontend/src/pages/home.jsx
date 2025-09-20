import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createGame, joinGame } from "../api/client";
import { v4 as uuidv4 } from "uuid";

export default function Home() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [joinId, setJoinId] = useState("");

  const handleCreate = async () => {
    if (!name.trim()) return alert("Enter a name");
    const hostId = uuidv4();
    const res = await createGame(hostId);
    const gameId = res.data.game_id;
    await joinGame(gameId, hostId, name);
    navigate(`/room/${gameId}`, {
      state: { name, playerId: hostId, isHost: true },
    });
  };

  const handleJoin = async () => {
    if (!name.trim() || !joinId.trim()) return alert("Enter both fields");
    const playerId = uuidv4();
    await joinGame(joinId, playerId, name);
    navigate(`/room/${joinId}`, { state: { name, playerId } });
  };

  return (
    <div className="p-6 max-w-md mx-auto space-y-4">
      <h1 className="text-2xl font-bold">mafAI</h1>
      <input
        className="border p-2 w-full"
        placeholder="Your Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <button
        className="bg-green-500 text-white px-4 py-2 w-full rounded"
        onClick={handleCreate}
      >
        Create Game
      </button>

      <hr />

      <input
        className="border p-2 w-full"
        placeholder="Game ID to Join"
        value={joinId}
        onChange={(e) => setJoinId(e.target.value)}
      />
      <button
        className="bg-blue-500 text-white px-4 py-2 w-full rounded"
        onClick={handleJoin}
      >
        Join Game
      </button>
    </div>
  );
}
