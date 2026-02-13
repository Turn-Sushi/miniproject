import axios from "axios"

export const api = axios.create({
  baseURL: import.meta.env.VITE_APP_FASTAPI_URL || "http://192.168.0.180:8001",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
})