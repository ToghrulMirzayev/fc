import React from "react";

// 1. Базовый пульсирующий блок-заглушка
export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={["animate-pulse rounded-sm bg-primary/10", className].join(" ")}
      {...props}
    />
  );
}

// 2. Универсальный скелетон для строк таблиц
export function TableSkeleton({
  rows = 5,
  cols = 5,
}: {
  rows?: number;
  cols?: number;
}) {
  return (
    <>
      {Array.from({ length: rows }).map((_, rIdx) => (
        <tr key={rIdx} className="border-b border-subtle last:border-0">
          {Array.from({ length: cols }).map((_, cIdx) => (
            <td key={cIdx} className="px-4 py-3.5">
              {cIdx === 0 ? (
                <div className="flex items-center gap-2.5">
                  <Skeleton className="h-7 w-7 rounded-full" />
                  <div className="space-y-1.5">
                    <Skeleton className="h-3.5 w-24" />
                    <Skeleton className="h-3 w-16" />
                  </div>
                </div>
              ) : (
                <Skeleton
                  className={`h-3.5 ${
                    cIdx % 2 === 0 ? "w-16" : "w-24"
                  }`}
                />
              )}
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

// 3. Универсальный скелетон для сетки карточек
export function CardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className="rounded-md border border-subtle bg-card p-5 space-y-4"
        >
          <div className="space-y-2">
            <Skeleton className="h-3.5 w-20" />
            <Skeleton className="h-6 w-32" />
          </div>
          <Skeleton className="h-10 w-24" />
          <div className="space-y-2 pt-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </div>
      ))}
    </>
  );
}

// 4. Универсальный скелетон для списков активности (Live feed)
export function FeedSkeleton({ count = 4 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className="flex items-center gap-3.5 rounded-md border border-subtle bg-card p-3.5"
        >
          <Skeleton className="h-4 w-14 shrink-0" />
          <Skeleton className="h-7 w-7 rounded-full shrink-0" />
          <div className="min-w-0 flex-1 space-y-1.5">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3.5 w-20" />
          </div>
          <Skeleton className="h-6 w-12 rounded-sm shrink-0" />
          <Skeleton className="h-3 w-10 shrink-0" />
        </div>
      ))}
    </>
  );
}
