import { SearchBar } from "./SearchBar";

interface FilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  untagged: boolean;
  onUntaggedChange: (value: boolean) => void;
  aiTagged: boolean;
  onAiTaggedChange: (value: boolean) => void;
  favoritesOnly: boolean;
  onFavoritesOnlyChange: (value: boolean) => void;
}

export function FilterBar({
  search,
  onSearchChange,
  untagged,
  onUntaggedChange,
  aiTagged,
  onAiTaggedChange,
  favoritesOnly,
  onFavoritesOnlyChange,
}: FilterBarProps) {
  return (
    <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
      <div className="flex-1 w-full sm:w-auto">
        <SearchBar value={search} onChange={onSearchChange} />
      </div>
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={untagged}
            onChange={(e) => onUntaggedChange(e.target.checked)}
            className="rounded bg-gray-800 border-gray-600 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-0"
          />
          Untagged
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={aiTagged}
            onChange={(e) => onAiTaggedChange(e.target.checked)}
            className="rounded bg-gray-800 border-gray-600 text-purple-500 focus:ring-purple-500 focus:ring-offset-0"
          />
          AI-tagged
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={favoritesOnly}
            onChange={(e) => onFavoritesOnlyChange(e.target.checked)}
            className="rounded bg-gray-800 border-gray-600 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-0"
          />
          Favorites
        </label>
      </div>
    </div>
  );
}
