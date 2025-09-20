import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import { useParams, useLocation } from "react-router-dom";

export default function Room() {
  const { id } = useParams();
  const { name, playerId, isHost } = useLocation().state || {};
  const [players, setPlayers] = useState([]);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const s = io("http://localhost:5001");
    setSocket(s);

    s.emit("join", { game_id: id, player_id: playerId });

    s.on("state_update", (data) => {
      if (data.players) setPlayers(data.players);
    });

    return () => s.disconnect();
  }, [id, playerId]);

  return (
    <div>
      <h1>Lobby: {id}</h1>
      <ul>
        {players.map((p) => (
          <li key={p.player_id}>{p.name}</li>
        ))}
      </ul>
      {isHost && <button>Start Game</button>}
    </div>
  );
}
