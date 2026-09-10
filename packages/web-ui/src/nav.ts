import type { Portal } from "./api";

export type NavItem = { href: string; label: string; path: string };

export function portalNav(portal: Portal): NavItem[] {
  if (portal === "platform") {
    return [
      { href: "#/dashboard", label: "Dashboard", path: "/api/v1/platform/dashboard" },
      { href: "#/agencies", label: "Agencies", path: "/api/v1/platform/agencies" },
      { href: "#/customers", label: "Customers", path: "/api/v1/platform/customers" },
      { href: "#/kyc", label: "KYC", path: "/api/v1/platform/kyc/cases" },
      { href: "#/agents", label: "Agents", path: "/api/v1/platform/agents" },
      { href: "#/templates", label: "Templates", path: "/api/v1/platform/templates" },
      { href: "#/instructions", label: "Instructions", path: "/api/v1/platform/instructions" },
      { href: "#/knowledge", label: "Knowledge", path: "/api/v1/platform/knowledge" },
      { href: "#/numbers", label: "Numbers", path: "/api/v1/platform/phone-numbers" },
      { href: "#/transfers", label: "Transfers", path: "/api/v1/platform/transfers" },
      { href: "#/plans", label: "Plans", path: "/api/v1/platform/plans" },
      { href: "#/invoices", label: "Invoices", path: "/api/v1/platform/invoices" },
      { href: "#/payments", label: "Payments", path: "/api/v1/platform/payments" },
      { href: "#/disputes", label: "Disputes", path: "/api/v1/platform/disputes" },
      { href: "#/payouts", label: "Payouts", path: "/api/v1/platform/payouts" },
      { href: "#/calls", label: "Calls", path: "/api/v1/platform/calls" },
      { href: "#/integrations", label: "Integrations", path: "/api/v1/platform/integrations" },
      { href: "#/risk", label: "Risk", path: "/api/v1/platform/risk/cases" },
      { href: "#/notifications", label: "Notifications", path: "/api/v1/platform/notifications" },
      {
        href: "#/notice-templates",
        label: "Notice templates",
        path: "/api/v1/platform/notification-templates",
      },
      { href: "#/audit", label: "Audit", path: "/api/v1/platform/audit-events" },
      { href: "#/users", label: "Users", path: "/api/v1/platform/users" },
      { href: "#/settings", label: "Settings", path: "/api/v1/platform/settings" },
    ];
  }
  if (portal === "agency") {
    return [
      { href: "#/dashboard", label: "Dashboard", path: "/api/v1/agency/dashboard" },
      { href: "#/customers", label: "Customers", path: "/api/v1/agency/customers" },
      { href: "#/agents", label: "Agents", path: "/api/v1/agency/agents" },
      { href: "#/templates", label: "Templates", path: "/api/v1/agency/templates" },
      { href: "#/numbers", label: "Numbers", path: "/api/v1/agency/phone-numbers" },
      { href: "#/calls", label: "Calls", path: "/api/v1/agency/calls" },
      { href: "#/transfers", label: "Transfers", path: "/api/v1/agency/transfers" },
      { href: "#/knowledge", label: "Knowledge", path: "/api/v1/agency/knowledge" },
      { href: "#/integrations", label: "Integrations", path: "/api/v1/agency/integrations" },
      { href: "#/webhooks", label: "Webhooks", path: "/api/v1/agency/webhooks" },
      { href: "#/plans", label: "Plans", path: "/api/v1/agency/plans" },
      { href: "#/invoices", label: "Invoices", path: "/api/v1/agency/customer-invoices" },
      { href: "#/wallet", label: "Wallet", path: "/api/v1/agency/wallet" },
      { href: "#/payouts", label: "Payouts", path: "/api/v1/agency/payouts" },
      { href: "#/kyc", label: "KYC", path: "/api/v1/agency/kyc" },
      { href: "#/team", label: "Team", path: "/api/v1/agency/team" },
      { href: "#/notifications", label: "Notifications", path: "/api/v1/agency/notifications" },
      {
        href: "#/preferences",
        label: "Preferences",
        path: "/api/v1/agency/notification-preferences",
      },
    ];
  }
  return [
    { href: "#/dashboard", label: "Dashboard", path: "/api/v1/customer/dashboard" },
    { href: "#/agents", label: "Agents", path: "/api/v1/customer/agents" },
    { href: "#/calls", label: "Calls", path: "/api/v1/customer/calls" },
    { href: "#/usage", label: "Usage", path: "/api/v1/customer/usage" },
    { href: "#/invoices", label: "Invoices", path: "/api/v1/customer/invoices" },
    { href: "#/payment-methods", label: "Payment methods", path: "/api/v1/customer/payment-methods" },
    { href: "#/account", label: "Account", path: "/api/v1/customer/account" },
    { href: "#/risk", label: "Risk", path: "/api/v1/customer/risk" },
    { href: "#/knowledge", label: "Knowledge", path: "/api/v1/customer/knowledge" },
    { href: "#/integrations", label: "Integrations", path: "/api/v1/customer/integrations" },
    { href: "#/team", label: "Team", path: "/api/v1/customer/team" },
    { href: "#/notifications", label: "Notifications", path: "/api/v1/customer/notifications" },
    {
      href: "#/preferences",
      label: "Preferences",
      path: "/api/v1/customer/notification-preferences",
    },
  ];
}

export function currentRoute(): string {
  const hash = window.location.hash.replace(/^#\/?/, "");
  return hash.split("?")[0] || "dashboard";
}
