import React from "react";

export default function LoadingScreen({ type, progress = 0 }) {
  const backgroundImage =
    type === "sunrise" ? "/assets/sunrise.png" : "/assets/nightfall.png";

  return (
    <div
      className="fixed inset-0 flex flex-col items-center justify-center bg-black"
      style={{
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <div className="w-3/4 h-6 bg-gray-700 rounded-full overflow-hidden mt-8">
        <div
          className="h-full bg-yellow-400"
          style={{ width: `${progress * 100}%` }}
        ></div>
      </div>
      <p className="text-white mt-4 font-semibold">Loading...</p>
    </div>
  );
}
