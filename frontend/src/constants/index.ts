import type {
  ApprovalStatus,
  DocumentStatus,
  EmployeeStatus,
  InvitationStatus,
  TaskStatus,
  UserRole,
  WorkflowStatus,
} from "@/types";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  Bell,
  Bot,
  Settings,
  FileText,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Status labels
// ---------------------------------------------------------------------------

export const STATUS_LABELS: Record<
  EmployeeStatus | WorkflowStatus | TaskStatus | ApprovalStatus | DocumentStatus | InvitationStatus,
  string
> = {
  invited: "Invited",
  accepted: "Accepted",
  profile_pending: "Profile Pending",
  documents_pending: "Documents Pending",
  verifying: "Verifying",
  awaiting_approval: "Awaiting Approval",
  provisioning: "Provisioning",
  active: "Active",
  rejected: "Rejected",
  pending: "Pending",
  running: "Running",
  paused: "Paused",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
  skipped: "Skipped",
  retrying: "Retrying",
  approved: "Approved",
  uploaded: "Uploaded",
  verified: "Verified",
  sent: "Sent",
  expired: "Expired",
  revoked: "Revoked",
};

// Tailwind class strings matching the app's zinc/dark palette + semantic accents.
export const STATUS_COLORS: Record<
  EmployeeStatus | WorkflowStatus | TaskStatus | ApprovalStatus | DocumentStatus | InvitationStatus,
  string
> = {
  invited: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  accepted: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  profile_pending: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  documents_pending: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  verifying: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  awaiting_approval: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  provisioning: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  active: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  rejected: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  pending: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  running: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  paused: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  completed: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  failed: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  cancelled: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  skipped: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  retrying: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
  approved: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  uploaded: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  verified: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  sent: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  expired: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  revoked: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Admin",
  hr: "HR",
  manager: "Manager",
  employee: "Employee",
};

export const DEPARTMENTS = [
  "Engineering",
  "Product",
  "Design",
  "Sales",
  "Marketing",
  "Finance",
  "Human Resources",
  "Operations",
  "Legal",
  "Customer Success",
] as const;

export const DOCUMENT_TYPES = [
  { value: "government_id", label: "Government ID" },
  { value: "passport", label: "Passport" },
  { value: "proof_of_address", label: "Proof of Address" },
  { value: "tax_form", label: "Tax Form" },
  { value: "bank_details", label: "Bank Details" },
  { value: "signed_offer_letter", label: "Signed Offer Letter" },
  { value: "nda", label: "NDA" },
  { value: "background_check_consent", label: "Background Check Consent" },
] as const;

export const WORKFLOW_STAGES = [
  { key: "invited", label: "Invited" },
  { key: "profile", label: "Profile" },
  { key: "documents", label: "Documents" },
  { key: "verification", label: "Verification" },
  { key: "approval", label: "Approval" },
  { key: "provisioning", label: "Provisioning" },
  { key: "active", label: "Active" },
] as const;

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  roles?: UserRole[];
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Employees", href: "/employees", icon: Users },
  { label: "Agents", href: "/agents", icon: Bot },
  { label: "Workflows", href: "/workflows", icon: Briefcase },
  { label: "Documents", href: "/documents", icon: FileText },
  { label: "Approvals", href: "/approvals", icon: ShieldCheck },
  { label: "Notifications", href: "/notifications", icon: Bell },
  { label: "Settings", href: "/settings", icon: Settings },
];
