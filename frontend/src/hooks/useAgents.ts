"use client";

import { useQuery } from "@tanstack/react-query";
import { agentsApi } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";

export function useAgentsList() {
  return useQuery({
    queryKey: queryKeys.agents.list(),
    queryFn: agentsApi.list,
    refetchInterval: 5000,
  });
}

export function useAgent(name: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.agents.detail(name),
    queryFn: () => agentsApi.get(name),
    enabled: enabled && !!name,
  });
}

export function useAgentExecutions(workflowId?: string) {
  return useQuery({
    queryKey: queryKeys.agents.executions(workflowId),
    queryFn: () => agentsApi.executions(workflowId),
    refetchInterval: 5000,
  });
}

export function useAgentTools() {
  return useQuery({
    queryKey: queryKeys.agents.tools(),
    queryFn: agentsApi.tools,
  });
}
