import { addDays, formatDisplay, getISOWeekStart, toISODate } from "../utils/date.js";

function createNullContainer() {
  return {
    _html: "",
    set innerHTML(value) {
      this._html = value;
    },
    get innerHTML() {
      return this._html;
    },
  };
}

function providerLabel(assignment) {
  if (assignment.providerDisplay) {
    return assignment.providerDisplay;
  }
  if (assignment.providerInitials) {
    return assignment.providerInitials;
  }
  if (assignment.provider_id) {
    return assignment.provider_id;
  }
  if (assignment.providerId) {
    return assignment.providerId;
  }
  return assignment.provider ?? "";
}

function siteLabel(assignment) {
  return (
    assignment.siteLabel ??
    assignment.site_name ??
    assignment.siteName ??
    assignment.site_code ??
    assignment.siteCode ??
    assignment.site_id ??
    assignment.siteId ??
    assignment.site ??
    ""
  );
}

function normaliseAssignment(assignment) {
  return {
    ...assignment,
    date: toISODate(assignment.date),
    block: assignment.block ?? assignment.session ?? "AM",
    site: siteLabel(assignment),
    provider: providerLabel(assignment),
    siteType: assignment.site_type ?? assignment.siteType ?? "",
  };
}

function collateByBlock(assignments) {
  const buckets = new Map();
  for (const raw of assignments) {
    const item = normaliseAssignment(raw);
    const key = `${item.date}_${item.block}`;
    if (!buckets.has(key)) {
      buckets.set(key, []);
    }
    buckets.get(key).push(item);
  }
  for (const list of buckets.values()) {
    list.sort((a, b) => a.site.localeCompare(b.site));
  }
  return buckets;
}

function renderBlockCell(entries) {
  if (!entries || entries.length === 0) {
    return '<span class="empty">Unassigned</span>';
  }
  return entries
    .map((entry) => {
      const role = entry.role ? ` <span class="role">${entry.role}</span>` : "";
      return `<div class="site">${entry.site}: <strong>${entry.provider}</strong>${role}</div>`;
    })
    .join("");
}

function renderCallSummary(weekStart, callAssignments) {
  if (!callAssignments.length) {
    return "";
  }
  const start = getISOWeekStart(weekStart);
  const window = [];
  for (let day = 0; day < 7; day += 1) {
    window.push(toISODate(addDays(start, day)));
  }
  const filtered = callAssignments
    .map((assignment) => ({ ...assignment, date: toISODate(assignment.date) }))
    .filter((assignment) => window.includes(assignment.date));
  if (!filtered.length) {
    return "";
  }

  const weekdayNoninvasive = {};
  const weekdayInterventional = {};
  const weekendBuckets = { noninvasive: [], interventional: [] };

  for (const assignment of filtered) {
    const label = assignment.label ?? assignment.day ?? assignment.date;
    const provider = providerLabel(assignment);
    switch (assignment.type) {
      case "weekday_noninvasive":
        weekdayNoninvasive[label] = provider;
        break;
      case "weekday_interventional":
        weekdayInterventional[label] = provider;
        break;
      case "weekend_noninvasive":
        weekendBuckets.noninvasive.push({ label, provider });
        break;
      case "weekend_interventional":
        weekendBuckets.interventional.push({ label, provider });
        break;
      default:
        break;
    }
  }

  const weekdayRows = Object.keys(weekdayNoninvasive)
    .sort()
    .map((label) => `<tr><td>${label}</td><td>${weekdayNoninvasive[label]}</td></tr>`) // reuse for call table
    .join("");

  const interventionalRows = Object.keys(weekdayInterventional)
    .sort()
    .map((label) => `<tr><td>${label}</td><td>${weekdayInterventional[label]}</td></tr>`)
    .join("");

  const weekendRows = weekendBuckets.noninvasive
    .map((entry) => `<li>${entry.label}: ${entry.provider}</li>`)
    .join("");

  const weekendIntRows = weekendBuckets.interventional
    .map((entry) => `<li>${entry.label}: ${entry.provider}</li>`)
    .join("");

  return `<div class="call-summary">
    <h3>Call Coverage</h3>
    <div class="call-grid">
      <div>
        <h4>Weekday Noninvasive</h4>
        <table>${weekdayRows || '<tr><td colspan="2">n/a</td></tr>'}</table>
      </div>
      <div>
        <h4>Weekday Interventional</h4>
        <table>${interventionalRows || '<tr><td colspan="2">n/a</td></tr>'}</table>
      </div>
      <div>
        <h4>Weekend Noninvasive</h4>
        <ul>${weekendRows || "<li>n/a</li>"}</ul>
      </div>
      <div>
        <h4>Weekend Interventional</h4>
        <ul>${weekendIntRows || "<li>n/a</li>"}</ul>
      </div>
    </div>
  </div>`;
}

export class ScheduleBoard {
  constructor(store, options = {}) {
    this.store = store;
    this.container = options.container ?? createNullContainer();
    this.weekStart = options.weekStart ?? null;
    this.unsubscribe = this.store.subscribe(() => this.render());
    this.render();
  }

  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  }

  setWeekStart(date) {
    this.weekStart = toISODate(date);
    this.render();
  }

  render() {
    const state = this.store.getState();
    if (!state.window) {
      this.container.innerHTML = "<p>Scheduling window not configured.</p>";
      return;
    }
    const weekStart = this.weekStart ?? getISOWeekStart(state.window.start);
    const body = this.renderWeek(weekStart, state.scheduleAssignments);
    const callSummary = renderCallSummary(weekStart, state.callAssignments);
    this.container.innerHTML = `<div class="schedule-board__week">
      ${body}
      ${callSummary}
    </div>`;
  }

  renderWeek(weekStart, assignments) {
    const buckets = collateByBlock(assignments);
    const start = getISOWeekStart(weekStart);
    const rows = [];
    for (let day = 0; day < 5; day += 1) {
      const current = addDays(start, day);
      const iso = toISODate(current);
      const am = buckets.get(`${iso}_AM`) ?? [];
      const pm = buckets.get(`${iso}_PM`) ?? [];
      rows.push(`<tr>
        <td>${formatDisplay(current)}</td>
        <td>${renderBlockCell(am)}</td>
        <td>${renderBlockCell(pm)}</td>
      </tr>`);
    }
    return `<table class="schedule-board">
      <thead>
        <tr>
          <th>Day</th>
          <th>AM</th>
          <th>PM</th>
        </tr>
      </thead>
      <tbody>
        ${rows.join("")}
      </tbody>
    </table>`;
  }
}