export function SkeletonLines({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2 p-4" aria-hidden>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-3 animate-pulse rounded bg-muted"
          style={{ width: `${90 - i * 12}%`, animationDelay: `${i * 90}ms` }}
        />
      ))}
    </div>
  );
}
