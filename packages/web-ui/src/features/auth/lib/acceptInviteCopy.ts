import type { Portal } from "@/api";
import type { AcceptInvitePortalCopy } from "@/features/auth/types/auth.types";

export const ACCEPT_INVITE_COPY: Record<Portal, AcceptInvitePortalCopy> = {
  platform: {
    eyebrow: "Platform invitation",
    heroTitle: "Finish setup to access the Vokit control plane.",
    subtitle: "Create your password to join the platform workspace.",
  },
  agency: {
    eyebrow: "Agency invitation",
    heroTitle: "Finish setup to access your agency workspace.",
    subtitle: "Create your password to join this agency on Vokit.",
  },
  customer: {
    eyebrow: "Customer invitation",
    heroTitle: "Finish setup to access your customer workspace.",
    subtitle: "Create your password to join this customer account.",
  },
};
