export function formatINR(amount: number, decimals = 2): string {
  const safe = Number.isFinite(amount) ? amount : 0;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(safe);
}

export function formatPercent(fraction: number, decimals = 1): string {
  const safe = Number.isFinite(fraction) ? fraction : 0;
  return `${(safe * 100).toFixed(decimals)}%`;
}

export function formatDaysOfCover(days: number): string {
  if (!Number.isFinite(days) || days < 0) {
    return "0.0d";
  }
  if (days >= 99) {
    return "99+ d";
  }
  return `${days.toFixed(1)}d`;
}

export function formatPerformanceDelta(ratio: number): string {
  const safe = Number.isFinite(ratio) ? ratio : 1;
  const pct = (safe - 1) * 100;
  if (Math.abs(pct) < 0.05) {
    return "0.0% vs target";
  }
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}% vs target`;
}

export function formatShortDate(isoDate: string): string {
  const parts = isoDate.split("-");
  if (parts.length === 3) {
    const [, month, day] = parts;
    const monthNames = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];
    const mIdx = Number(month) - 1;
    const label = monthNames[mIdx];
    if (label && day) {
      return `${day} ${label}`;
    }
  }
  return isoDate;
}
