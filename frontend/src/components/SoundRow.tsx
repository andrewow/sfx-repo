import { useState, useRef, useEffect } from "react";
import type { Sound } from "../types";
import { AudioPlayer } from "./AudioPlayer";
import { FavoriteButton } from "./FavoriteButton";
import { TagEditor } from "./TagEditor";

interface SoundRowProps {
  sound: Sound;
  currentSoundId: string | null;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onTogglePlay: (soundId: string) => void;
  onToggleFavorite: (soundId: string, isFavorited: boolean) => void;
  onAddTag: (soundId: string, tag: string) => void;
  onRemoveTag: (soundId: string, tag: string) => void;
  onMarkSeen: (soundId: string) => void;
  onUpdateNotes: (soundId: string, notes: string | null) => void;
}

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return "--";
  if (seconds === 0) return "<1s";
  if (seconds >= 60) {
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return s > 0 ? `${m}m ${s}s` : `${m}m`;
  }
  return `${Math.round(seconds)}s`;
}

export function SoundRow({
  sound,
  currentSoundId,
  isPlaying,
  currentTime,
  duration,
  onTogglePlay,
  onToggleFavorite,
  onAddTag,
  onRemoveTag,
  onMarkSeen,
  onUpdateNotes,
}: SoundRowProps) {
  const [copied, setCopied] = useState(false);
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesValue, setNotesValue] = useState(sound.notes || "");
  const notesRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editingNotes) notesRef.current?.focus();
  }, [editingNotes]);

  const handleCopyFilename = () => {
    navigator.clipboard.writeText(sound.filename);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleNotesSubmit = () => {
    const trimmed = notesValue.trim();
    const newNotes = trimmed || null;
    if (newNotes !== sound.notes) {
      onUpdateNotes(sound.id, newNotes);
    }
    setEditingNotes(false);
  };

  return (
    <tr className="border-b border-gray-800 hover:bg-gray-900/50 transition-colors">
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {sound.is_new && (
            <button
              onClick={() => onMarkSeen(sound.id)}
              className="w-2 h-2 rounded-full bg-green-500 shrink-0"
              title="Mark as seen"
            />
          )}
          <span
            className={`text-sm font-medium truncate max-w-[250px] cursor-copy transition-colors ${copied ? "text-green-400" : "text-white hover:text-indigo-300"}`}
            title="Click to copy filename"
            onClick={handleCopyFilename}
          >
            {copied ? "Copied!" : sound.filename}
          </span>
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-400 tabular-nums">{formatDuration(sound.duration_seconds)}</td>
      <td className="px-4 py-3">
        <TagEditor
          tags={sound.tags}
          onAdd={(tag) => onAddTag(sound.id, tag)}
          onRemove={(tag) => onRemoveTag(sound.id, tag)}
        />
      </td>
      <td className="px-4 py-3">
        <AudioPlayer
          soundId={sound.id}
          currentSoundId={currentSoundId}
          isPlaying={isPlaying}
          currentTime={currentTime}
          duration={duration}
          onToggle={onTogglePlay}
        />
      </td>
      <td className="px-4 py-3">
        <FavoriteButton
          isFavorited={sound.is_favorited}
          onClick={() => onToggleFavorite(sound.id, sound.is_favorited)}
        />
      </td>
      <td className="px-4 py-3">
        {editingNotes ? (
          <textarea
            ref={notesRef}
            value={notesValue}
            onChange={(e) => setNotesValue(e.target.value)}
            onBlur={handleNotesSubmit}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleNotesSubmit(); }
              if (e.key === "Escape") { setEditingNotes(false); setNotesValue(sound.notes || ""); }
            }}
            className="w-full bg-gray-800 text-xs text-gray-300 px-2 py-1 rounded border border-gray-600 focus:border-indigo-500 outline-none resize-none min-w-[150px]"
            rows={2}
          />
        ) : (
          <span
            onClick={() => { setNotesValue(sound.notes || ""); setEditingNotes(true); }}
            className="text-xs block cursor-text max-w-[200px]"
            title={sound.notes || "Click to add notes"}
          >
            {sound.notes ? (
              <span className="text-gray-500 truncate block">{sound.notes}</span>
            ) : (
              <span className="text-gray-700 italic">add notes...</span>
            )}
          </span>
        )}
      </td>
    </tr>
  );
}
