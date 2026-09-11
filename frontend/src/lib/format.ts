// Formatting helpers. Backend returns monetary amounts as decimal strings;
// callers pass those (or numbers) through here rather than doing ad-hoc
// Number() + toFixed() at call sites.

export function toNum(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : null;
}

export function formatCurrency(
  value: string | number | null | undefined,
  currency = "USD",
): string {
  const n = toNum(value);
  if (n === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(n);
}

/** Format a signed monetary value with an explicit +/- and a sign class hint. */
export function formatSignedCurrency(
  value: string | number | null | undefined,
  currency = "USD",
): string {
  const n = toNum(value);
  if (n === null) return "N/A";
  const formatted = formatCurrency(Math.abs(n), currency);
  return n < 0 ? `-${formatted}` : n > 0 ? `+${formatted}` : formatted;
}

export function formatNumber(
  value: string | number | null | undefined,
  fractionDigits = 2,
): string {
  const n = toNum(value);
  if (n === null) return "N/A";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(n);
}

/** Formats a ratio (e.g. 0.153) as a percentage string ("15.3%"). Null-safe. */
export function formatPercent(
  value: number | null | undefined,
  fractionDigits = 1,
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }
  return `${(value * 100).toFixed(fractionDigits)}%`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "N/A";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "N/A";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function signClass(value: string | number | null | undefined): string {
  const n = toNum(value);
  if (n === null || n === 0) return "neutral";
  return n > 0 ? "positive" : "negative";
}
