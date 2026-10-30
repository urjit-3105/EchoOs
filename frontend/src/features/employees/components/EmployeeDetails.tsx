"use client"

import * as React from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { StatusChip, type StatusType } from "@/components/StatusChip"
import { TimelineItem } from "@/components/TimelineItem"
import { QueryBoundary } from "@/components/QueryBoundary"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog"
import { User, FileText, Activity, Clock, Briefcase, Mail, Building, Pencil } from "lucide-react"
import { useEmployee, useUpdateEmployee } from "@/hooks/useEmployees"
import { useDocumentChecklist } from "@/hooks/useDocuments"
import { useWorkflows, useWorkflowHistory, useStartWorkflow } from "@/hooks/useWorkflows"
import { useInvitations, useResendInvitation } from "@/hooks/useInvitations"
import { useAudit } from "@/hooks/useAudit"
import { DEPARTMENTS, STATUS_LABELS } from "@/constants"
import { formatRelativeTime, initials } from "@/utils/format"

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
  pending: "default",
  sent: "info",
  expired: "default",
  revoked: "error",
  completed: "success",
  running: "info",
  failed: "error",
  cancelled: "default",
  paused: "warning",
  uploaded: "info",
  verified: "success",
}

interface EmployeeDetailsProps {
  employeeId: string
}

interface EditFormState {
  full_name: string
  department: string
  job_title: string
  phone: string
}

