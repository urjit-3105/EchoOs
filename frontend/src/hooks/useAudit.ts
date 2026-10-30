"use client";

import { useQuery } from "@tanstack/react-query";
import { auditApi, type AuditListParams } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";

export function useAudit(params?: AuditListParams) {
  return useQuery({
    queryKey: queryKeys.audit.list(params),
    queryFn: () => auditApi.list(params),
  });
}
