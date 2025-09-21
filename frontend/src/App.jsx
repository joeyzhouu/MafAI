import { Routes, Route } from "react-router-dom";
import Home from "./pages/home.jsx";
import Room from "./pages/room.jsx";
import Join from "./pages/join.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/join" element={<Join />} />
      <Route path="/room/:id" element={<Room />} />
    </Routes>
  );
}
