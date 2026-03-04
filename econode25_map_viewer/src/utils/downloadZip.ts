import { strToU8, zipSync } from "fflate";

export function downloadZip(filename: string, files: Record<string, unknown>) {
  const zipEntries: Record<string, Uint8Array> = {};
  for (const [name, payload] of Object.entries(files)) {
    zipEntries[name] = strToU8(JSON.stringify(payload, null, 2));
  }
  const blob = new Blob([zipSync(zipEntries)], { type: "application/zip" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
