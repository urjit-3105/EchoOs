// Pure helpers for deriving onboarding-portal stepper state.
//
// Hard rule from the spec: "resume later" must work with zero client storage.
// The token in the URL is the whole session - every reload re-derives the
// current step from the server's progress payload. Nothing here reads or
// writes localStorage/sessionStorage.

import type { EmployeeStatus, PortalProgress } from "@/types";

export type PortalStepKey =
  | "profile"
  | "documents"
  | "policies"
  | "terms"
  | "tracking";

export const PORTAL_STEP_ORDER: PortalStepKey[] = [
  "profile",
  "documents",
  "policies",
  "terms",
  "tracking",
];

export const PORTAL_STEP_LABELS: Record<PortalStepKey, string> = {
  profile: "Profile",
  documents: "Documents",
  policies: "Policies",
  terms: "Terms",
  tracking: "Track Progress",
};

export interface DerivedStepState {
  /** The step the server-side progress says the employee is on right now. */
  current: PortalStepKey;
  /** Steps that are fully done and safe to revisit read-only. */
  completed: Set<PortalStepKey>;
}

const STATUS_FALLBACK: Record<EmployeeStatus, { current: PortalStepKey; completedThrough: number }> = {
  invited: { current: "profile", completedThrough: -1 },
  accepted: { current: "profile", completedThrough: -1 },
  profile_pending: { current: "profile", completedThrough: -1 },
  documents_pending: { current: "documents", completedThrough: 0 },
  verifying: { current: "tracking", completedThrough: 3 },
  awaiting_approval: { current: "tracking", completedThrough: 3 },
  provisioning: { current: "tracking", completedThrough: 3 },
  active: { current: "tracking", completedThrough: 4 },
  rejected: { current: "tracking", completedThrough: 3 },
};

/**
 * Works out which step to show and which steps are done.
 *
 * Prefers the granular `steps[]` the backend can send in `PortalProgress`
 * (keyed the same as `PORTAL_STEP_ORDER`) and falls back to a coarse mapping
 * off the employee's overall status when that array isn't populated yet -
 * keeps the UI useful before the backend ships the fine-grained payload.
 */
export function deriveStepState(progress?: PortalProgress | null): DerivedStepState {
  const completed = new Set<PortalStepKey>();

  const serverSteps = progress?.steps?.filter((step) =>
    PORTAL_STEP_ORDER.includes(step.key as PortalStepKey)
  );

  if (serverSteps && serverSteps.length > 0) {
    let current: PortalStepKey | undefined;
    for (const step of serverSteps) {
      const key = step.key as PortalStepKey;
      if (step.completed) completed.add(key);
      if (step.active && !current) current = key;
    }
    if (!current) {
      current = PORTAL_STEP_ORDER.find((key) => !completed.has(key)) ?? "tracking";
    }
    return { current, completed };
  }

  const status = progress?.status;
  const fallback = (status && STATUS_FALLBACK[status]) || STATUS_FALLBACK.accepted;
  PORTAL_STEP_ORDER.forEach((key, index) => {
    if (index <= fallback.completedThrough) completed.add(key);
  });
  return { current: fallback.current, completed };
}

export function isStepUnlocked(
  step: PortalStepKey,
  derived: DerivedStepState
): boolean {
  if (derived.completed.has(step)) return true;
  return PORTAL_STEP_ORDER.indexOf(step) <= PORTAL_STEP_ORDER.indexOf(derived.current);
}

/** The five AI agent stages shown by the WorkflowTracker, in execution order. */
export const AGENT_STAGES = [
  { key: "verification", label: "Verification" },
  { key: "compliance", label: "Compliance" },
  { key: "provisioning", label: "Provisioning" },
  { key: "monitoring", label: "Monitoring" },
  { key: "activation", label: "Activation" },
] as const;
