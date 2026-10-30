"use client";

import React from "react";
import { useApp } from "@/context/AppContext";
import { EmptyState } from "@/components/EmptyState";
import { Briefcase } from "lucide-react";

export default function WorkflowsPage() {
  const { employees } = useApp();

  if (employees.length === 0) {
    return (
      <div className="h-full flex items-center justify-center animate-in fade-in duration-500">
        <EmptyState
          title="No workflows have started"
          description="Workflows will automatically generate here when you invite an employee and they begin their onboarding journey."
          icon={<Briefcase className="w-8 h-8 text-zinc-400" />}
          action={{
            label: "Invite Employee",
            href: "/employees/invite",
          }}
          className="max-w-md w-full"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">Workflows</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Track and manage active enterprise workflows.</p>
        </div>
      </div>
      
      <div className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-zinc-50 dark:bg-zinc-800/50 text-zinc-500 dark:text-zinc-400 border-b border-zinc-200 dark:border-zinc-800">
            <tr>
              <th className="px-6 py-4 font-medium">Workflow</th>
              <th className="px-6 py-4 font-medium">Target</th>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800 text-zinc-900 dark:text-zinc-50">
            {employees.map((emp) => (
              <tr key={`wf-${emp.id}`} className="hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors">
                <td className="px-6 py-4 font-medium">Employee Onboarding</td>
                <td className="px-6 py-4 text-zinc-500 dark:text-zinc-400">{emp.name}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    emp.status === "active" 
                      ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                      : "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                  }`}>
                    {emp.status === "active" ? "Completed" : "In Progress"}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button className="text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
