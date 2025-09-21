import { Routes, Route } from "react-router-dom";
import Home from "./pages/home.jsx";
import Join from "./pages/join.jsx";
import PlayerRoom from "./pages/player_room.jsx";
import HostRoom from "./pages/host_room.jsx";
import Narration from "./components/narration.jsx"; 

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/join" element={<Join />} />
      <Route path="/room/:id" element={<PlayerRoom />} />
      <Route path="/host/:id" element={<HostRoom />} />
      <Route path="/narration" element={<Narration />} /> {/* ⬅️ new */}
    </Routes>
  );
}
