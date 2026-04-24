import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import { Dashboard } from "./components/Dashboard";
import { AdminPage } from "./components/AdminPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export default function App() {
  const isAdmin =
    typeof window !== "undefined" && window.location.pathname === "/admin";

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ProtectedRoute>
          <Layout>{isAdmin ? <AdminPage /> : <Dashboard />}</Layout>
        </ProtectedRoute>
      </AuthProvider>
    </QueryClientProvider>
  );
}
