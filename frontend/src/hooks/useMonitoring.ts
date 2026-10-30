"use client";

import { useQuery } from "@tanstack/react-query";
import { monitoringApi } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";

export function useMonitoringHealth() {
  return useQuery({
    queryKey: queryKeys.monitoring.health(),
    queryFn: monitoringApi.health,
    refetchInterval: 5000,
  });
}

export function useMonitoringMetrics() {
  return useQuery({
    queryKey: queryKeys.monitoring.metrics(),
    queryFn: monitoringApi.metrics,
    refetchInterval: 5000,
  });
}
