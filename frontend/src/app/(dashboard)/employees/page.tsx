"use client";

import React from "react";
import Link from "next/link";
import { UserPlus } from "lucide-react";
import { EmployeeList } from "@/features/employees/components/EmployeeList";

export default function EmployeesPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">Employees</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Manage your workforce and view onboarding status.</p>
        </div>
        <Link
          href="/employees/invite"
          className="inline-flex items-center justify-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-black hover:bg-zinc-800 dark:bg-white dark:text-black dark:hover:bg-zinc-200 transition-colors"
        >
          <UserPlus className="w-4 h-4 mr-2" />
          Invite Employee
        </Link>
      </div>

      <EmployeeList />
    </div>
  );
}
