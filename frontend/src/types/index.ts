// Shared TypeScript types mirroring the ECHO WorkforceOS backend contract.
// Keep in sync with the backend's Pydantic schemas (see AGENTS handoff notes).

// ---------------------------------------------------------------------------
// String unions
// ---------------------------------------------------------------------------

export type UserRole = "admin" | "hr" | "manager" | "employee";

export type EmployeeStatus =
  | "invited"
  | "accepted"
  | "profile_pending"
  | "documents_pending"
  | "verifying"
  | "awaiting_approval"
  | "provisioning"
  | "active"
  | "rejected";

export type WorkflowStatus =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export type TaskStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "skipped"
  | "retrying";

export type ApprovalStatus = "pending" | "approved" | "rejected";

export type DocumentStatus =
  | "pending"
  | "uploaded"
  | "verifying"
  | "verified"
  | "rejected";

export type InvitationStatus =
  | "pending"
  | "sent"
  | "accepted"
  | "expired"
  | "revoked";

export type NotificationType =
  | "info"
  | "success"
  | "warning"
  | "error"
  | "approval_request"
  | "task_update"
  | "workflow_update";

// ---------------------------------------------------------------------------
// Core entities
// ---------------------------------------------------------------------------

export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: UserRole;
  organization_id?: string;
  avatar_url?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Organization {
  id: string;
  name: string;
  industry?: string;
  size?: string;
  logo_url?: string;
  settings?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface Employee {
  id: string;
  organization_id?: string;
  full_name: string;
  email: string;
  phone?: string;
  department?: string;
  job_title?: string;
  manager_id?: string;
  status: EmployeeStatus;
  start_date?: string;
  compliance_score?: number;
  avatar_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Invitation {
  id: string;
  organization_id?: string;
  employee_id?: string;
  email: string;
  full_name?: string;
  role?: UserRole;
  department?: string;
  job_title?: string;
  status: InvitationStatus;
  token?: string;
  expires_at?: string;
  created_at?: string;
  updated_at?: string;
  // Portal-only convenience fields (populated by GET /portal/{token}) so the
  // welcome screen can render organization branding without a second round trip.
  organization_name?: string;
  organization_logo_url?: string;
  invited_by_name?: string;
}

export interface DocumentRecord {
  id: string;
  employee_id: string;
  document_type: string;
  file_name?: string;
  file_url?: string;
  file_size?: number;
  status: DocumentStatus;
  rejection_reason?: string;
  uploaded_at?: string;
  verified_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface DocumentChecklistItem {
  document_type: string;
  label?: string;
  required: boolean;
  uploaded?: boolean;
  status: DocumentStatus;
  document_id?: string;
}

export interface Workflow {
  id: string;
  employee_id: string;
  organization_id?: string;
  template_id?: string;
  template_name?: string;
  status: WorkflowStatus;
  current_stage?: string;
  progress?: number;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface WorkflowTask {
  id: string;
  workflow_id: string;
  name: string;
  description?: string;
  status: TaskStatus;
  agent_name?: string;
  stage?: string;
  order?: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface WorkflowStatusDetail {
  id: string;
  status: WorkflowStatus;
  current_stage?: string;
  progress?: number;
  tasks_total?: number;
  tasks_completed?: number;
  tasks_failed?: number;
  updated_at?: string;
}

export interface WorkflowHistoryEntry {
  id: string;
  workflow_id: string;
  event: string;
  message?: string;
  actor?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface ExecutionPlan {
  id?: string;
  workflow_id?: string;
  steps: Array<{
    id: string;
    name: string;
    agent_name?: string;
    status?: TaskStatus;
    depends_on?: string[];
  }>;
}

export interface AgentInfo {
  id?: string;
  name: string;
  display_name?: string;
  description?: string;
  status?: "idle" | "running" | "error" | "disabled";
  capabilities?: string[];
  version?: string;
  total_tasks?: number;
}

export type Agent = AgentInfo;

export interface AgentExecution {
  id: string;
  agent_name: string;
  workflow_id?: string;
  task_id?: string;
  status: TaskStatus;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
}

export interface ToolInfo {
  name: string;
  description?: string;
  agent_name?: string;
  parameters?: Record<string, unknown>;
}

export interface Approval {
  id: string;
  workflow_id?: string;
  task_id?: string;
  employee_id?: string;
  employee_name?: string;
  title: string;
  description?: string;
  status: ApprovalStatus;
  requested_by?: string;
  decided_by?: string;
  comments?: string;
  created_at?: string;
  decided_at?: string;
}

export interface Notification {
  id: string;
  user_id?: string;
  type: NotificationType;
  title: string;
  message?: string;
  is_read: boolean;
  link?: string;
  created_at: string;
}

export interface AuditEntry {
  id: string;
  resource_type: string;
  resource_id: string;
  action: string;
  actor?: string;
  changes?: Record<string, unknown>;
  created_at: string;
}

export interface DashboardStats {
  total_employees?: number;
  active_employees?: number;
  pending_onboarding?: number;
  completed_onboarding?: number;
  average_compliance_score?: number;
  by_status?: Partial<Record<EmployeeStatus, number>>;
  by_department?: Record<string, number>;
}

export interface PortalProgress {
  token: string;
  employee_name?: string;
  organization_name?: string;
  status: EmployeeStatus;
  current_step?: string;
  steps?: Array<{
    key: string;
    label: string;
    completed: boolean;
    active?: boolean;
  }>;
  documents_checklist?: DocumentChecklistItem[];
}

export interface PortalDetail {
  invitation: Invitation;
  organization?: Organization;
  employee?: Employee;
}

export interface PortalPolicy {
  id: string;
  title: string;
  content?: string;
  url?: string;
}

/** One entry in the five-stage AI onboarding tracker shown on the "Track progress" step. */
export interface PortalWorkflowStage {
  key: string;
  label: string;
  status: TaskStatus | WorkflowStatus;
}

export interface PortalWorkflow {
  workflow?: Workflow;
  tasks?: WorkflowTask[];
  stages?: PortalWorkflowStage[];
}

export interface AuthResponse {
  access_token: string;
  token_type?: string;
  user?: User;
}

export interface ApiError {
  detail: string;
}
