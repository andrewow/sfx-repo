import { apiFetch } from "./client";

export interface BackupFile {
  id: string;
  name: string;
  created_time: string;
  size_bytes: number;
}

export interface BackupStatus {
  last_backup: BackupFile | null;
  days_ago: number | null;
  is_stale: boolean;
  stale_threshold_days: number;
  drive_folder_configured: boolean;
  log_tail: string;
}

export function fetchBackupStatus(): Promise<BackupStatus> {
  return apiFetch<BackupStatus>("/api/admin/backup/status");
}

export function triggerBackup(): Promise<{ status: string; triggered_by: string }> {
  return apiFetch("/api/admin/backup", { method: "POST" });
}
