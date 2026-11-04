import { Link } from "@tanstack/react-router";
import { buttonVariants } from "@/components/ui/button-variants";
import { useI18n } from "@/lib/i18n/context";

export function NotFoundPage() {
  const { t } = useI18n();
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <p className="mt-4 text-sm text-muted-foreground">{t("nav.notFound")}</p>
        <Link
          to="/"
          className={buttonVariants({ variant: "primary", size: "md", className: "mt-6" })}
        >
          {t("nav.backToMap")}
        </Link>
      </div>
    </div>
  );
}
