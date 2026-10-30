"use client";

import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query-keys";
import { useRealtimeTable } from "@/hooks/useRealtime";
import { useApp } from "@/context/AppContext";
import { OverviewCards } from "@/features/dashboard/components/OverviewCards";
import { RecentActivity } from "@/features/dashboard/components/RecentActivity";
import { RecentEmployees } from "@/features/dashboard/components/RecentEmployees";
import { WorkflowStatusChart } from "@/features/dashboard/components/WorkflowStatusChart";
import { WeeklyOnboardingChart } from "@/features/dashboard/components/WeeklyOnboardingChart";
import { DepartmentDistributionChart } from "@/features/dashboard/components/DepartmentDistributionChart";
import { SystemHealthChart } from "@/features/dashboard/components/SystemHealthChart";
import { QuickActions } from "@/features/dashboard/components/QuickActions";
import { Announcements } from "@/features/dashboard/components/Announcements";

export default function Dashboard() {
  const { org } = useApp();
  const queryClient = useQueryClient();

  useRealtimeTable("workflows", () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.workflows.all });
  });
  useRealtimeTable("employees", () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.employees.all });
  });
  useRealtimeTable("notifications", () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all });
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          {org?.name ? `Welcome to ${org.name}` : "Overview"}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
          A live look at onboarding, workflows, and system health across your workforce.
        </p>
      </div>

      <OverviewCards />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <WorkflowStatusChart />
        <WeeklyOnboardingChart />
        <DepartmentDistributionChart />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <SystemHealthChart />
        </div>
        <QuickActions />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <RecentEmployees />
        <div className="space-y-6 lg:col-span-1">
          <RecentActivity />
          <Announcements />
        </div>
      </div>
    </div>
  );
}
