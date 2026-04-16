import { apiFetch } from "./client";
import type { TagWithCount } from "../types";

export function fetchTags(q?: string): Promise<TagWithCount[]> {
  const params = q ? `?q=${encodeURIComponent(q)}` : "";
  return apiFetch<TagWithCount[]>(`/api/tags${params}`);
}
