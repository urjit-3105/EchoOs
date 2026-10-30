"use client"

import * as React from "react"
import Link from "next/link"
import { Users } from "lucide-react"
import { useEmployees } from "@/hooks/useEmployees"
import { DataTable } from "@/components/DataTable"
import { QueryBoundary } from "@/components/QueryBoundary"
import { StatusChip, type StatusType } from "@/components/StatusChip"
import { Button } from "@/components/ui/button"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination"
import { DEPARTMENTS, STATUS_LABELS } from "@/constants"
import { formatDate } from "@/utils/format"
import type { Employee, EmployeeStatus } from "@/types"

const CHIP_STATUS: Record<string, StatusType> = {
  active: "success",
  accepted: "info",
  invited: "default",
  profile_pending: "warning",
  documents_pending: "warning",
  verifying: "info",
  awaiting_approval: "warning",
  provisioning: "info",
  rejected: "error",
}

const EMPLOYEE_STATUSES: EmployeeStatus[] = [
  "invited",
  "accepted",
  "profile_pending",
  "documents_pending",
  "verifying",
  "awaiting_approval",
  "provisioning",
  "active",
  "rejected",
]

const PAGE_SIZE = 10

export function EmployeeList() {
  const [search, setSearch] = React.useState("")
  const [statusFilter, setStatusFilter] = React.useState<EmployeeStatus | "all">("all")
  const [deptFilter, setDeptFilter] = React.useState<string>("all")
  const [page, setPage] = React.useState(0)

  const { data, isLoading, isError, error, refetch } = useEmployees({
    status: statusFilter === "all" ? undefined : statusFilter,
    search: search || undefined,
    limit: 200,
  })

  const filtered = React.useMemo(() => {
    const employees = data ?? []
    if (deptFilter === "all") return employees
    return employees.filter((emp) => emp.department === deptFilter)
  }, [data, deptFilter])

  React.useEffect(() => {
    setPage(0)
  }, [search, statusFilter, deptFilter])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, pageCount - 1)
  const paged = filtered.slice(currentPage * PAGE_SIZE, currentPage * PAGE_SIZE + PAGE_SIZE)

  const columns = [
    {
      header: "Name",
      cell: (item: Employee) => (
        <span className="font-medium text-zinc-900 dark:text-zinc-50">{item.full_name}</span>
      ),
    },
    { header: "Email", accessorKey: "email" as const },
    {
      header: "Department",
      cell: (item: Employee) => item.department ?? "—",
    },
    {
      header: "Job Title",
      cell: (item: Employee) => item.job_title ?? "—",
    },
    {
      header: "Status",
      cell: (item: Employee) => (
        <StatusChip status={CHIP_STATUS[item.status] ?? "default"} label={STATUS_LABELS[item.status]} />
      ),
    },
    {
      header: "Start Date",
      cell: (item: Employee) => formatDate(item.start_date),
    },
    {
      header: "Actions",
      cell: (item: Employee) => (
        <Link href={`/employees/${item.id}`}>
          <Button variant="ghost" size="sm">
            View
          </Button>
        </Link>
      ),
    },
  ]

  return (
    <QueryBoundary
      isLoading={isLoading}
      isError={isError}
      error={error}
      isEmpty={filtered.length === 0}
      emptyTitle="No employees yet"
      emptyMessage="Get started by inviting your first employee. The AI workforce will activate automatically."
      emptyIcon={<Users className="w-8 h-8 text-zinc-400" />}
      emptyAction={{ label: "Invite Employee", href: "/employees/invite" }}
      onRetry={() => refetch()}
      loadingVariant="table"
      loadingColumns={6}
    >
      <div className="space-y-4">
        <div className="flex flex-wrap gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as EmployeeStatus | "all")}
            className="h-8 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-2.5 text-sm text-zinc-900 dark:text-zinc-50 shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white"
          >
            <option value="all">All statuses</option>
            {EMPLOYEE_STATUSES.map((status) => (
              <option key={status} value={status}>
                {STATUS_LABELS[status]}
              </option>
            ))}
          </select>
          <select
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value)}
            className="h-8 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-2.5 text-sm text-zinc-900 dark:text-zinc-50 shadow-sm focus:outline-none focus:ring-2 focus:ring-black dark:focus:ring-white"
          >
            <option value="all">All departments</option>
            {DEPARTMENTS.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>
        </div>

        <DataTable
          data={paged}
          columns={columns}
          searchPlaceholder="Search employees by name or email..."
          onSearch={setSearch}
        />

        {pageCount > 1 && (
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  href="#"
                  onClick={(e) => {
                    e.preventDefault()
                    setPage((p) => Math.max(0, p - 1))
                  }}
                />
              </PaginationItem>
              {Array.from({ length: pageCount }).map((_, idx) => (
                <PaginationItem key={idx}>
                  <PaginationLink
                    href="#"
                    isActive={idx === currentPage}
                    onClick={(e) => {
                      e.preventDefault()
                      setPage(idx)
                    }}
                  >
                    {idx + 1}
                  </PaginationLink>
                </PaginationItem>
              ))}
              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={(e) => {
                    e.preventDefault()
                    setPage((p) => Math.min(pageCount - 1, p + 1))
                  }}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
      </div>
    </QueryBoundary>
  )
}
