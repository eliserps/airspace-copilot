import { Outlet, createRootRoute } from "@tanstack/react-router";
import { ErrorPage } from "@/components/pages/ErrorPage";
import { NotFoundPage } from "@/components/pages/NotFoundPage";

export const Route = createRootRoute({
  component: Outlet,
  notFoundComponent: NotFoundPage,
  errorComponent: ErrorPage,
});
