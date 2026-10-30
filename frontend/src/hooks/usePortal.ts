"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { portalApi } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";
import { ApiError } from "@/lib/api/client";

export function usePortalDetail(token: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.portal.detail(token),
    queryFn: () => portalApi.get(token),
    enabled: enabled && !!token,
    retry: false,
  });
}

export function usePortalInvitation(token: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.portal.invitation(token),
    queryFn: () => portalApi.invitation(token),
    enabled: enabled && !!token,
    retry: false,
  });
}

export function usePortalProgress(token: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.portal.progress(token),
    queryFn: () => portalApi.progress(token),
    enabled: enabled && !!token,
    refetchInterval: 5000,
  });
}

export function usePortalPolicies(token: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.portal.policies(token),
    queryFn: () => portalApi.policies(token),
    enabled: enabled && !!token,
  });
}

export function useAcceptPortalInvitation(token: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload?: Record<string, unknown>) => portalApi.acceptInvitation(token, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.portal.invitation(token) });
      queryClient.invalidateQueries({ queryKey: queryKeys.portal.detail(token) });
      queryClient.invalidateQueries({ queryKey: queryKeys.portal.progress(token) });
      toast.success("Invitation accepted");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to accept invitation");
    },
  });
}

export function useSubmitPortalProfile(token: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Record<string, unknown>) => portalApi.submitProfile(token, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.portal.progress(token) });
      toast.success("Profile saved");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to save profile");
    },
  });
}

export function usePortalDocuments(token: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.portal.documents(token),
    queryFn: () => portalApi.documents(token),
    enabled: enabled && !!token,
  });
}

export function useUploadPortalDocument(token: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ documentType, file }: { documentType: string; file: File }) =>
      portalApi.uploadDocument(token, documentType, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.portal.progress(token) });
      queryClient.invalidateQueries({ queryKey: queryKeys.portal.documents(token) });
      toast.success("Document uploaded");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to upload document");
    },
  });
}

export function useDeletePortalDocument(token: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) => portalApi.deleteDocument(token, documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.portal.progress(token) });
      queryClient.invalidateQueries({ queryKey: queryKeys.portal.documents(token) });
      toast.success("Document removed");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to remove document");
    },
  });
}

export function usePortalWorkflow(token: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.portal.workflow(token),
    queryFn: () => portalApi.workflow(token),
    enabled: enabled && !!token,
    refetchInterval: 5000,
  });
}

export function useAcceptPortalTerms(token: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => portalApi.acceptTerms(token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.portal.progress(token) });
      toast.success("Terms accepted");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to accept terms");
    },
  });
}
