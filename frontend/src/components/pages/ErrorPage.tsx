import { useRouter } from "@tanstack/react-router";
import { Button } from "@/components/ui/Button";
import { buttonVariants } from "@/components/ui/button-variants";
import { useI18n } from "@/lib/i18n/context";

export function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  const { t } = useI18n();
  const router = useRouter();
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div role="alert" className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{t("state.error")}</h1>
        <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <Button
            variant="primary"
            size="md"
            onClick={() => {
              void router.invalidate();
              reset();
            }}
          >
            {t("state.retry")}
          </Button>
          <a href="/" className={buttonVariants({ variant: "outline", size: "md" })}>
            {t("nav.backToMap")}
          </a>
        </div>
      </div>
    </div>
  );
}
