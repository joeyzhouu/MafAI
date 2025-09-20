import { Routes, Route } from "react-router-dom";
import Home from "./pages/home.jsx";
import Room from "./pages/room.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/room/:id" element={<Room />} />
    </Routes>
  );
}
