interface FavoriteButtonProps {
  isFavorited: boolean;
  onClick: () => void;
}

export function FavoriteButton({ isFavorited, onClick }: FavoriteButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`transition-colors ${isFavorited ? "text-red-500 hover:text-red-400" : "text-gray-600 hover:text-gray-400"}`}
      title={isFavorited ? "Remove from favorites" : "Add to favorites"}
    >
      <svg className="w-5 h-5" fill={isFavorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
      </svg>
    </button>
  );
}
