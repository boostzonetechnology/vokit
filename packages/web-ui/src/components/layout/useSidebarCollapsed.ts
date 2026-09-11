import { useEffect, useState } from "react";

const STORAGE_KEY = "vokit.sidebar.collapsed";

export function useSidebarCollapsed(defaultCollapsed = false) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored === "1") {
        setCollapsed(true);
      } else if (stored === "0") {
        setCollapsed(false);
      }
    } catch {
      // Ignore storage access failures.
    }
  }, []);

  function toggle() {
    setCollapsed((current) => {
      const next = !current;
      try {
        window.localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
      } catch {
        // Ignore storage access failures.
      }
      return next;
    });
  }

  return { collapsed, toggle, setCollapsed };
}
