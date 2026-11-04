import { cva } from "class-variance-authority";

export const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-1.5 font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-40",
  {
    variants: {
      variant: {
        primary: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary: "border border-border bg-secondary text-secondary-foreground hover:bg-muted",
        ghost: "text-muted-foreground hover:bg-secondary hover:text-foreground",
        outline: "border border-input bg-background text-foreground hover:bg-secondary",
        chip: "rounded-full border border-border bg-secondary/60 text-secondary-foreground hover:-translate-y-0.5 hover:border-primary/60 hover:text-primary",
        toggle:
          "border border-border bg-secondary text-muted-foreground aria-pressed:border-primary/50 aria-pressed:bg-primary/10 aria-pressed:text-primary",
      },
      size: {
        xs: "rounded-md px-2 py-1 text-[11px]",
        sm: "rounded-lg px-2.5 py-1.5 text-xs",
        md: "rounded-md px-4 py-2 text-sm",
        icon: "size-9 rounded-lg",
        iconSm: "rounded-md p-1",
      },
    },
    compoundVariants: [{ variant: "chip", class: "rounded-full px-3 py-1.5" }],
    defaultVariants: { variant: "secondary", size: "sm" },
  },
);
