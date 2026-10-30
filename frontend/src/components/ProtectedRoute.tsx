"use client";

import * as React from "react";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { LoadingState } from "@/components/LoadingState";
import type { UserRole } from "@/types";

interface ProtectedRouteProps {
  roles?: UserRole[];
  children: React.ReactNode;
}

export function ProtectedRoute({ roles, children }: ProtectedRouteProps) {
  const router = useRouter();
  const { isLoading, isAuthenticated, hasRole } = useAuth();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const isAuthorized = !roles || roles.length === 0 || hasRole(...roles);

  React.useEffect(() => {
    if (mounted && !isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [mounted, isLoading, isAuthenticated, router]);

  if (!mounted) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="p-8">
        <LoadingState variant="card" rows={4} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  if (!isAuthorized) {
    return (
      <div className="flex h-full min-h-[60vh] flex-col items-center justify-center gap-3 rounded-2xl border border-zinc-100 bg-white p-10 text-center shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex h-16 w-16 items-center justify-center rounded-full border border-zinc-100 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800/50">
          <ShieldAlert className="h-8 w-8 text-zinc-400" />
        </div>
        <h3 className="text-xl font-medium tracking-tight text-zinc-900 dark:text-zinc-50">
          Insufficient permissions
        </h3>
        <p className="mt-1 max-w-sm text-sm text-zinc-500 dark:text-zinc-400">
          You don&apos;t have access to this page. Contact your administrator if you
          believe this is a mistake.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
