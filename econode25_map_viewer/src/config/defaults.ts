import { AppConfigSchema, type AppConfig } from "./schema";

export const DEFAULT_SCENARIOS = ["baseline", "transit_first", "green_first", "high_density"] as const;

export const appConfig: AppConfig = AppConfigSchema.parse({
  mapboxToken: import.meta.env.VITE_MAPBOX_TOKEN,
  outputsBaseUrl: import.meta.env.VITE_OUTPUTS_BASE_URL ?? "/outputs",
  mapStyle: "mapbox://styles/mapbox/light-v11",
  scenarios: [...DEFAULT_SCENARIOS]
});
