interface AudioPlayerProps {
  soundId: string;
  currentSoundId: string | null;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  onToggle: (soundId: string) => void;
}

function formatTime(seconds: number): string {
  if (!seconds || !isFinite(seconds)) return "0:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function AudioPlayer({ soundId, currentSoundId, isPlaying, currentTime, duration, onToggle }: AudioPlayerProps) {
  const isActive = currentSoundId === soundId;
  const playing = isActive && isPlaying;
  const progress = isActive && duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onToggle(soundId)}
        className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${
          playing
            ? "bg-indigo-500 text-white"
            : "bg-gray-700 text-gray-300 hover:bg-gray-600"
        }`}
      >
        {playing ? (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="4" width="4" height="16" />
            <rect x="14" y="4" width="4" height="16" />
          </svg>
        ) : (
          <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
            <polygon points="5,3 19,12 5,21" />
          </svg>
        )}
      </button>
      {isActive && (
        <div className="flex items-center gap-1.5 min-w-[100px]">
          <div className="flex-1 h-1 bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-500 transition-all" style={{ width: `${progress}%` }} />
          </div>
          <span className="text-xs text-gray-500 tabular-nums w-9">{formatTime(currentTime)}</span>
        </div>
      )}
    </div>
  );
}
