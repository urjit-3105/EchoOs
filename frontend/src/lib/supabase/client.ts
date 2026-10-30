import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let cachedClient: SupabaseClient | null | undefined;

/**
 * Returns a memoised Supabase browser client, or `null` when the required
 * public env vars are not configured. Safe to call from client components;
 * returns `null` during SSR since realtime is a browser-only concern.
 */
export function getSupabaseBrowserClient(): SupabaseClient | null {
  if (cachedClient !== undefined) return cachedClient;

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !anonKey) {
    cachedClient = null;
    return cachedClient;
  }

  cachedClient = createClient(url, anonKey, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  });

  return cachedClient;
}

/**
 * True only when a Supabase client is configured AND realtime hasn't been
 * explicitly disabled via NEXT_PUBLIC_ENABLE_REALTIME=false.
 */
export function isRealtimeEnabled(): boolean {
  if (typeof window === "undefined") return false;
  if (!getSupabaseBrowserClient()) return false;
  return process.env.NEXT_PUBLIC_ENABLE_REALTIME !== "false";
}
