import { eachWeekdayBetween, isWeekend, isWithinRange, toISODate, parseISODate } from "./utils/date.js";

const STATUS_FLOW = {
  DRAFT: ["SUBMITTED"],
  SUBMITTED: ["APPROVED", "DENIED"],
  APPROVED: [],
  DENIED: [],
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function normaliseAllowanceRecord(record) {
  const providerId = record.provider_id ?? record.providerId;
  const year = record.year;
  if (typeof providerId === "undefined" || typeof year === "undefined") {
    throw new Error("Allowance record must include provider_id and year");
  }
  return {
    providerId,
    year,
    daysTotal: record.days_total ?? record.daysTotal ?? 0,
    daysUsed: record.days_used ?? record.daysUsed ?? 0,
    amQuota: record.am_quota ?? record.amQuota ?? null,
    pmQuota: record.pm_quota ?? record.pmQuota ?? null,
    amUsed: record.am_used ?? record.amUsed ?? 0,
    pmUsed: record.pm_used ?? record.pmUsed ?? 0,
  };
}

function computeImpact(block, start, end) {
  const startDate = parseISODate(start);
  const endDate = parseISODate(end ?? start);
  if (endDate.getTime() < startDate.getTime()) {
    throw new RangeError("End date must not precede start date");
  }
  const weekdays = eachWeekdayBetween(startDate, endDate);
  if (block === "AM" || block === "PM") {
    if (weekdays.length !== 1) {
      throw new RangeError("AM/PM requests must be a single weekday");
    }
  }
  if (block === "FULLDAY" && weekdays.length !== 1) {
    throw new RangeError("Full-day requests span exactly one weekday");
  }
  if (block === "FULLWEEK" && weekdays.length < 1) {
    throw new RangeError("Full-week requests must include at least one weekday");
  }

  const totals = { days: 0, am: 0, pm: 0 };
  switch (block) {
    case "AM":
      totals.days = 0.5;
      totals.am = 1;
      break;
    case "PM":
      totals.days = 0.5;
      totals.pm = 1;
      break;
    case "FULLDAY":
      totals.days = 1;
      totals.am = 1;
      totals.pm = 1;
      break;
    case "FULLWEEK": {
      totals.days = weekdays.length;
      totals.am = weekdays.length;
      totals.pm = weekdays.length;
      break;
    }
    default:
      throw new Error(`Unsupported block type ${block}`);
  }
  return totals;
}

function ensureStatusTransition(currentStatus, nextStatus) {
  const allowed = STATUS_FLOW[currentStatus] ?? [];
  if (!allowed.includes(nextStatus)) {
    throw new Error(`Cannot transition from ${currentStatus} to ${nextStatus}`);
  }
}

export function createAppStore(initialState = {}) {
  const state = {
    providers: [],
    holidays: [],
    allowances: {},
    vacations: [],
    fairnessTargets: { weekendCall: {}, hospitalDays: {} },
    scheduleAssignments: [],
    callAssignments: [],
    window: null,
    ...clone(initialState),
  };

  let sequence = 1;
  const listeners = new Set();

  function notify() {
    const snapshot = getState();
    for (const listener of listeners) {
      listener(snapshot);
    }
  }

  function getState() {
    return clone(state);
  }

  function subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  function setProviders(providers) {
    state.providers = providers.map((provider) => ({ ...provider }));
    notify();
  }

  function setWindow(window) {
    if (!window || !window.start || !window.end) {
      throw new Error("Window must include start and end dates");
    }
    state.window = { start: toISODate(window.start), end: toISODate(window.end) };
    notify();
  }

  function setHolidays(holidays) {
    state.holidays = holidays.map((holiday) => ({
      date: toISODate(holiday.date ?? holiday),
      name: holiday.name ?? "",
      isOfficeClosed: holiday.is_office_closed ?? holiday.isOfficeClosed ?? false,
      extendWeekend: holiday.extend_weekend ?? holiday.extendWeekend ?? false,
    }));
    notify();
  }

  function setAllowances(allowances) {
    state.allowances = {};
    for (const record of allowances) {
      const normalized = normaliseAllowanceRecord(record);
      if (!state.allowances[normalized.providerId]) {
        state.allowances[normalized.providerId] = {};
      }
      state.allowances[normalized.providerId][normalized.year] = normalized;
    }
    notify();
  }

  function locateAllowance(providerId, year) {
    const allowance = state.allowances?.[providerId]?.[year];
    if (!allowance) {
      throw new Error(`No allowance configured for provider ${providerId} in ${year}`);
    }
    return allowance;
  }

  function detectHolidayOverlap(start, end) {
    const range = eachWeekdayBetween(start, end);
    return range.some((date) => {
      const iso = toISODate(date);
      return state.holidays.some((holiday) => holiday.date === iso && holiday.isOfficeClosed);
    });
  }

  function assertWithinWindow(start, end) {
    if (!state.window) {
      throw new Error("Scheduling window not configured");
    }
    if (!isWithinRange(start, state.window.start, state.window.end) || !isWithinRange(end, state.window.start, state.window.end)) {
      throw new Error("Vacation request must stay within the active window");
    }
  }

  function createVacationDraft(payload) {
    const providerId = payload.provider_id ?? payload.providerId;
    if (!providerId) {
      throw new Error("Provider is required for a vacation request");
    }
    const block = payload.block;
    if (!block) {
      throw new Error("Block type is required");
    }
    const start = toISODate(payload.start_date ?? payload.startDate);
    const end = toISODate(payload.end_date ?? payload.endDate ?? start);
    assertWithinWindow(start, end);
    if (detectHolidayOverlap(start, end)) {
      throw new Error("Request intersects with an office closure holiday");
    }
    const startDate = parseISODate(start);
    const endDate = parseISODate(end);
    if (block === "AM" || block === "PM" || block === "FULLDAY") {
      if (isWeekend(startDate) || isWeekend(endDate)) {
        throw new Error("Partial day requests must fall on weekdays");
      }
    }
    const request = {
      id: `VR-${String(sequence++).padStart(5, "0")}`,
      providerId,
      startDate: start,
      endDate: end,
      block,
      status: "DRAFT",
      approverId: null,
      auditLog: [
        {
          timestamp: new Date().toISOString(),
          action: "CREATE",
          actor: payload.actor ?? "user",
          notes: payload.notes ?? "",
        },
      ],
      metadata: {
        notes: payload.notes ?? "",
        createdBy: payload.actor ?? "user",
      },
    };
    state.vacations.push(request);
    notify();
    return clone(request);
  }

  function touchAllowance(providerId, year, impact, direction) {
    const allowance = locateAllowance(providerId, year);
    const multiplier = direction === "revert" ? -1 : 1;
    const proposedDays = allowance.daysUsed + multiplier * impact.days;
    if (proposedDays > allowance.daysTotal + 1e-6) {
      throw new Error("Insufficient total allowance");
    }
    if (allowance.amQuota !== null) {
      const proposedAm = allowance.amUsed + multiplier * impact.am;
      if (proposedAm > allowance.amQuota + 1e-6) {
        throw new Error("Insufficient AM quota");
      }
      allowance.amUsed = Number((proposedAm).toFixed(3));
    }
    if (allowance.pmQuota !== null) {
      const proposedPm = allowance.pmUsed + multiplier * impact.pm;
      if (proposedPm > allowance.pmQuota + 1e-6) {
        throw new Error("Insufficient PM quota");
      }
      allowance.pmUsed = Number((proposedPm).toFixed(3));
    }
    allowance.daysUsed = Number((proposedDays).toFixed(3));
  }

  function updateStatus(id, nextStatus, actor, extra = {}) {
    const request = state.vacations.find((item) => item.id === id);
    if (!request) {
      throw new Error(`Unknown request ${id}`);
    }
    ensureStatusTransition(request.status, nextStatus);
    const year = Number.parseInt(request.startDate.slice(0, 4), 10);
    if (nextStatus === "APPROVED") {
      const impact = computeImpact(request.block, request.startDate, request.endDate);
      touchAllowance(request.providerId, year, impact, "apply");
    }
    request.status = nextStatus;
    if (nextStatus === "APPROVED" || nextStatus === "DENIED") {
      request.approverId = extra.approverId ?? actor ?? null;
    }
    request.auditLog.push({
      timestamp: new Date().toISOString(),
      action: nextStatus,
      actor: actor ?? "system",
      notes: extra.notes ?? "",
    });
    notify();
    return clone(request);
  }

  function submitVacationRequest(id, actor = "user") {
    return updateStatus(id, "SUBMITTED", actor);
  }

  function approveVacationRequest(id, approverId) {
    return updateStatus(id, "APPROVED", approverId, { approverId });
  }

  function denyVacationRequest(id, approverId, notes = "") {
    return updateStatus(id, "DENIED", approverId, { approverId, notes });
  }

  function setSchedule(assignments) {
    state.scheduleAssignments = assignments.map((assignment) => ({ ...assignment, date: toISODate(assignment.date) }));
    notify();
  }

  function setCallAssignments(assignments) {
    state.callAssignments = assignments.map((assignment) => ({ ...assignment, date: toISODate(assignment.date) }));
    notify();
  }

  function setFairnessTargets(targets) {
    state.fairnessTargets = clone(targets);
    notify();
  }

  function getAllowanceSummary(providerId, year) {
    const allowance = locateAllowance(providerId, year);
    return clone(allowance);
  }

  return {
    getState,
    subscribe,
    setProviders,
    setWindow,
    setHolidays,
    setAllowances,
    setSchedule,
    setCallAssignments,
    setFairnessTargets,
    createVacationDraft,
    submitVacationRequest,
    approveVacationRequest,
    denyVacationRequest,
    getAllowanceSummary,
  };
}

export { computeImpact };