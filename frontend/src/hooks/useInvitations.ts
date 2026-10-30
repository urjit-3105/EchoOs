"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { invitationsApi, type InvitationListParams } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";
import { ApiError } from "@/lib/api/client";
import type { Invitation } from "@/types";

export function useInvitations(params?: InvitationListParams) {
  return useQuery({
    queryKey: queryKeys.invitations.list(params),
    queryFn: () => invitationsApi.list(params),
  });
}

export function useInvitationByToken(token: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.invitations.byToken(token),
    queryFn: () => invitationsApi.byToken(token),
    enabled: enabled && !!token,
    retry: false,
  });
}

export function useInvitationQr(id: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.invitations.qr(id),
    queryFn: () => invitationsApi.qr(id),
    enabled: enabled && !!id,
  });
}

export function useCreateInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<Invitation>) => invitationsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.invitations.all });
      toast.success("Invitation sent");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to send invitation");
    },
  });
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ token, payload }: { token: string; payload?: Record<string, unknown> }) =>
      invitationsApi.accept(token, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.invitations.all });
      toast.success("Invitation accepted");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to accept invitation");
    },
  });
}

export function useResendInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => invitationsApi.resend(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.invitations.all });
      toast.success("Invitation resent");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to resend invitation");
    },
  });
}

export function useRevokeInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => invitationsApi.revoke(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.invitations.all });
      toast.success("Invitation revoked");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to revoke invitation");
    },
  });
}
