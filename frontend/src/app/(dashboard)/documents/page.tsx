"use client";

import * as React from "react";
import Link from "next/link";
import { Download, FileText } from "lucide-react";
import { useDocuments } from "@/hooks/useDocuments";
import { useEmployees } from "@/hooks/useEmployees";
import { QueryBoundary } from "@/components/QueryBoundary";
import { StatusChip, type StatusType } from "@/components/StatusChip";
import { STATUS_LABELS, DOCUMENT_TYPES } from "@/constants";
import { formatDateTime } from "@/utils/format";
import type { DocumentStatus } from "@/types";

const DOCUMENT_STATUSES: DocumentStatus[] = [
  "pending",
  "uploaded",
  "verifying",
  "verified",
  "rejected",
];

const DOCUMENT_STATUS_CHIP: Record<DocumentStatus, StatusType> = {
  pending: "default",
  uploaded: "info",
  verifying: "info",
  verified: "success",
  rejected: "error",
};

const DOCUMENT_TYPE_LABELS: Record<string, string> = Object.fromEntries(
  DOCUMENT_TYPES.map((type) => [type.value, type.label])
);

export default function DocumentsPage() {
  const [statusFilter, setStatusFilter] = React.useState<DocumentStatus | "all">("all");

  const { data: documents, isLoading, isError, error, refetch } = useDocuments();
  const { data: employees } = useEmployees({ limit: 200 });

  const employeeMap = React.useMemo(() => {
    const map = new Map<string, string>();
    (employees ?? []).forEach((emp) => map.set(emp.id, emp.full_name));
    return map;
  }, [employees]);

  const filteredDocuments = React.useMemo(() => {
    if (!documents) return [];
    if (statusFilter === "all") return documents;
    return documents.filter((doc) => doc.status === statusFilter);
  }, [documents, statusFilter]);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Documents
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Review documents uploaded across all employees.
          </p>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as DocumentStatus | "all")}
          className="h-9 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 text-sm text-zinc-900 dark:text-zinc-50 shadow-sm focus:outline-none focus:ring-2 focus:ring-zinc-300 dark:focus:ring-zinc-700"
        >
          <option value="all">All statuses</option>
          {DOCUMENT_STATUSES.map((status) => (
            <option key={status} value={status}>
              {STATUS_LABELS[status]}
            </option>
          ))}
        </select>
      </div>

      <QueryBoundary
        isLoading={isLoading}
        isError={isError}
        error={error}
        onRetry={() => refetch()}
        isEmpty={filteredDocuments.length === 0}
        emptyTitle="No documents found"
        emptyMessage="Documents uploaded by employees during onboarding will appear here."
        emptyIcon={<FileText className="w-8 h-8 text-zinc-400" />}
        loadingVariant="table"
        loadingColumns={6}
      >
        <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-zinc-50 dark:bg-zinc-800/50 text-zinc-500 dark:text-zinc-400 border-b border-zinc-200 dark:border-zinc-800">
              <tr>
                <th className="px-6 py-4 font-medium">File</th>
                <th className="px-6 py-4 font-medium">Type</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Owner</th>
                <th className="px-6 py-4 font-medium">Uploaded</th>
                <th className="px-6 py-4 font-medium text-right">File</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800 text-zinc-900 dark:text-zinc-50">
              {filteredDocuments.map((doc) => {
                const ownerName = employeeMap.get(doc.employee_id);
                return (
                  <tr
                    key={doc.id}
                    className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
                  >
                    <td className="px-6 py-4 font-medium">
                      {doc.file_name ?? doc.document_type}
                    </td>
                    <td className="px-6 py-4 text-zinc-500 dark:text-zinc-400">
                      {DOCUMENT_TYPE_LABELS[doc.document_type] ?? doc.document_type}
                    </td>
                    <td className="px-6 py-4">
                      <StatusChip
                        status={DOCUMENT_STATUS_CHIP[doc.status]}
                        label={STATUS_LABELS[doc.status]}
                      />
                    </td>
                    <td className="px-6 py-4">
                      {ownerName ? (
                        <Link
                          href={`/employees/${doc.employee_id}`}
                          className="text-zinc-900 dark:text-zinc-50 hover:underline"
                        >
                          {ownerName}
                        </Link>
                      ) : (
                        <span className="text-zinc-400">Unknown</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-zinc-500 dark:text-zinc-400">
                      {formatDateTime(doc.uploaded_at ?? doc.created_at)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {doc.file_url ? (
                        <a
                          href={doc.file_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 text-zinc-500 hover:text-zinc-900 dark:hover:text-white transition-colors"
                        >
                          <Download className="w-4 h-4" />
                          Download
                        </a>
                      ) : (
                        <span className="text-zinc-300 dark:text-zinc-700">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </QueryBoundary>
    </div>
  );
}
