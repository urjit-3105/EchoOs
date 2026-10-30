import { api } from "@/lib/api/client";
import type {
  AgentExecution,
  AgentInfo,
  ApiError as ApiErrorShape,
  Approval,
  AuditEntry,
  AuthResponse,
  DashboardStats,
  DocumentChecklistItem,
  DocumentRecord,
  Employee,
  EmployeeStatus,
  Invitation,
  Notification,
  Organization,
  PortalDetail,
  PortalPolicy,
  PortalProgress,
  PortalWorkflow,
  TaskStatus,
  ToolInfo,
  User,
  Workflow,
  WorkflowHistoryEntry,
  WorkflowStatus,
  WorkflowStatusDetail,
  WorkflowTask,
} from "@/types";

// Re-exported so consumers can `import type { ApiError } from "@/lib/api/endpoints"`
// without pulling the class implementation in as well, if they only need the shape.
export type { ApiErrorShape };

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  organization_name?: string;
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    api.post<AuthResponse>("/auth/register", payload, { skipAuth: true }),
  login: (payload: LoginPayload) =>
    api.post<AuthResponse>("/auth/login", payload, { skipAuth: true }),
  magicLink: (email: string) =>
    api.post<{ detail?: string }>("/auth/magic-link", { email }, { skipAuth: true }),
  magicLinkVerify: (token: string) =>
    api.post<AuthResponse>("/auth/magic-link/verify", { token }, { skipAuth: true }),
  passwordReset: (email: string) =>
    api.post<{ detail?: string }>("/auth/password-reset", { email }, { skipAuth: true }),
  passwordResetConfirm: (token: string, password: string) =>
    api.post<{ detail?: string }>(
      "/auth/password-reset/confirm",
      { token, password },
      { skipAuth: true }
    ),
  me: () => api.get<User>("/auth/me"),
  logout: () => api.post<void>("/auth/logout"),
};

// ---------------------------------------------------------------------------
// Organizations
// ---------------------------------------------------------------------------

export const organizationsApi = {
  list: () => api.get<Organization[]>("/organizations"),
  create: (payload: Partial<Organization>) =>
    api.post<Organization>("/organizations", payload),
  get: (id: string) => api.get<Organization>(`/organizations/${id}`),
  update: (id: string, payload: Partial<Organization>) =>
    api.patch<Organization>(`/organizations/${id}`, payload),
  current: () => api.get<Organization>("/organizations/current"),
};

// ---------------------------------------------------------------------------
// Employees
// ---------------------------------------------------------------------------

export interface EmployeeListParams {
  organization_id?: string;
  status?: EmployeeStatus;
  search?: string;
  limit?: number;
  offset?: number;
}

export const employeesApi = {
  list: async (params?: EmployeeListParams): Promise<Employee[]> => {
    const res = await api.get<any>("/employees", params as Record<string, unknown>);
    if (Array.isArray(res)) return res;
    if (res && Array.isArray(res.items)) return res.items;
    return [];
  },
  create: (payload: Partial<Employee>) => api.post<Employee>("/employees", payload),
  get: (id: string) => api.get<Employee>(`/employees/${id}`),
  update: (id: string, payload: Partial<Employee>) =>
    api.patch<Employee>(`/employees/${id}`, payload),
  remove: (id: string) => api.del<void>(`/employees/${id}`),
  stats: () => api.get<DashboardStats>("/employees/stats"),
};

// ---------------------------------------------------------------------------
// Invitations
// ---------------------------------------------------------------------------

