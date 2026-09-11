/** Path routes for Super Admin customers (list / create / detail). */

export function customersListHref(): string {
  return "/customers";
}

export function customerCreateHref(): string {
  return "/customers/new";
}

export function customerDetailHref(customerId: string): string {
  return `/customers/${customerId}`;
}

export function parseCustomerRoute(
  route: string,
): { kind: "list" } | { kind: "create" } | { kind: "detail"; customerId: string } | null {
  if (route === "customers") return { kind: "list" };
  if (route === "customers/new") return { kind: "create" };
  const match = /^customers\/([^/]+)$/.exec(route);
  if (match?.[1] && match[1] !== "new") {
    return { kind: "detail", customerId: match[1] };
  }
  return null;
}

export function isCustomersRoute(route: string): boolean {
  return route === "customers" || route.startsWith("customers/");
}
