import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { io } from "socket.io-client";

export default function NightPhase() {
  const location = useLocation();
  const navigate = useNavigate();

  const { gameId, playerId, name } = location.state || {};

  const [socket, setSocket] = useState(null);
  const [playerRole, setPlayerRole] = useState(null);
  const [players, setPlayers] = useState([]);
  const [activity, setActivity] = useState("");
  const [targetPlayer, setTargetPlayer] = useState("");
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const getRolePrompt = (role) => {
    switch (role) {
      case "mafia":
        return {
          question: "Who do you want to kill?",
          actionType: "kill",
          needsTarget: true,
        };
      case "doctor":
        return {
          question: "Who do you want to save?",
          actionType: "save",
          needsTarget: true,
        };
      case "detective":
        return {
          question: "Who do you want to investigate?",
          actionType: "investigate",
          needsTarget: true,
        };
      default:
        return {
          question: "What will you do tonight?",
          actionType: "none",
          needsTarget: false,
        };
    }
  };

  useEffect(() => {
    if (!gameId || !playerId) {
      navigate("/");
      return;
    }

    const s = io("http://localhost:5001");
    setSocket(s);

    s.emit("join", { game_id: gameId, player_id: playerId });

    // Listen for game state to get player role and other players
    s.on("state_update", (data) => {
      if (data.state) {
        const gameState = data.state;

        // Find current player's role
        if (gameState.players && gameState.players[playerId]) {
          setPlayerRole(gameState.players[playerId].role);
        }

        // Get all players for target selection (exclude self)
        const allPlayers = Object.entries(gameState.players || {})
          .filter(([id, player]) => id !== playerId && player.alive)
          .map(([id, player]) => ({ id, name: player.name }));
        setPlayers(allPlayers);
      }
    });

    s.on("day_started", (data) => {
      // Navigate to next phase when night resolves
      navigate("/narration", {
        state: {
          gameId,
          playerId,
          name,
          story: data.story || "The night has ended...",
        },
      });
    });

    s.on("error", (error) => {
      console.error("Socket error:", error);
      alert(error.msg || "An error occurred");
    });

    return () => s.disconnect();
  }, [gameId, playerId, navigate, name]);

  const handleSubmit = () => {
    if (!socket) return;

    const rolePrompt = getRolePrompt(playerRole);

    // Validate submission
    if (!activity.trim()) {
      alert("Please describe what you'll do tonight");
      return;
    }

    if (rolePrompt.needsTarget && !targetPlayer) {
      alert(`Please select a target for your ${rolePrompt.actionType} action`);
      return;
    }

    // Prepare action data
    const action = {
      type: rolePrompt.actionType,
      activity: activity.trim(),
      target: rolePrompt.needsTarget ? targetPlayer : null,
    };

    // Send action to backend
    socket.emit("player_action", {
      game_id: gameId,
      player_id: playerId,
      action: action,
    });

    setHasSubmitted(true);
  };

  if (!playerRole) {
    return (
      <div className="flex flex-col h-screen items-center justify-center bg-gradient-to-br from-gray-900 to-gray-800 text-white">
        <div className="text-2xl font-medium mb-4">Loading your role...</div>
        <div className="text-lg text-gray-400">Game: {gameId}</div>
      </div>
    );
  }

  const rolePrompt = getRolePrompt(playerRole);

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <div className="absolute top-6 left-6 text-white text-lg">
        Game: {gameId}
      </div>
      <div className="absolute top-6 right-6 text-white font-semibold text-lg">
        {name}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center px-8 max-w-2xl mx-auto">
        {/* Role Display */}
        <div className="mb-8 text-center">
          <div className="text-sm text-gray-400 mb-2">Your Role:</div>
          <div className="text-2xl font-bold capitalize text-blue-400">
            {playerRole}
          </div>
        </div>

        {/* Activity Input */}
        <div className="w-full mb-6">
          <label className="block text-lg font-medium mb-3 text-center">
            What will you do tonight?
          </label>
          <textarea
            value={activity}
            onChange={(e) => setActivity(e.target.value)}
            placeholder="Describe your nighttime activities..."
            disabled={hasSubmitted}
            className="w-full h-32 p-4 rounded-lg border border-gray-700 bg-gray-800 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        {/* Target Selection (for special roles) */}
        {rolePrompt.needsTarget && (
          <div className="w-full mb-6">
            <label className="block text-lg font-medium mb-3 text-center">
              {rolePrompt.question}
            </label>
            <select
              value={targetPlayer}
              onChange={(e) => setTargetPlayer(e.target.value)}
              disabled={hasSubmitted}
              className="w-full p-3 rounded-lg border border-gray-700 bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a player...</option>
              {players.map((player) => (
                <option key={player.id} value={player.id}>
                  {player.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={hasSubmitted}
          className={`px-8 py-3 rounded-lg font-semibold text-lg transition-all duration-200 ${
            hasSubmitted
              ? "bg-gray-600 text-gray-300 cursor-not-allowed"
              : "bg-blue-500 hover:bg-blue-600 text-white hover:scale-105 active:scale-95"
          }`}
        >
          {hasSubmitted ? "Action Submitted" : "Submit Action"}
        </button>

        {hasSubmitted && (
          <div className="mt-4 text-center text-gray-400">
            Waiting for other players to submit their actions...
          </div>
        )}
      </div>
    </div>
  );
}
