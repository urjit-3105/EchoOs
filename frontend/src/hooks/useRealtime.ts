"use client";

import { useEffect, useInsertionEffect, useRef } from "react";
import type { RealtimeChannel } from "@supabase/supabase-js";
import { getSupabaseBrowserClient, isRealtimeEnabled } from "@/lib/supabase/client";

/**
 * Subscribes to Supabase `postgres_changes` events for the given table and
 * invokes `onChange` for every INSERT/UPDATE/DELETE. When Supabase isn't
 * configured (or realtime is disabled via env), this is a no-op — the
 * `refetchInterval` polling on the underlying query hooks covers that case.
 */
export function useRealtimeTable(table: string, onChange: () => void): void {
  const onChangeRef = useRef(onChange);
  useInsertionEffect(() => {
    onChangeRef.current = onChange;
  });

  useEffect(() => {
    if (!isRealtimeEnabled()) return;

    const supabase = getSupabaseBrowserClient();
    if (!supabase) return;

    let channel: RealtimeChannel | null = supabase
      .channel(`realtime:${table}`)
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table },
        () => {
          onChangeRef.current();
        }
      )
      .subscribe();

    return () => {
      if (channel) {
        supabase.removeChannel(channel);
        channel = null;
      }
    };
  }, [table]);
}
