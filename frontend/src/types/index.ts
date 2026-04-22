export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url: string | null;
}

export interface Tag {
  id: string;
  name: string;
}

export interface TagWithCount {
  name: string;
  count: number;
}

export interface Sound {
  id: string;
  filename: string;
  duration_seconds: number | null;
  notes: string | null;
  is_new: boolean;
  ai_tagged: boolean;
  mime_type: string;
  tags: Tag[];
  is_favorited: boolean;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}
