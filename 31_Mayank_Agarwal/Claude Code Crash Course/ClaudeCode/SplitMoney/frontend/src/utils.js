/** Format paise (integer) as ₹X,XX,XXX.XX */
export const fmtPaise = (paise) =>
  `₹${(paise / 100).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;

/** Format rupees (float) as ₹X,XX,XXX.XX — used for settlement amounts */
export const fmtRupees = (rupees) =>
  `₹${Number(rupees).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;

/** Format an ISO date string as "3 May 2026" */
export const fmtDate = (isoDate) =>
  new Date(`${isoDate}T00:00:00`).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

/** Today's date as YYYY-MM-DD */
export const today = () => new Date().toISOString().slice(0, 10);
