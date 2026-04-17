import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchTags } from "../api/tags";
import type { Tag } from "../types";

interface TagEditorProps {
  tags: Tag[];
  onAdd: (tagName: string) => void;
  onRemove: (tagName: string) => void;
}

export function TagEditor({ tags, onAdd, onRemove }: TagEditorProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const { data: suggestions } = useQuery({
    queryKey: ["tags", input],
    queryFn: () => fetchTags(input),
    enabled: isAdding && input.length >= 1,
  });

  useEffect(() => {
    if (isAdding) inputRef.current?.focus();
  }, [isAdding]);

  const addTagByName = (tagName: string) => {
    const name = tagName.trim().toLowerCase();
    if (name && !tags.some((t) => t.name === name)) {
      onAdd(name);
    }
  };

  const handleSubmit = (tagName: string) => {
    addTagByName(tagName);
    setInput("");
    setIsAdding(false);
  };

  const handleInputChange = (value: string) => {
    if (value.includes(",")) {
      const parts = value.split(",");
      for (let i = 0; i < parts.length - 1; i++) {
        addTagByName(parts[i]);
      }
      setInput(parts[parts.length - 1]);
    } else {
      setInput(value);
    }
  };

  const existingTagNames = new Set(tags.map((t) => t.name));
  const filtered = suggestions?.filter((s) => !existingTagNames.has(s.name)).slice(0, 6) ?? [];

  return (
    <div className="flex flex-wrap items-center gap-1">
      {tags.map((tag) => (
        <span key={tag.id} className="inline-flex items-center gap-0.5 bg-gray-800 text-gray-300 text-xs px-2 py-0.5 rounded-full">
          {tag.name}
          <button onClick={() => onRemove(tag.name)} className="text-gray-500 hover:text-gray-300 ml-0.5">
            &times;
          </button>
        </span>
      ))}
      {isAdding ? (
        <div className="relative">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSubmit(input);
              if (e.key === "Escape") { setIsAdding(false); setInput(""); }
            }}
            onBlur={() => { setTimeout(() => { if (input.trim()) addTagByName(input); setIsAdding(false); setInput(""); }, 150); }}
            className="bg-gray-800 text-white text-xs px-2 py-0.5 rounded-full outline-none border border-gray-600 focus:border-indigo-500 w-24"
            placeholder="add tag..."
          />
          {filtered.length > 0 && (
            <div className="absolute top-full left-0 mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-10 min-w-[120px]">
              {filtered.map((s) => (
                <button
                  key={s.name}
                  onMouseDown={(e) => { e.preventDefault(); handleSubmit(s.name); }}
                  className="block w-full text-left text-xs px-3 py-1.5 text-gray-300 hover:bg-gray-700"
                >
                  {s.name} <span className="text-gray-500">({s.count})</span>
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
        <button
          onClick={() => setIsAdding(true)}
          className="text-gray-600 hover:text-gray-400 text-xs px-1"
          title="Add tag"
        >
          ADD+
        </button>
      )}
    </div>
  );
}
