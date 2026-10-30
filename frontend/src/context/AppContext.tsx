"use client";

import React, { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { organizationsApi } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query-keys";
import { useAuth } from "@/context/AuthContext";
import type { Organization } from "@/types";

// NOTE: this local `Employee` shape is intentionally narrower than the rich
// `Employee` interface in `@/types` — it backs the existing mock invite flow
// (`/employees/invite`, `/employees`) and its literal status union must not
// change, or those (frozen) pages break.
type Employee = {
  id: string;
  name: string;
  email: string;
  status: "invited" | "onboarding" | "active";
};

// Backward-compatible org shape: a plain object the setup wizard can create
// locally (no `id` yet) or the real `Organization` fetched from the API.
type Org = (Partial<Organization> & { name: string }) | null;

type AppState = {
  isAuthenticated: boolean;
  org: Org;
  employees: Employee[];
  setAuthenticated: (val: boolean) => void;
  setOrg: (org: Org) => void;
  addEmployee: (emp: Employee) => void;
  updateEmployee: (id: string, updates: Partial<Employee>) => void;
};

const AppContext = createContext<AppState | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated: authIsAuthenticated } = useAuth();

  // Local overrides preserve the pre-existing mock flows (login page,
  // setup wizard) that call `setAuthenticated`/`setOrg` directly without
  // touching the real backend yet.
  const [authOverride, setAuthOverride] = useState(false);
  const [localOrg, setLocalOrg] = useState<Org>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);

  const isAuthenticated = authIsAuthenticated || authOverride;

  const { data: fetchedOrg } = useQuery({
    queryKey: queryKeys.organizations.current(),
    queryFn: organizationsApi.current,
    enabled: isAuthenticated,
    retry: false,
  });

  const org: Org = fetchedOrg ?? localOrg;

  const setAuthenticated = (val: boolean) => setAuthOverride(val);
  const setOrg = (next: Org) => setLocalOrg(next);

  const addEmployee = (emp: Employee) => {
    setEmployees((prev) => [...prev, emp]);
  };

  const updateEmployee = (id: string, updates: Partial<Employee>) => {
    setEmployees((prev) =>
      prev.map((e) => (e.id === id ? { ...e, ...updates } : e))
    );
  };

  const value = useMemo<AppState>(
    () => ({
      isAuthenticated,
      org,
      employees,
      setAuthenticated,
      setOrg,
      addEmployee,
      updateEmployee,
    }),
    [isAuthenticated, org, employees]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}
