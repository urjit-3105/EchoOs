import * as React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export type LoadingStateVariant = "list" | "card" | "table";

interface LoadingStateProps {
  variant?: LoadingStateVariant;
  rows?: number;
  columns?: number;
  className?: string;
}

function ListSkeleton({ rows, className }: { rows: number; className?: string }) {
  return (
    <div className={cn("space-y-3", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 rounded-lg border bg-card p-4">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

function CardSkeleton({ rows, className }: { rows: number; className?: string }) {
  return (
    <div className={cn("grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4", className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="space-y-3 rounded-xl border bg-card p-4 shadow-sm">
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-7 w-1/3" />
          <Skeleton className="h-3 w-2/3" />
        </div>
      ))}
    </div>
  );
}

function TableSkeleton({
  rows,
  columns,
  className,
}: {
  rows: number;
  columns: number;
  className?: string;
}) {
  return (
    <div className={cn("rounded-md border bg-card", className)}>
      <div className="border-b p-4">
        <div className="flex gap-4">
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
      </div>
      <div className="divide-y">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="flex gap-4 p-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <Skeleton key={colIndex} className="h-4 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function LoadingState({
  variant = "list",
  rows = 4,
  columns = 4,
  className,
}: LoadingStateProps) {
  if (variant === "card") return <CardSkeleton rows={rows} className={className} />;
  if (variant === "table") return <TableSkeleton rows={rows} columns={columns} className={className} />;
  return <ListSkeleton rows={rows} className={className} />;
}
