import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function RoleDisplay() {
  const navigate = useNavigate();
  const { role } = useLocation().state || {}; // Expect { role: "mafia" }

  if (!role) {
    navigate("/");
    return null;
  }

  const roleColors = {
    mafia: "text-red-500",
    detective: "text-amber-600",
    doctor: "text-blue-400",
    civilian: "text-green-400",
  };

  const displayName =
    role.charAt(0).toUpperCase() + role.slice(1).toLowerCase();

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      <div className="bg-black/50 rounded-2xl p-8 text-center shadow-xl">
        <h1 className={`text-4xl font-bold mb-4 ${roleColors[role]}`}>
          Your Role
        </h1>
        <p className={`text-6xl font-extrabold ${roleColors[role]}`}>
          {displayName}
        </p>
      </div>
    </div>
  );
}
