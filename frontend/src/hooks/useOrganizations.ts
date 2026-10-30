"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { organizationsApi } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";
import { ApiError } from "@/lib/api/client";
import type { Organization } from "@/types";

export function useOrganizations() {
  return useQuery({
    queryKey: queryKeys.organizations.list(),
    queryFn: organizationsApi.list,
  });
}

export function useOrganization(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.organizations.detail(id),
    queryFn: () => organizationsApi.get(id),
    enabled: enabled && !!id,
  });
}

export function useCurrentOrganization(enabled = true) {
  return useQuery({
    queryKey: queryKeys.organizations.current(),
    queryFn: organizationsApi.current,
    enabled,
    retry: false,
  });
}

export function useCreateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Organization>) => organizationsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizations.all });
      toast.success("Organization created");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to create organization");
    },
  });
}

export function useUpdateOrganization(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Organization>) => organizationsApi.update(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.organizations.all });
      toast.success("Organization updated");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to update organization");
    },
  });
}
