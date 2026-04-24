import type { ReactNode } from "react";
import { useAuth } from "../context/AuthContext";

export function Layout({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const path = typeof window !== "undefined" ? window.location.pathname : "/";
  const isAdmin = path === "/admin";

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <a href="/" className="flex items-center gap-3">
              <span className="text-xl">🔊</span>
              <h1 className="text-lg font-semibold">SFX Repository</h1>
            </a>
          </div>
          {user && (
            <div className="flex items-center gap-3">
              <a
                href={isAdmin ? "/" : "/admin"}
                className="text-xs text-gray-500 hover:text-gray-300"
              >
                {isAdmin ? "Home" : "Admin"}
              </a>
              {user.avatar_url && (
                <img src={user.avatar_url} alt="" className="w-7 h-7 rounded-full" />
              )}
              <span className="text-sm text-gray-400">{user.display_name}</span>
              <a
                href="/auth/logout"
                className="text-xs text-gray-500 hover:text-gray-300 ml-2"
              >
                Sign out
              </a>
            </div>
          )}
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>
    </div>
  );
}
