function toIsoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function startOfMonth(d = new Date()): string {
  return toIsoDate(new Date(d.getFullYear(), d.getMonth(), 1));
}

export function today(): string {
  return toIsoDate(new Date());
}

/** ISO date string N months before today, first-of-month. */
export function monthsAgoStart(months: number): string {
  const d = new Date();
  d.setDate(1);
  d.setMonth(d.getMonth() - (months - 1));
  return toIsoDate(d);
}

export function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return toIsoDate(d);
}
