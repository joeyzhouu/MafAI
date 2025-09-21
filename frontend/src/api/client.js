import axios from "axios";
import { v4 as uuidv4 } from "uuid";

const client = axios.create({
  baseURL: "http://localhost:5001/api",
});

export const createGame = (hostName, theme = null) =>
  client.post("/create", { host_name: hostName, theme });

export const joinGame = (gameId, playerId, name) =>
  client.post("/join", { game_id: gameId, player_id: playerId, name });

export const getLobby = (id) => client.get(`/lobby/${id}`);
