/** Path routes for Super Admin agencies (list / create / detail). */

export function agenciesListHref(): string {
  return "/agencies";
}

export function agencyCreateHref(): string {
  return "/agencies/new";
}

export function agencyDetailHref(agencyId: string): string {
  return `/agencies/${agencyId}`;
}

export function parseAgencyRoute(
  route: string,
): { kind: "list" } | { kind: "create" } | { kind: "detail"; agencyId: string } | null {
  if (route === "agencies") return { kind: "list" };
  if (route === "agencies/new") return { kind: "create" };
  const match = /^agencies\/([^/]+)$/.exec(route);
  if (match?.[1] && match[1] !== "new") {
    return { kind: "detail", agencyId: match[1] };
  }
  return null;
}

export function isAgenciesRoute(route: string): boolean {
  return route === "agencies" || route.startsWith("agencies/");
}
