import { useState, useCallback, useRef, useEffect } from "react";
import { useQuery, useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchSounds, addTag, removeTag, updateSound, type SoundQueryParams } from "../api/sounds";
import { fetchTags } from "../api/tags";
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
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [sort, setSort] = useState("filename");
  const [order, setOrder] = useState<"asc" | "desc">("asc");
  const perPage = 50;

  const debouncedSearch = useDebounce(search, 300);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Popular tags (top 20 by usage count)
  const { data: popularTags } = useQuery({
    queryKey: ["tags", "popular"],
    queryFn: () => fetchTags(),
  });
  const top20Tags = popularTags?.slice(0, 20) ?? [];

  // Sounds with infinite scroll
  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["sounds", { q: debouncedSearch || undefined, is_new: showNew || undefined, favorites_only: favoritesOnly || undefined, tags: selectedTags.join(",") || undefined, sort, order }],
    queryFn: ({ pageParam }) => fetchSounds({
      q: debouncedSearch || undefined,
      is_new: showNew ? true : undefined,
      favorites_only: favoritesOnly || undefined,
      tags: selectedTags.join(",") || undefined,
      page: pageParam,
      per_page: perPage,
      sort,
      order,
    }),
    getNextPageParam: (lastPage, allPages) => {
      const loaded = allPages.length * perPage;
      return loaded < lastPage.total ? allPages.length + 1 : undefined;
    },
    initialPageParam: 1,
  });

  // Infinite scroll observer
  useEffect(() => {
    const el = bottomRef.current;
    if (!el || !hasNextPage) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const allSounds = data?.pages.flatMap((p) => p.items) ?? [];
  const total = data?.pages[0]?.total ?? 0;

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["sounds"] });
    queryClient.invalidateQueries({ queryKey: ["tags"] });
  };

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
  };

  const toggleTag = (tagName: string) => {
    setSelectedTags((prev) =>
      prev.includes(tagName) ? prev.filter((t) => t !== tagName) : [...prev, tagName],
    );
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (sort !== col) return null;
    return <span className="ml-1">{order === "asc" ? "\u25B2" : "\u25BC"}</span>;
  };

  return (
    <div className="space-y-4">
      <FilterBar
        search={search}
        onSearchChange={setSearch}
        showNew={showNew}
        onShowNewChange={setShowNew}
        favoritesOnly={favoritesOnly}
        onFavoritesOnlyChange={setFavoritesOnly}
      />

      {top20Tags.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider mr-1">Tags</span>
          {top20Tags.map((tag) => (
            <button
              key={tag.name}
              onClick={() => toggleTag(tag.name)}
              className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                selectedTags.includes(tag.name)
                  ? "bg-indigo-600 border-indigo-500 text-white"
                  : "bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-300"
              }`}
            >
              {tag.name} ({tag.count})
            </button>
          ))}
          {selectedTags.length > 0 && (
            <button
              onClick={() => setSelectedTags([])}
              className="text-xs text-gray-500 hover:text-gray-300 ml-1"
            >
              Clear
            </button>
          )}
        </div>
      )}

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
              {isLoading && allSounds.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-500">Loading sounds...</td>
                </tr>
              ) : allSounds.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-500">No sounds found</td>
                </tr>
              ) : (
                allSounds.map((sound) => (
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

        <div className="px-4 py-3 border-t border-gray-800 text-sm text-gray-500">
          {total > 0 && <span>{allSounds.length} of {total} sounds</span>}
          {isFetchingNextPage && <span className="ml-2">Loading more...</span>}
        </div>
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
