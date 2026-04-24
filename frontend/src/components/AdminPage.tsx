import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchBackupStatus, triggerBackup } from "../api/admin";

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function formatAge(days: number | null): string {
  if (days === null) return "never";
  if (days < 1 / 24) return "just now";
  if (days < 1) return `${Math.round(days * 24)} hours ago`;
  if (days < 2) return "1 day ago";
  return `${Math.round(days)} days ago`;
}

export function AdminPage() {
  const queryClient = useQueryClient();
  const [logOpen, setLogOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["backup-status"],
    queryFn: fetchBackupStatus,
    refetchInterval: 5000,
  });

  const trigger = useMutation({
    mutationFn: triggerBackup,
    onSuccess: () => {
      setTimeout(
        () => queryClient.invalidateQueries({ queryKey: ["backup-status"] }),
        1500,
      );
    },
  });

  const last = data?.last_backup;
  const isStale = data?.is_stale ?? false;

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-xl font-semibold">Database Backup</h2>
        <p className="text-sm text-gray-400 mt-1">
          Backs up the Postgres database to Google Drive. Runs automatically every 7 days.
        </p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
        <div>
          <div className="text-xs uppercase tracking-wider text-gray-500 mb-1">
            Last backup
          </div>
          {isLoading ? (
            <div className="text-sm text-gray-500">Loading…</div>
          ) : last ? (
            <>
              <div
                className={`text-base font-medium ${
                  isStale ? "text-red-400" : "text-gray-200"
                }`}
              >
                {formatAge(data!.days_ago)}
                {isStale && (
                  <span className="ml-2 text-xs font-normal text-red-400">
                    (over {data!.stale_threshold_days} days — stale)
                  </span>
                )}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                {last.name} · {formatBytes(last.size_bytes)} ·{" "}
                {new Date(last.created_time).toLocaleString()}
              </div>
            </>
          ) : (
            <div className="text-red-400 text-base font-medium">
              No backup found in Drive folder
            </div>
          )}
        </div>

        {data && !data.drive_folder_configured && (
          <div className="text-xs text-yellow-400 bg-yellow-400/10 border border-yellow-400/20 rounded px-3 py-2">
            BACKUP_DRIVE_FOLDER_ID is not configured. Backups will run but won't upload.
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            onClick={() => trigger.mutate()}
            disabled={trigger.isPending}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:text-gray-500 rounded text-sm font-medium transition-colors"
          >
            {trigger.isPending ? "Starting…" : "Run backup now"}
          </button>
          {trigger.isSuccess && (
            <span className="text-sm text-green-400">
              Started. Runs in the background — check back in a minute.
            </span>
          )}
          {trigger.isError && (
            <span className="text-sm text-red-400">
              Failed: {(trigger.error as Error).message}
            </span>
          )}
        </div>

        {data?.log_tail && (
          <div>
            <button
              onClick={() => setLogOpen((v) => !v)}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              {logOpen ? "▼" : "▶"} Last run log ({data.log_tail.split("\n").length} lines)
            </button>
            {logOpen && (
              <pre className="mt-2 bg-black/50 border border-gray-800 rounded p-3 text-xs text-gray-400 overflow-x-auto whitespace-pre-wrap">
                {data.log_tail}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
