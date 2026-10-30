"use client";

import React from "react";
import { NotificationList } from "@/features/notifications/components/NotificationList";

export default function NotificationsPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500 max-w-4xl">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">Notifications</h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">Activity and system alerts from your AI workforce.</p>
      </div>

      <NotificationList />
    </div>
  );
}
