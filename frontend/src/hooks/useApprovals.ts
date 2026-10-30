"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { approvalsApi } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";
import { ApiError } from "@/lib/api/client";

export function useApprovals(status: string = "pending") {
  return useQuery({
    queryKey: queryKeys.approvals.list(status),
    queryFn: () => approvalsApi.list(status),
    refetchInterval: 5000,
  });
}

export function useApproval(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.approvals.detail(id),
    queryFn: () => approvalsApi.get(id),
    enabled: enabled && !!id,
    refetchInterval: 5000,
  });
}

export function useDecideApproval() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      approved,
      comments,
    }: {
      id: string;
      approved: boolean;
      comments?: string;
    }) => approvalsApi.decide(id, { approved, comments }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.approvals.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all });
      toast.success(variables.approved ? "Approved" : "Rejected");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to submit decision");
    },
  });
}
