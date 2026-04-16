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
}: SoundRowProps) {
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
          <span className="text-sm text-white font-medium truncate max-w-[250px]" title={sound.filename}>
            {sound.filename}
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
        {sound.notes && (
          <span className="text-xs text-gray-500 truncate max-w-[150px] block" title={sound.notes}>
            {sound.notes}
          </span>
        )}
      </td>
    </tr>
  );
}
