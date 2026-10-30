"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { documentsApi } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";
import { ApiError } from "@/lib/api/client";

export function useDocuments(employeeId?: string) {
  return useQuery({
    queryKey: queryKeys.documents.list(employeeId),
    queryFn: () => documentsApi.list(employeeId),
  });
}

export function useDocumentChecklist(employeeId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.documents.checklist(employeeId),
    queryFn: () => documentsApi.checklist(employeeId),
    enabled: enabled && !!employeeId,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      employeeId,
      documentType,
      file,
    }: {
      employeeId: string;
      documentType: string;
      file: File;
    }) => documentsApi.upload(employeeId, documentType, file),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      queryClient.invalidateQueries({
        queryKey: queryKeys.documents.checklist(variables.employeeId),
      });
      toast.success("Document uploaded");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to upload document");
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      toast.success("Document removed");
    },
    onError: (error) => {
      toast.error(error instanceof ApiError ? error.detail : "Unable to remove document");
    },
  });
}
