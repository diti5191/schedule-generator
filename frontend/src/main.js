import { createAppStore } from "./store.js";
import { VacationRequestForm } from "./components/vacationForm.js";
import { ScheduleBoard } from "./components/scheduleBoard.js";
import { FairnessDashboard } from "./components/fairnessDashboard.js";
import { addDays, toISODate } from "./utils/date.js";

const DEFAULT_WINDOW = {
  start: "2026-01-05",
  end: "2026-03-27",
};

const SAMPLE_PROVIDERS = [
  { id: "JOO", initials: "JOO", fullName: "Joon Oh", type: "MD" },
  { id: "KC", initials: "KC", fullName: "Kara Chen", type: "APN" },
  { id: "APZ", initials: "APZ", fullName: "Aparna Zhao", type: "MD" },
];

const SAMPLE_ALLOWANCES = [
  { providerId: "JOO", year: 2026, days_total: 20, days_used: 2, am_quota: 20, pm_quota: 20, am_used: 2, pm_used: 1 },
  { providerId: "KC", year: 2026, days_total: 18, days_used: 1, am_quota: 18, pm_quota: 18, am_used: 1, pm_used: 0 },
  { providerId: "APZ", year: 2026, days_total: 22, days_used: 4, am_quota: 22, pm_quota: 22, am_used: 3, pm_used: 3 },
];

const SAMPLE_HOLIDAYS = [
  { date: "2026-01-19", name: "MLK Day", is_office_closed: true, extend_weekend: true },
  { date: "2026-02-16", name: "Presidents Day", is_office_closed: true, extend_weekend: true },
];

function buildSampleAssignments() {
  const monday = toISODate(DEFAULT_WINDOW.start);
  return [
    { date: monday, block: "AM", siteType: "office", site: "HH OFFICE", provider: "JOO", role: "MD" },
    { date: monday, block: "PM", siteType: "office", site: "SVI DR", provider: "KC", role: "APN" },
    { date: toISODate(addDays(monday, 1)), block: "AM", siteType: "hospital", site: "WT HOSP", provider: "APZ", role: "MD" },
    { date: toISODate(addDays(monday, 2)), block: "PM", siteType: "hospital", site: "RMC", provider: "JOO", role: "MD" },
  ];
}

function buildSampleCallAssignments() {
  const monday = toISODate(DEFAULT_WINDOW.start);
  return [
    { date: monday, label: "Mon", type: "weekday_noninvasive", provider: "JOO" },
    { date: toISODate(addDays(monday, 1)), label: "Tue", type: "weekday_interventional", provider: "APZ" },
    { date: toISODate(addDays(monday, 4)), label: "Fri", type: "weekend_noninvasive", provider: "KC" },
    { date: toISODate(addDays(monday, 5)), label: "Sat", type: "weekend_noninvasive", provider: "JOO" },
    { date: toISODate(addDays(monday, 5)), label: "Sat INT", type: "weekend_interventional", provider: "APZ" },
  ];
}

const SAMPLE_FAIRNESS_TARGETS = {
  weekendCall: {
    JOO: 3,
    KC: 2,
    APZ: 4,
  },
  hospitalDays: {
    JOO: 10,
    KC: 0,
    APZ: 12,
  },
};

function ensureElement(value) {
  if (!value) {
    return undefined;
  }
  return value;
}

export function bootstrapApp(options = {}) {
  const mounts = options.mounts ?? {};
  const store = options.store ?? createAppStore();
  const initialState = options.initialState ?? {};

  if (!options.store) {
    store.setWindow(initialState.window ?? DEFAULT_WINDOW);
    store.setProviders(initialState.providers ?? SAMPLE_PROVIDERS);
    store.setAllowances(initialState.allowances ?? SAMPLE_ALLOWANCES);
    store.setHolidays(initialState.holidays ?? SAMPLE_HOLIDAYS);
    store.setSchedule(initialState.scheduleAssignments ?? buildSampleAssignments());
    store.setCallAssignments(initialState.callAssignments ?? buildSampleCallAssignments());
    store.setFairnessTargets(initialState.fairnessTargets ?? SAMPLE_FAIRNESS_TARGETS);
  }

  const components = {};
  const formContainer = ensureElement(mounts.vacationForm ?? (typeof document !== "undefined" ? document.getElementById("vacation-form") : null));
  const allowanceContainer = ensureElement(mounts.allowance ?? (typeof document !== "undefined" ? document.getElementById("allowance-summary") : null));
  const boardContainer = ensureElement(mounts.board ?? (typeof document !== "undefined" ? document.getElementById("board-root") : null));
  const fairnessContainer = ensureElement(mounts.fairness ?? (typeof document !== "undefined" ? document.getElementById("fairness-root") : null));

  if (formContainer) {
    components.vacationForm = new VacationRequestForm(store, { form: formContainer, allowance: allowanceContainer });
  }
  if (boardContainer) {
    components.scheduleBoard = new ScheduleBoard(store, { container: boardContainer });
  }
  if (fairnessContainer) {
    components.fairnessDashboard = new FairnessDashboard(store, { container: fairnessContainer });
  }

  return { store, components };
}

if (typeof window !== "undefined") {
  window.addEventListener("DOMContentLoaded", () => {
    const app = bootstrapApp({});
    window.__SCHEDULER_APP__ = app;
  });
}