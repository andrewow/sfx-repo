import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchSounds, addTag, removeTag, updateSound, type SoundQueryParams } from "../api/sounds";
import { addFavorite, removeFavorite } from "../api/favorites";
import { useDebounce } from "../hooks/useDebounce";
import { useAudioPlayer } from "../hooks/useAudioPlayer";
import { FilterBar } from "./FilterBar";
import { SoundRow } from "./SoundRow";

export function Dashboard() {
  const queryClient = useQueryClient();
  const audio = useAudioPlayer();

  const [search, setSearch] = useState("");
  const [showNew, setShowNew] = useState(false);
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("filename");
  const [order, setOrder] = useState<"asc" | "desc">("asc");
  const perPage = 50;

  const debouncedSearch = useDebounce(search, 300);

  const params: SoundQueryParams = {
    q: debouncedSearch || undefined,
    is_new: showNew ? true : undefined,
    favorites_only: favoritesOnly || undefined,
    page,
    per_page: perPage,
    sort,
    order,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["sounds", params],
    queryFn: () => fetchSounds(params),
    placeholderData: (prev) => prev,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["sounds"] });

  const addTagMut = useMutation({ mutationFn: ({ soundId, tag }: { soundId: string; tag: string }) => addTag(soundId, tag), onSuccess: invalidate });
  const removeTagMut = useMutation({ mutationFn: ({ soundId, tag }: { soundId: string; tag: string }) => removeTag(soundId, tag), onSuccess: invalidate });
  const addFavMut = useMutation({ mutationFn: (soundId: string) => addFavorite(soundId), onSuccess: invalidate });
  const removeFavMut = useMutation({ mutationFn: (soundId: string) => removeFavorite(soundId), onSuccess: invalidate });
  const markSeenMut = useMutation({ mutationFn: (soundId: string) => updateSound(soundId, { is_new: false }), onSuccess: invalidate });

  const handleToggleFavorite = useCallback(
    (soundId: string, isFavorited: boolean) => {
      if (isFavorited) removeFavMut.mutate(soundId);
      else addFavMut.mutate(soundId);
    },
    [addFavMut, removeFavMut],
  );

  const handleSort = (col: string) => {
    if (sort === col) {
      setOrder(order === "asc" ? "desc" : "asc");
    } else {
      setSort(col);
      setOrder("asc");
    }
    setPage(1);
  };

  const totalPages = data ? Math.ceil(data.total / perPage) : 0;

  const SortIcon = ({ col }: { col: string }) => {
    if (sort !== col) return null;
    return <span className="ml-1">{order === "asc" ? "\u25B2" : "\u25BC"}</span>;
  };

  return (
    <div className="space-y-4">
      <FilterBar
        search={search}
        onSearchChange={(v) => { setSearch(v); setPage(1); }}
        showNew={showNew}
        onShowNewChange={(v) => { setShowNew(v); setPage(1); }}
        favoritesOnly={favoritesOnly}
        onFavoritesOnlyChange={(v) => { setFavoritesOnly(v); setPage(1); }}
      />

      <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800 text-left">
                <th className="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300" onClick={() => handleSort("filename")}>
                  Name <SortIcon col="filename" />
                </th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300 w-20" onClick={() => handleSort("duration_seconds")}>
                  Duration <SortIcon col="duration_seconds" />
                </th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Tags</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider w-40">Play</th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider w-12"></th>
                <th className="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Notes</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && !data ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-500">Loading sounds...</td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-500">No sounds found</td>
                </tr>
              ) : (
                data?.items.map((sound) => (
                  <SoundRow
                    key={sound.id}
                    sound={sound}
                    currentSoundId={audio.currentSoundId}
                    isPlaying={audio.isPlaying}
                    currentTime={audio.currentTime}
                    duration={audio.duration}
                    onTogglePlay={audio.toggle}
                    onToggleFavorite={handleToggleFavorite}
                    onAddTag={(soundId, tag) => addTagMut.mutate({ soundId, tag })}
                    onRemoveTag={(soundId, tag) => removeTagMut.mutate({ soundId, tag })}
                    onMarkSeen={(soundId) => markSeenMut.mutate(soundId)}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-800">
            <span className="text-sm text-gray-500">
              {data?.total} sounds total
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="px-3 py-1 text-sm text-gray-400 bg-gray-800 rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Prev
              </button>
              <span className="text-sm text-gray-400 px-3">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1 text-sm text-gray-400 bg-gray-800 rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
