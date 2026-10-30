"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { workflowApi, type WorkflowListParams } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";
import { ApiError } from "@/lib/api/client";

export function useWorkflows(params?: WorkflowListParams) {
  return useQuery({
    queryKey: queryKeys.workflows.list(params),
    queryFn: () => workflowApi.list(params),
    refetchInterval: 5000,
  });
}

export function useWorkflow(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.workflows.detail(id),
    queryFn: () => workflowApi.get(id),
    enabled: enabled && !!id,
    refetchInterval: 5000,
  });
}

export function useWorkflowStatus(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.workflows.status(id),
    queryFn: () => workflowApi.status(id),
    enabled: enabled && !!id,
    refetchInterval: 5000,
  });
}

export function useWorkflowHistory(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.workflows.history(id),
    queryFn: () => workflowApi.history(id),
    enabled: enabled && !!id,
  });
}

export function useWorkflowTasks(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.workflows.tasks(id),
    queryFn: () => workflowApi.tasks(id),
    enabled: enabled && !!id,
    refetchInterval: 5000,
  });
}

export function useWorkflowTemplates() {
  return useQuery({
    queryKey: queryKeys.workflows.templates(),
    queryFn: workflowApi.templates,
  });
}

export function useStartWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { employee_id: string; template_id?: string }) =>
      workflowApi.start(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all });
      toast.success("Workflow started");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to start workflow");
    },
  });
}

function useWorkflowAction(
  action: (id: string) => Promise<unknown>,
  successMessage: string,
  failureMessage: string
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => action(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.workflows.status(id) });
      toast.success(successMessage);
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : failureMessage);
    },
  });
}

export function usePauseWorkflow() {
  return useWorkflowAction(workflowApi.pause, "Workflow paused", "Unable to pause workflow");
}

export function useResumeWorkflow() {
  return useWorkflowAction(workflowApi.resume, "Workflow resumed", "Unable to resume workflow");
}

export function useCancelWorkflow() {
  return useWorkflowAction(workflowApi.cancel, "Workflow cancelled", "Unable to cancel workflow");
}

export function useRetryWorkflow() {
  return useWorkflowAction(workflowApi.retry, "Workflow retried", "Unable to retry workflow");
}
