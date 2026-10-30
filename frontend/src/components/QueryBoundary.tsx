import * as React from "react";
import { ErrorState } from "@/components/ErrorState";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState, type LoadingStateVariant } from "@/components/LoadingState";
import { ApiError } from "@/lib/api/client";

interface QueryBoundaryProps {
  isLoading: boolean;
  isError: boolean;
  error?: unknown;
  isEmpty?: boolean;
  emptyMessage?: string;
  emptyTitle?: string;
  emptyIcon?: React.ReactNode;
  emptyAction?: { label: string; onClick?: () => void; href?: string };
  errorTitle?: string;
  onRetry?: () => void;
  loadingVariant?: LoadingStateVariant;
  loadingRows?: number;
  loadingColumns?: number;
  className?: string;
  children: React.ReactNode;
}

function messageFromError(error: unknown): string {
  if (error instanceof ApiError) return error.detail;
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  return "Something went wrong. Please try again.";
}

/**
 * Uniform loading / error / empty handling for query-backed pages, wrapping
 * the existing `LoadingState`, `ErrorState`, and `EmptyState` components so
 * every page renders these states the same way.
 */
export function QueryBoundary({
  isLoading,
  isError,
  error,
  isEmpty = false,
  emptyMessage = "Nothing to show yet.",
  emptyTitle = "No results",
  emptyIcon,
  emptyAction,
  errorTitle = "An error occurred",
  onRetry,
  loadingVariant = "list",
  loadingRows,
  loadingColumns,
  className,
  children,
}: QueryBoundaryProps) {
  if (isLoading) {
    return (
      <LoadingState
        variant={loadingVariant}
        rows={loadingRows}
        columns={loadingColumns}
        className={className}
      />
    );
  }

  if (isError) {
    return (
      <ErrorState
        title={errorTitle}
        message={messageFromError(error)}
        onRetry={onRetry}
        className={className}
      />
    );
  }

  if (isEmpty) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyMessage}
        icon={emptyIcon}
        action={emptyAction}
        className={className}
      />
    );
  }

  return <>{children}</>;
}
