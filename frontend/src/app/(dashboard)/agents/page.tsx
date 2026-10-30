"use client";

import React from "react";
import { useAgentsList } from "@/hooks/useAgents";
import { QueryBoundary } from "@/components/QueryBoundary";
import { Bot, RefreshCcw, Cpu } from "lucide-react";
import type { Agent } from "@/types";

export default function AgentsPage() {
  const { data, isLoading, isError, error, refetch } = useAgentsList();
  const agents: Agent[] = data ?? [];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">AI Agent Fleet</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">Monitor and manage your enterprise AI workforce.</p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center justify-center py-2 px-4 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-sm text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
        >
          <RefreshCcw className="w-4 h-4 mr-2" />
          Refresh Status
        </button>
      </div>

      <QueryBoundary
        isLoading={isLoading}
        isError={isError}
        error={error}
        isEmpty={agents.length === 0}
        emptyTitle="No AI agents registered"
        emptyMessage="Your autonomous workforce is initializing."
        emptyIcon={<Bot className="w-8 h-8 text-zinc-400" />}
        onRetry={() => refetch()}
      >
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {agents.map((agent) => (
            <div key={agent.id || agent.name} className="bg-white dark:bg-zinc-900 shadow-sm border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-zinc-900 dark:text-zinc-50">{agent.display_name || agent.name}</h3>
                    <p className="text-xs text-zinc-500">{agent.description || "Autonomous Agent"}</p>
                  </div>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  agent.status === 'error'
                    ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                    : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                }`}>
                  {agent.status || "Online"}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-xs text-zinc-500 mb-1">Tasks Completed</p>
                  <p className="font-medium text-zinc-900 dark:text-zinc-50">{agent.total_tasks ?? 0}</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 mb-1">Capabilities</p>
                  <p className="font-medium text-zinc-900 dark:text-zinc-50 text-xs">
                    {Array.isArray(agent.capabilities) ? agent.capabilities.slice(0, 2).join(", ") : "general"}
                  </p>
                </div>
              </div>
              <div className="bg-zinc-50 dark:bg-zinc-800/50 rounded-lg p-3 flex items-center justify-between">
                <p className="text-xs text-zinc-500">Status</p>
                <div className="flex items-center text-xs font-medium text-zinc-900 dark:text-zinc-100">
                  <Cpu className="w-3.5 h-3.5 mr-1 text-zinc-400" />
                  {agent.status || "Ready"}
                </div>
              </div>
            </div>
          ))}
        </div>
      </QueryBoundary>
    </div>
  );
}
