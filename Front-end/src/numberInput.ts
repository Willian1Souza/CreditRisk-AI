export function cleanNumberInput(
  value: string,
  allowDecimals = true,
  allowNegative = false,
): string {
  if (!value) return "";
  let cleaned = value.replace(",", ".");
  const sign = allowNegative && cleaned.startsWith("-") ? "-" : "";
  cleaned = cleaned.replace(/-/g, "");

  if (allowDecimals) {
    cleaned = cleaned.replace(/[^0-9.]/g, "");
    const parts = cleaned.split(".");
    if (parts.length > 2) {
      cleaned = `${parts[0]}.${parts.slice(1).join("")}`;
    }
  } else {
    cleaned = cleaned.replace(/[^0-9]/g, "");
  }

  if (/^0[0-9]+/.test(cleaned)) {
    cleaned = cleaned.replace(/^0+/, "");
    if (cleaned === "") cleaned = "0";
  }

  return `${sign}${cleaned}`;
}
