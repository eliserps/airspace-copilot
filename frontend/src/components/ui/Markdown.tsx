import { Suspense, lazy } from "react";

const MarkdownRenderer = lazy(() => import("./MarkdownRenderer"));

export function Markdown({ children, className }: { children: string; className?: string }) {
  return (
    <Suspense fallback={<p className="text-sm whitespace-pre-wrap text-foreground">{children}</p>}>
      <MarkdownRenderer {...(className ? { className } : {})}>{children}</MarkdownRenderer>
    </Suspense>
  );
}
