import { z } from "zod";

export const AppConfigSchema = z.object({
  mapboxToken: z.string().optional(),
  outputsBaseUrl: z.string().url(),
  mapStyle: z.string().min(1),
  scenarios: z.array(z.string()).min(1)
});

export type AppConfig = z.infer<typeof AppConfigSchema>;
