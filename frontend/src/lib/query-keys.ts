// Centralised, hierarchical query-key factories for TanStack Query.
// Keeping every key in one place makes cache invalidation predictable.

import type {
  AuditListParams,
  EmployeeListParams,
  InvitationListParams,
  TaskListParams,
  WorkflowListParams,
} from "@/lib/api/endpoints";

export const queryKeys = {
  auth: {
    all: ["auth"] as const,
    me: () => [...queryKeys.auth.all, "me"] as const,
  },
  organizations: {
    all: ["organizations"] as const,
    list: () => [...queryKeys.organizations.all, "list"] as const,
    current: () => [...queryKeys.organizations.all, "current"] as const,
    detail: (id: string) => [...queryKeys.organizations.all, "detail", id] as const,
  },
  employees: {
    all: ["employees"] as const,
    list: (filters?: EmployeeListParams) =>
      [...queryKeys.employees.all, "list", filters ?? {}] as const,
    detail: (id: string) => [...queryKeys.employees.all, "detail", id] as const,
    stats: () => [...queryKeys.employees.all, "stats"] as const,
  },
  invitations: {
    all: ["invitations"] as const,
    list: (filters?: InvitationListParams) =>
      [...queryKeys.invitations.all, "list", filters ?? {}] as const,
    detail: (id: string) => [...queryKeys.invitations.all, "detail", id] as const,
    byToken: (token: string) =>
      [...queryKeys.invitations.all, "token", token] as const,
    qr: (id: string) => [...queryKeys.invitations.all, "qr", id] as const,
  },
  documents: {
    all: ["documents"] as const,
    list: (employeeId?: string) =>
      [...queryKeys.documents.all, "list", employeeId ?? "all"] as const,
    checklist: (employeeId: string) =>
      [...queryKeys.documents.all, "checklist", employeeId] as const,
  },
  workflows: {
    all: ["workflows"] as const,
    list: (filters?: WorkflowListParams) =>
      [...queryKeys.workflows.all, "list", filters ?? {}] as const,
    detail: (id: string) => [...queryKeys.workflows.all, "detail", id] as const,
    status: (id: string) => [...queryKeys.workflows.all, "status", id] as const,
    history: (id: string) => [...queryKeys.workflows.all, "history", id] as const,
    tasks: (id: string) => [...queryKeys.workflows.all, "tasks", id] as const,
    templates: () => [...queryKeys.workflows.all, "templates"] as const,
  },
  tasks: {
    all: ["tasks"] as const,
    list: (filters?: TaskListParams) =>
      [...queryKeys.tasks.all, "list", filters ?? {}] as const,
    detail: (id: string) => [...queryKeys.tasks.all, "detail", id] as const,
  },
  approvals: {
    all: ["approvals"] as const,
    list: (status?: string) =>
      [...queryKeys.approvals.all, "list", status ?? "pending"] as const,
    detail: (id: string) => [...queryKeys.approvals.all, "detail", id] as const,
  },
  agents: {
    all: ["agents"] as const,
    list: () => [...queryKeys.agents.all, "list"] as const,
    detail: (name: string) => [...queryKeys.agents.all, "detail", name] as const,
    executions: (workflowId?: string) =>
      [...queryKeys.agents.all, "executions", workflowId ?? "all"] as const,
    tools: () => [...queryKeys.agents.all, "tools"] as const,
  },
  notifications: {
    all: ["notifications"] as const,
    list: () => [...queryKeys.notifications.all, "list"] as const,
    unreadCount: () => [...queryKeys.notifications.all, "unread-count"] as const,
  },
  audit: {
    all: ["audit"] as const,
    list: (filters?: AuditListParams) =>
      [...queryKeys.audit.all, "list", filters ?? {}] as const,
  },
  monitoring: {
    all: ["monitoring"] as const,
    health: () => [...queryKeys.monitoring.all, "health"] as const,
    metrics: () => [...queryKeys.monitoring.all, "metrics"] as const,
  },
  settings: {
    all: ["settings"] as const,
    detail: () => [...queryKeys.settings.all, "detail"] as const,
  },
  portal: {
    all: ["portal"] as const,
    detail: (token: string) => [...queryKeys.portal.all, "detail", token] as const,
    invitation: (token: string) => [...queryKeys.portal.all, "invitation", token] as const,
    progress: (token: string) => [...queryKeys.portal.all, "progress", token] as const,
    documents: (token: string) => [...queryKeys.portal.all, "documents", token] as const,
    policies: (token: string) => [...queryKeys.portal.all, "policies", token] as const,
    workflow: (token: string) => [...queryKeys.portal.all, "workflow", token] as const,
  },
};
