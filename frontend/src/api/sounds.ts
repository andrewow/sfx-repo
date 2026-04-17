import { apiFetch } from "./client";
import type { PaginatedResponse, Sound } from "../types";

export interface SoundQueryParams {
  q?: string;
  tags?: string;
  is_new?: boolean;
  untagged?: boolean;
  favorites_only?: boolean;
  page?: number;
  per_page?: number;
  sort?: string;
  order?: string;
}

export function fetchSounds(params: SoundQueryParams): Promise<PaginatedResponse<Sound>> {
  const searchParams = new URLSearchParams();
  if (params.q) searchParams.set("q", params.q);
  if (params.tags) searchParams.set("tags", params.tags);
  if (params.is_new !== undefined) searchParams.set("is_new", String(params.is_new));
  if (params.untagged) searchParams.set("untagged", "true");
  if (params.favorites_only) searchParams.set("favorites_only", "true");
  if (params.page) searchParams.set("page", String(params.page));
  if (params.per_page) searchParams.set("per_page", String(params.per_page));
  if (params.sort) searchParams.set("sort", params.sort);
  if (params.order) searchParams.set("order", params.order);

  return apiFetch<PaginatedResponse<Sound>>(`/api/sounds?${searchParams}`);
}

export function addTag(soundId: string, tag: string): Promise<Sound> {
  return apiFetch<Sound>(`/api/sounds/${soundId}/tags`, {
    method: "POST",
    body: JSON.stringify({ tag }),
  });
}

export function removeTag(soundId: string, tagName: string): Promise<Sound> {
  return apiFetch<Sound>(`/api/sounds/${soundId}/tags/${encodeURIComponent(tagName)}`, {
    method: "DELETE",
  });
}

export function updateSound(soundId: string, data: { notes?: string | null; is_new?: boolean; duration_seconds?: number }): Promise<Sound> {
  return apiFetch<Sound>(`/api/sounds/${soundId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function getAudioUrl(soundId: string): string {
  return `/api/sounds/${soundId}/audio`;
}
