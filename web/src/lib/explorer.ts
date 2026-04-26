export const EXPLORER_BASE = process.env.NEXT_PUBLIC_EXPLORER_URL ?? "";
export const EXPLORER_TX_PATH = process.env.NEXT_PUBLIC_EXPLORER_TX_PATH ?? "/tx/";

export function txUrl(hash: string | null | undefined): string | null {
  if (!hash || !EXPLORER_BASE) return null;
  const clean = hash.startsWith("0x") ? hash : `0x${hash}`;
  const base = EXPLORER_BASE.replace(/\/$/, "");
  return `${base}${EXPLORER_TX_PATH}${clean}`;
}

export function shorten(addr: string | null | undefined, head = 6, tail = 4): string {
  if (!addr) return "";
  if (addr.length <= head + tail + 2) return addr;
  return `${addr.slice(0, head)}…${addr.slice(-tail)}`;
}
