const MS_PER_DAY = 24 * 60 * 60 * 1000;

function normalizeDateInput(value) {
  if (value instanceof Date) {
    return new Date(Date.UTC(value.getUTCFullYear(), value.getUTCMonth(), value.getUTCDate()));
  }
  if (typeof value === "string") {
    const [year, month = "1", day = "1"] = value.split("-").map((segment) => Number.parseInt(segment, 10));
    return new Date(Date.UTC(year, month - 1, day));
  }
  throw new TypeError("Unsupported date value");
}

export function toISODate(value) {
  const date = normalizeDateInput(value);
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}-${String(date.getUTCDate()).padStart(2, "0")}`;
}

export function parseISODate(value) {
  return normalizeDateInput(value);
}

export function addDays(value, delta) {
  const date = normalizeDateInput(value);
  return new Date(date.getTime() + delta * MS_PER_DAY);
}

export function isWeekend(value) {
  const date = normalizeDateInput(value);
  const day = date.getUTCDay();
  return day === 0 || day === 6;
}

export function isWeekday(value) {
  return !isWeekend(value);
}

export function iterateRange(start, end) {
  const startDate = normalizeDateInput(start);
  const endDate = normalizeDateInput(end);
  if (startDate.getTime() > endDate.getTime()) {
    throw new RangeError("Start date must be before end date");
  }
  const results = [];
  for (let time = startDate.getTime(); time <= endDate.getTime(); time += MS_PER_DAY) {
    results.push(new Date(time));
  }
  return results;
}

export function eachWeekdayBetween(start, end) {
  return iterateRange(start, end).filter((date) => isWeekday(date));
}

export function isWithinRange(value, start, end) {
  const date = normalizeDateInput(value).getTime();
  const startTime = normalizeDateInput(start).getTime();
  const endTime = normalizeDateInput(end).getTime();
  return date >= startTime && date <= endTime;
}

export function getISOWeekStart(value) {
  const date = normalizeDateInput(value);
  const day = date.getUTCDay();
  const offset = day === 0 ? -6 : 1 - day; // shift Sunday to previous Monday
  return addDays(date, offset);
}

export function formatDisplay(value) {
  const date = normalizeDateInput(value);
  const month = date.toLocaleString("en-US", { month: "short", timeZone: "UTC" });
  const day = String(date.getUTCDate()).padStart(2, "0");
  return `${month} ${day}`;
}

export function enumerateWeeks(start, end) {
  const weeks = [];
  let cursor = getISOWeekStart(start);
  const endDate = normalizeDateInput(end);
  while (cursor.getTime() <= endDate.getTime()) {
    weeks.push(toISODate(cursor));
    cursor = addDays(cursor, 7);
  }
  return weeks;
}

export function businessDayCount(start, end) {
  return eachWeekdayBetween(start, end).length;
}

export function clampToWindow(value, { start, end }) {
  const date = normalizeDateInput(value);
  if (date.getTime() < normalizeDateInput(start).getTime()) {
    return normalizeDateInput(start);
  }
  if (date.getTime() > normalizeDateInput(end).getTime()) {
    return normalizeDateInput(end);
  }
  return date;
}

export function spansWeekend(start, end) {
  return iterateRange(start, end).some((date) => isWeekend(date));
}

export function diffInDays(start, end) {
  const startDate = normalizeDateInput(start);
  const endDate = normalizeDateInput(end);
  return Math.round((endDate.getTime() - startDate.getTime()) / MS_PER_DAY);
}