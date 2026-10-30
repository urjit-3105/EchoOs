"use client";

import React from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { LogOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useCurrentOrganization } from "@/hooks/useOrganizations";
import { useUnreadNotificationCount } from "@/hooks/useNotifications";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { NAV_ITEMS } from "@/constants";
import { ROLE_LABELS } from "@/constants";
import { initials } from "@/utils/format";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout, hasRole } = useAuth();
  const { data: organization, isLoading: orgLoading } = useCurrentOrganization();
  const { data: unreadData } = useUnreadNotificationCount();

  const unreadCount = unreadData?.count ?? 0;

  const visibleNavItems = NAV_ITEMS.filter(
    (item) => !item.roles || item.roles.length === 0 || hasRole(...item.roles)
  );

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-zinc-50 dark:bg-black">
        {/* Sidebar */}
        <div className="w-64 flex flex-col border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
          <div className="p-6 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-zinc-900 dark:text-zinc-50">
                {orgLoading ? "…" : organization?.name ?? "ECHO WorkforceOS"}
              </h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Workspace</p>
            </div>
            <ThemeToggle />
          </div>

          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {visibleNavItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
              const Icon = item.icon;
              const showBadge = item.href === "/notifications" && unreadCount > 0;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? "bg-zinc-100 text-zinc-900 dark:bg-zinc-800 dark:text-white"
                      : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800/50 dark:hover:text-white"
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3 flex-shrink-0" />
                  <span className="flex-1">{item.label}</span>
                  {showBadge && (
                    <span className="ml-2 inline-flex min-w-[1.25rem] items-center justify-center rounded-full bg-zinc-900 px-1.5 py-0.5 text-[10px] font-semibold leading-none text-white dark:bg-white dark:text-black">
                      {unreadCount > 99 ? "99+" : unreadCount}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 space-y-3">
            {user && (
              <div className="flex items-center gap-3 px-1">
                <Avatar size="sm">
                  <AvatarFallback>{initials(user.full_name ?? user.email)}</AvatarFallback>
                </Avatar>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-zinc-900 dark:text-zinc-50">
                    {user.full_name ?? user.email}
                  </p>
                  <p className="truncate text-xs text-zinc-500 dark:text-zinc-400">
                    {ROLE_LABELS[user.role]}
                  </p>
                </div>
              </div>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-3 py-2 text-sm font-medium text-zinc-600 hover:text-red-600 hover:bg-red-50 dark:text-zinc-400 dark:hover:text-red-400 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            >
              <LogOut className="w-5 h-5 mr-3 flex-shrink-0" />
              Sign out
            </button>
          </div>
        </div>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto bg-zinc-50 dark:bg-black p-8">
            <div className="max-w-6xl mx-auto">{children}</div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
