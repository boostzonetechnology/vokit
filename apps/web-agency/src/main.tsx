import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { PortalApp } from "@vokit/web-ui";
import "@vokit/web-ui/styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <PortalApp portal="agency" title="Agency portal" />
  </StrictMode>,
);
