import { apiFetch } from "./client";
import type { User } from "../types";

export function fetchMe(): Promise<User> {
  return apiFetch<User>("/auth/me");
}
