import axios from "axios"

export const api = axios.create({
  baseURL: "http://app1:8001", // || "http://192.168.0.180:8000",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
})