import { Layout } from "./components/Layout";
import { SummaryPage } from "./pages/Summary";
import { ForecastPage } from "./pages/Forecast";
import { InventoryPage } from "./pages/Inventory";
import { PricingPage } from "./pages/Pricing";
import { AssortmentPage } from "./pages/Assortment";
import { OpsPage } from "./pages/Ops";
import { CopilotPage } from "./pages/Copilot";

function route() {
  const hash = window.location.hash || "#/";
  return hash.replace("#", "");
}

export function App() {
  const path = route();
  let page = <SummaryPage />;

  if (path.startsWith("/forecast")) page = <ForecastPage />;
  if (path.startsWith("/inventory")) page = <InventoryPage />;
  if (path.startsWith("/pricing")) page = <PricingPage />;
  if (path.startsWith("/assortment")) page = <AssortmentPage />;
  if (path.startsWith("/ops")) page = <OpsPage />;
  if (path.startsWith("/copilot")) page = <CopilotPage />;

  return <Layout>{page}</Layout>;
}
