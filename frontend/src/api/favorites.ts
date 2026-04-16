import { apiFetch } from "./client";

export function addFavorite(soundId: string): Promise<void> {
  return apiFetch(`/api/favorites/${soundId}`, { method: "POST" });
}

export function removeFavorite(soundId: string): Promise<void> {
  return apiFetch(`/api/favorites/${soundId}`, { method: "DELETE" });
}
