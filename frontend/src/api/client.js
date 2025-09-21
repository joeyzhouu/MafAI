import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:5001/api",
});

export const createGame = (hostName, theme = null) =>
  client.post("/create", { host_name: hostName, theme });

export const joinGame = (gameId, name) =>
  client.post("/join", { game_id: gameId, name });

export const getLobby = (id) => client.get(`/lobby/${id}`);
