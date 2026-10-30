// Re-export so consumers can import auth alongside the other domain hooks
// from `@/hooks/useAuth` without reaching into `@/context` directly.
export { useAuth, AuthProvider } from "@/context/AuthContext";