export interface InvitationListParams {
  organization_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export const invitationsApi = {
  list: (params?: InvitationListParams) =>
    api.get<Invitation[]>("/invitations", params as Record<string, unknown>),
  create: (payload: Partial<Invitation>) =>
    api.post<Invitation>("/invitations", payload),
  byToken: (token: string) =>
    api.get<Invitation>(`/invitations/token/${token}`, undefined, { skipAuth: true }),
  accept: (token: string, payload?: Record<string, unknown>) =>
    api.post<AuthResponse>(`/invitations/token/${token}/accept`, payload, {
      skipAuth: true,
    }),
  resend: (id: string) => api.post<Invitation>(`/invitations/${id}/resend`),
  revoke: (id: string) => api.post<Invitation>(`/invitations/${id}/revoke`),
  qr: (id: string) => api.get<{ qr_code: string }>(`/invitations/${id}/qr`),
};

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

export const documentsApi = {
  list: (employeeId?: string) =>
    api.get<DocumentRecord[]>("/documents", { employee_id: employeeId }),
  upload: (employeeId: string, documentType: string, file: File) => {
    const formData = new FormData();
    formData.append("employee_id", employeeId);
    formData.append("document_type", documentType);
    formData.append("file", file);
    return api.upload<DocumentRecord>("/documents/upload", formData);
  },
  checklist: (employeeId: string) =>
    api.get<DocumentChecklistItem[]>(`/documents/checklist/${employeeId}`),
  remove: (id: string) => api.del<void>(`/documents/${id}`),
};

// ---------------------------------------------------------------------------
// Workflow
// ---------------------------------------------------------------------------

export interface WorkflowListParams {
  employee_id?: string;
  status?: WorkflowStatus;
  limit?: number;
  offset?: number;
}

export const workflowApi = {
  list: (params?: WorkflowListParams) =>
    api.get<Workflow[]>("/workflow", params as Record<string, unknown>),
  start: (payload: { employee_id: string; template_id?: string }) =>
    api.post<Workflow>("/workflow/start", payload),
  get: (id: string) => api.get<Workflow>(`/workflow/${id}`),
  status: (id: string) => api.get<WorkflowStatusDetail>(`/workflow/${id}/status`),
  history: (id: string) => api.get<WorkflowHistoryEntry[]>(`/workflow/${id}/history`),
  tasks: (id: string) => api.get<WorkflowTask[]>(`/workflow/${id}/tasks`),
  pause: (id: string) => api.post<Workflow>(`/workflow/${id}/pause`),
  resume: (id: string) => api.post<Workflow>(`/workflow/${id}/resume`),
  cancel: (id: string) => api.post<Workflow>(`/workflow/${id}/cancel`),
  retry: (id: string) => api.post<Workflow>(`/workflow/${id}/retry`),
  templates: () => api.get<{ id: string; name: string; description?: string }[]>(
    "/workflow/templates"
  ),
};

// ---------------------------------------------------------------------------
// Tasks
// ---------------------------------------------------------------------------

export interface TaskListParams {
  workflow_id?: string;
  status?: TaskStatus;
}

export const tasksApi = {
  list: (params?: TaskListParams) =>
    api.get<WorkflowTask[]>("/tasks", params as Record<string, unknown>),
  get: (id: string) => api.get<WorkflowTask>(`/tasks/${id}`),
  retry: (id: string) => api.post<WorkflowTask>(`/tasks/${id}/retry`),
};

// ---------------------------------------------------------------------------
// Approvals
// ---------------------------------------------------------------------------

export const approvalsApi = {
  list: (status: string = "pending") =>
    api.get<Approval[]>("/approvals", { status }),
  get: (id: string) => api.get<Approval>(`/approvals/${id}`),
  decide: (id: string, payload: { approved: boolean; comments?: string }) =>
    api.post<Approval>(`/approvals/${id}/decision`, payload),
};

// ---------------------------------------------------------------------------
// Agents
// ---------------------------------------------------------------------------

export const agentsApi = {
  list: () => api.get<AgentInfo[]>("/agents"),
  get: (name: string) => api.get<AgentInfo>(`/agents/${name}`),
  executions: (workflowId?: string) =>
    api.get<AgentExecution[]>("/agents/executions", { workflow_id: workflowId }),
  tools: () => api.get<ToolInfo[]>("/agents/tools"),
};

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

export const notificationsApi = {
  list: () => api.get<Notification[]>("/notifications"),
  markRead: (id: string) => api.post<Notification>(`/notifications/${id}/read`),
  markAllRead: () => api.post<void>("/notifications/read-all"),
  unreadCount: () => api.get<{ count: number }>("/notifications/unread-count"),
};

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

export interface AuditListParams {
  resource_type?: string;
  resource_id?: string;
  limit?: number;
}

export const auditApi = {
  list: (params?: AuditListParams) =>
    api.get<AuditEntry[]>("/audit", params as Record<string, unknown>),
};

// ---------------------------------------------------------------------------
// Monitoring
// ---------------------------------------------------------------------------

export const monitoringApi = {
  health: () => api.get<{ status: string; [key: string]: unknown }>("/monitoring/health"),
  metrics: () => api.get<Record<string, unknown>>("/monitoring/metrics"),
};

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

export const settingsApi = {
  get: () => api.get<Record<string, unknown>>("/settings"),
  update: (payload: Record<string, unknown>) =>
    api.patch<Record<string, unknown>>("/settings", payload),
};

// ---------------------------------------------------------------------------
// Portal (public, no auth)
// ---------------------------------------------------------------------------

export const portalApi = {
  /** GET /portal/{token} - richer welcome-screen payload (org branding, inviter, employee). */
  get: (token: string) =>
    api.get<PortalDetail>(`/portal/${token}`, undefined, { skipAuth: true }),
  invitation: (token: string) =>
    api.get<Invitation>(`/invitations/token/${token}`, undefined, { skipAuth: true }),
  acceptInvitation: (token: string, payload?: Record<string, unknown>) =>
    api.post<AuthResponse>(`/invitations/token/${token}/accept`, payload, {
      skipAuth: true,
    }),
  progress: (token: string) =>
    api.get<PortalProgress>(`/portal/${token}/progress`, undefined, { skipAuth: true }),
  submitProfile: (token: string, payload: Record<string, unknown>) =>
    api.post<PortalProgress>(`/portal/${token}/profile`, payload, { skipAuth: true }),
  documents: (token: string) =>
    api.get<DocumentRecord[]>(`/portal/${token}/documents`, undefined, { skipAuth: true }),
  uploadDocument: (token: string, documentType: string, file: File) => {
    const formData = new FormData();
    formData.append("document_type", documentType);
    formData.append("file", file);
    return api.upload<DocumentRecord>(`/portal/${token}/documents`, formData, {
      skipAuth: true,
    });
  },
  deleteDocument: (token: string, documentId: string) =>
    api.del<void>(`/portal/${token}/documents/${documentId}`, { skipAuth: true }),
  acceptTerms: (token: string) =>
    api.post<{ detail?: string }>(`/portal/${token}/accept-terms`, undefined, {
      skipAuth: true,
    }),
  policies: (token: string) =>
    api.get<PortalPolicy[]>(`/portal/${token}/policies`, undefined, { skipAuth: true }),
  workflow: (token: string) =>
    api.get<PortalWorkflow>(`/portal/${token}/workflow`, undefined, { skipAuth: true }),
};
