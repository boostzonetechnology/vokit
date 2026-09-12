import type { LucideIcon } from "lucide-react";
import {
  BadgeDollarSign,
  Bell,
  BookOpen,
  Bot,
  Building2,
  ClipboardList,
  CreditCard,
  FileText,
  LayoutDashboard,
  Layers,
  Megaphone,
  Phone,
  PhoneCall,
  Receipt,
  Scale,
  ScrollText,
  Settings,
  Shield,
  ArrowLeftRight,
  UserRound,
  Users,
  Wallet,
  Webhook,
} from "lucide-react";

import type { Portal } from "@/api";
import type { NavItem } from "@/nav";

export type NavGroup = {
  id: string;
  label: string;
  items: Array<NavItem & { icon: LucideIcon }>;
};

const ICONS: Record<string, LucideIcon> = {
  dashboard: LayoutDashboard,
  agencies: Building2,
  customers: Users,
  agents: Bot,
  numbers: Phone,
  knowledge: BookOpen,
  calls: PhoneCall,
  plans: CreditCard,
  invoices: Receipt,
  payments: BadgeDollarSign,
  payouts: Wallet,
  wallet: Wallet,
  kyc: Shield,
  settings: Settings,
  users: UserRound,
  team: Users,
  integrations: Webhook,
  webhooks: Webhook,
  notifications: Bell,
  preferences: Settings,
  account: UserRound,
  usage: FileText,
  risk: Shield,
  transfers: ArrowLeftRight,
  templates: Layers,
  instructions: ScrollText,
  audit: ClipboardList,
  disputes: Scale,
  "payment-methods": CreditCard,
  "notice-templates": Megaphone,
};

function withIcons(items: NavItem[]): Array<NavItem & { icon: LucideIcon }> {
  return items.map((item) => ({
    ...item,
    icon: ICONS[item.href.replace(/^\/+/, "")] ?? LayoutDashboard,
  }));
}

function pick(
  byRoute: Map<string, NavItem>,
  route: string,
  fallbackLabel: string,
  portal: Portal,
): NavItem & { icon: LucideIcon } {
  const item = byRoute.get(route) ?? {
    href: `/${route}`,
    label: fallbackLabel,
    path: `/api/v1/${portal}/${route}`,
  };
  return { ...item, icon: ICONS[route] ?? LayoutDashboard };
}

/** Shared sidebar groups — same shell layout for every portal. */
export function portalNavGroups(portal: Portal, nav: NavItem[]): NavGroup[] {
  const byRoute = new Map(nav.map((item) => [item.href.replace(/^\/+/, ""), item]));

  if (portal === "platform") {
    return [
      {
        id: "workspace",
        label: "Workspace",
        items: [
          pick(byRoute, "dashboard", "Dashboard", portal),
          pick(byRoute, "agencies", "Agencies", portal),
          pick(byRoute, "customers", "Customers", portal),
          pick(byRoute, "agents", "Agents", portal),
          pick(byRoute, "templates", "Templates", portal),
          pick(byRoute, "instructions", "Instructions", portal),
          pick(byRoute, "knowledge", "Knowledge", portal),
          pick(byRoute, "numbers", "Numbers", portal),
          pick(byRoute, "transfers", "Transfers", portal),
          pick(byRoute, "calls", "Calls", portal),
        ],
      },
      {
        id: "billing",
        label: "Billing",
        items: [
          pick(byRoute, "plans", "Plans", portal),
          pick(byRoute, "invoices", "Invoices", portal),
          pick(byRoute, "payments", "Payments", portal),
          pick(byRoute, "disputes", "Disputes", portal),
          pick(byRoute, "payouts", "Payouts", portal),
        ],
      },
      {
        id: "ops",
        label: "Operations",
        items: [
          pick(byRoute, "kyc", "KYC", portal),
          pick(byRoute, "risk", "Risk", portal),
          pick(byRoute, "integrations", "Integrations", portal),
          pick(byRoute, "audit", "Audit", portal),
        ],
      },
      {
        id: "account",
        label: "Account",
        items: [
          pick(byRoute, "notifications", "Notifications", portal),
          pick(byRoute, "notice-templates", "Notice templates", portal),
          pick(byRoute, "users", "Users", portal),
          pick(byRoute, "settings", "Settings", portal),
        ],
      },
    ];
  }

  if (portal === "agency") {
    return [
      {
        id: "workspace",
        label: "Workspace",
        items: [
          pick(byRoute, "dashboard", "Overview", portal),
          pick(byRoute, "agents", "Agents", portal),
          pick(byRoute, "numbers", "Phone numbers", portal),
          pick(byRoute, "knowledge", "Knowledge", portal),
          pick(byRoute, "calls", "Calls", portal),
          pick(byRoute, "transfers", "Transfers", portal),
          pick(byRoute, "customers", "Customers", portal),
        ],
      },
      {
        id: "ops",
        label: "Operations",
        items: [
          pick(byRoute, "integrations", "Integrations", portal),
          pick(byRoute, "webhooks", "Webhooks", portal),
        ],
      },
      {
        id: "billing",
        label: "Billing",
        items: [
          pick(byRoute, "wallet", "Wallet", portal),
          pick(byRoute, "payouts", "Payouts", portal),
          pick(byRoute, "invoices", "Invoices", portal),
          pick(byRoute, "plans", "Plans", portal),
        ],
      },
      {
        id: "account",
        label: "Account",
        items: [
          pick(byRoute, "kyc", "KYC", portal),
          pick(byRoute, "team", "Team", portal),
          pick(byRoute, "notifications", "Notifications", portal),
          pick(byRoute, "preferences", "Settings", portal),
        ],
      },
    ];
  }

  return [
    {
      id: "workspace",
      label: "Workspace",
      items: [
        pick(byRoute, "dashboard", "Overview", portal),
        pick(byRoute, "agents", "Agents", portal),
        pick(byRoute, "calls", "Calls", portal),
        pick(byRoute, "knowledge", "Knowledge", portal),
      ],
    },
    {
      id: "billing",
      label: "Billing",
      items: [
        pick(byRoute, "usage", "Usage", portal),
        pick(byRoute, "invoices", "Invoices", portal),
        pick(byRoute, "payment-methods", "Payment methods", portal),
      ],
    },
    {
      id: "account",
      label: "Account",
      items: [
        pick(byRoute, "account", "Account", portal),
        pick(byRoute, "team", "Team", portal),
        pick(byRoute, "notifications", "Notifications", portal),
      ],
    },
  ];
}

export { withIcons };