export function EmployeeDetails({ employeeId }: EmployeeDetailsProps) {
  const { data: employee, isLoading, isError, error, refetch } = useEmployee(employeeId)
  const { data: checklist, isLoading: checklistLoading, isError: checklistError } =
    useDocumentChecklist(employeeId)
  const { data: workflows } = useWorkflows({ employee_id: employeeId })
  const workflow = workflows?.[0]
  const { data: history, isLoading: historyLoading, isError: historyError } = useWorkflowHistory(
    workflow?.id ?? "",
    !!workflow?.id
  )
  const { data: invitations } = useInvitations({ limit: 200 })
  const invitation = invitations?.find((inv) => inv.employee_id === employeeId)
  const { data: activity, isLoading: activityLoading, isError: activityError } = useAudit({
    resource_type: "employee",
    resource_id: employeeId,
  })

  const resendInvitation = useResendInvitation()
  const startWorkflow = useStartWorkflow()
  const updateEmployee = useUpdateEmployee(employeeId)

  const [editOpen, setEditOpen] = React.useState(false)
  const [form, setForm] = React.useState<EditFormState>({
    full_name: "",
    department: "",
    job_title: "",
    phone: "",
  })

  React.useEffect(() => {
    if (employee) {
      setForm({
        full_name: employee.full_name ?? "",
        department: employee.department ?? "",
        job_title: employee.job_title ?? "",
        phone: employee.phone ?? "",
      })
    }
  }, [employee])

  const hasActiveWorkflow =
    !!workflow && workflow.status !== "completed" && workflow.status !== "cancelled" && workflow.status !== "failed"

  const handleSaveEdit = (e: React.FormEvent) => {
    e.preventDefault()
    updateEmployee.mutate(
      {
        full_name: form.full_name,
        department: form.department || undefined,
        job_title: form.job_title || undefined,
        phone: form.phone || undefined,
      },
      { onSuccess: () => setEditOpen(false) }
    )
  }

  return (
    <QueryBoundary
      isLoading={isLoading}
      isError={isError}
      error={error}
      onRetry={() => refetch()}
      loadingVariant="card"
    >
      {employee && (
        <div className="space-y-6">
          {/* Profile Header */}
          <Card>
            <CardContent className="p-6 flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
              <div className="flex gap-4 items-center">
                <div className="h-20 w-20 bg-primary/10 rounded-full flex items-center justify-center text-primary text-2xl font-bold">
                  {initials(employee.full_name)}
                </div>
                <div>
                  <h2 className="text-2xl font-bold">{employee.full_name}</h2>
                  <div className="flex flex-wrap gap-4 mt-2 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Briefcase size={14} /> {employee.job_title ?? "—"}
                    </span>
                    <span className="flex items-center gap-1">
                      <Building size={14} /> {employee.department ?? "—"}
                    </span>
                    <span className="flex items-center gap-1">
                      <Mail size={14} /> {employee.email}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex flex-col gap-2 items-end">
                <StatusChip status={CHIP_STATUS[employee.status] ?? "default"} label={STATUS_LABELS[employee.status]} />
                {typeof employee.compliance_score === "number" && (
                  <span className="text-sm font-medium">Compliance: {employee.compliance_score}%</span>
                )}
                <div className="flex gap-2 mt-2">
                  {!hasActiveWorkflow && (
                    <Button
                      size="sm"
                      onClick={() => startWorkflow.mutate({ employee_id: employeeId })}
                      disabled={startWorkflow.isPending}
                    >
                      Start Onboarding
                    </Button>
                  )}
                  {invitation && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => resendInvitation.mutate(invitation.id)}
                      disabled={resendInvitation.isPending}
                    >
                      Resend Invitation
                    </Button>
                  )}
                  <Dialog open={editOpen} onOpenChange={setEditOpen}>
                    <DialogTrigger render={<Button size="sm" variant="ghost" />}>
                      <Pencil size={14} className="mr-1.5" /> Edit
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Edit Employee</DialogTitle>
                      </DialogHeader>
                      <form onSubmit={handleSaveEdit} className="space-y-3">
                        <div>
                          <label className="block text-xs font-medium text-muted-foreground mb-1">Full Name</label>
                          <Input
                            value={form.full_name}
                            onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-muted-foreground mb-1">Department</label>
                          <select
                            value={form.department}
                            onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))}
                            className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm text-foreground dark:bg-input/30"
                          >
                            <option value="">—</option>
                            {DEPARTMENTS.map((dept) => (
                              <option key={dept} value={dept}>
                                {dept}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-muted-foreground mb-1">Job Title</label>
                          <Input
                            value={form.job_title}
                            onChange={(e) => setForm((f) => ({ ...f, job_title: e.target.value }))}
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-muted-foreground mb-1">Phone</label>
                          <Input
                            value={form.phone}
                            onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                          />
                        </div>
                        <DialogFooter>
                          <Button type="submit" disabled={updateEmployee.isPending}>
                            {updateEmployee.isPending ? "Saving..." : "Save Changes"}
                          </Button>
                        </DialogFooter>
                      </form>
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            </CardContent>
          </Card>

          {workflow && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-base">
                  <span>Onboarding Workflow</span>
                  <StatusChip
                    status={CHIP_STATUS[workflow.status] ?? "default"}
                    label={STATUS_LABELS[workflow.status] ?? workflow.status}
                  />
                </CardTitle>
                <CardDescription>Current stage: {workflow.current_stage ?? "—"}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-2 w-full rounded-full bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${Math.min(100, Math.max(0, workflow.progress ?? 0))}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-2">{workflow.progress ?? 0}% complete</p>
              </CardContent>
            </Card>
          )}

          {/* Details Tabs */}
          <Tabs defaultValue="timeline" className="w-full">
            <TabsList className="w-full justify-start border-b rounded-none h-auto p-0 bg-transparent">
              <TabsTrigger
                value="timeline"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent py-3 px-4"
              >
                <Clock size={16} className="mr-2" /> Timeline
              </TabsTrigger>
              <TabsTrigger
                value="documents"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent py-3 px-4"
              >
                <FileText size={16} className="mr-2" /> Documents
              </TabsTrigger>
              <TabsTrigger
                value="manager"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent py-3 px-4"
              >
                <User size={16} className="mr-2" /> Manager Info
              </TabsTrigger>
              <TabsTrigger
                value="activity"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent py-3 px-4"
              >
                <Activity size={16} className="mr-2" /> Recent Activity
              </TabsTrigger>
            </TabsList>

            <TabsContent value="timeline" className="p-4 pt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Onboarding Timeline</CardTitle>
                </CardHeader>
                <CardContent>
                  <QueryBoundary
                    isLoading={!!workflow && historyLoading}
                    isError={historyError}
                    isEmpty={!workflow || (history?.length ?? 0) === 0}
                    emptyMessage="No timeline events yet."
                    loadingVariant="list"
                  >
                    {history?.map((entry, idx) => (
                      <TimelineItem
                        key={entry.id}
                        title={entry.event}
                        description={entry.message}
                        time={formatRelativeTime(entry.created_at)}
                        isActive={idx === 0}
                        isLast={idx === history.length - 1}
                      />
                    ))}
                  </QueryBoundary>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="documents" className="p-4 pt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Document Checklist</CardTitle>
                </CardHeader>
                <CardContent>
                  <QueryBoundary
                    isLoading={checklistLoading}
                    isError={checklistError}
                    isEmpty={(checklist?.length ?? 0) === 0}
                    emptyMessage="No documents required."
                    loadingVariant="list"
                  >
                    <div className="space-y-3">
                      {checklist?.map((doc) => (
                        <div
                          key={doc.document_type}
                          className="flex items-center justify-between border-b last:border-0 pb-3 last:pb-0"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">{doc.label ?? doc.document_type}</span>
                            {doc.required && (
                              <Badge variant="outline" className="text-xs">
                                Required
                              </Badge>
                            )}
                          </div>
                          <StatusChip
                            status={CHIP_STATUS[doc.status] ?? "default"}
                            label={STATUS_LABELS[doc.status] ?? doc.status}
                          />
                        </div>
                      ))}
                    </div>
                  </QueryBoundary>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="manager" className="p-4 pt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Manager Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {employee.manager_id ? (
                    <div className="flex justify-between max-w-sm">
                      <span className="text-muted-foreground">Manager ID:</span>
                      <span className="font-medium">{employee.manager_id}</span>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No manager assigned.</p>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="activity" className="p-4 pt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Recent Activity</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <QueryBoundary
                    isLoading={activityLoading}
                    isError={activityError}
                    isEmpty={(activity?.length ?? 0) === 0}
                    emptyMessage="No recent activity."
                    loadingVariant="list"
                  >
                    {activity?.map((entry) => (
                      <div
                        key={entry.id}
                        className="flex justify-between items-center border-b last:border-0 pb-3 last:pb-0"
                      >
                        <span className="text-sm font-medium">{entry.action}</span>
                        <span className="text-xs text-muted-foreground">{formatRelativeTime(entry.created_at)}</span>
                      </div>
                    ))}
                  </QueryBoundary>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </QueryBoundary>
  )
}
