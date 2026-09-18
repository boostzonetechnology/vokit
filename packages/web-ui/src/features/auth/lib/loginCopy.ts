import type { Portal } from "@/api";
import type { LoginPortalCopy } from "@/features/auth/types/auth.types";

export const LOGIN_COPY: Record<Portal, LoginPortalCopy> = {
  platform: {
    title: "Sign in",
    subtitle: "Access the Platform control plane",
    heroEyebrow: "Platform portal",
    heroTitle: "Log in to your personal account to access all features.",
  },
  agency: {
    title: "Sign in",
    subtitle: "Access your Agency workspace",
    heroEyebrow: "Agency portal",
    heroTitle: "Log in to your personal account to access all features.",
  },
  customer: {
    title: "Sign in",
    subtitle: "Access your Customer workspace",
    heroEyebrow: "Customer portal",
    heroTitle: "Log in to your personal account to access all features.",
  },
};
