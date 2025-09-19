import { getISOWeekStart } from "../utils/date.js";

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

function providerIdFromAssignment(assignment) {
  return assignment.providerId ?? assignment.provider_id ?? assignment.provider ?? "";
}

export class FairnessDashboard {
  constructor(store, options = {}) {
    this.store = store;
    this.container = options.container ?? createNullContainer();
    this.windowDays = options.windowDays ?? 84; // 12 week lookback
    this.unsubscribe = this.store.subscribe(() => this.render());
    this.render();
  }

  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  }

  render() {
    const weekendRows = this.computeWeekendCallDeltas();
    const hospitalRows = this.computeHospitalBalance();
    const html = `<div class="fairness-dashboard">
      <p class="caption">Weekend call, hospital days, and fairness deltas compared to configured targets.</p>
      <div class="fairness-grid">
        <section>
          <h3>Weekend Call</h3>
          ${this.renderTable(weekendRows, "Weekend delta")}
        </section>
        <section>
          <h3>Hospital Days</h3>
          ${this.renderTable(hospitalRows, "Hospital delta")}
        </section>
      </div>
    </div>`;
    this.container.innerHTML = html;
  }

  renderTable(rows, deltaLabel) {
    if (!rows.length) {
      return '<p class="empty">No data</p>';
    }
    const body = rows
      .map((row) => `<tr>
        <td>${row.provider}</td>
        <td>${row.actual}</td>
        <td>${row.target}</td>
        <td>${row.delta > 0 ? "+" : ""}${row.delta.toFixed(2)}</td>
      </tr>`)
      .join("");
    return `<table>
      <thead>
        <tr>
          <th>Provider</th>
          <th>Actual</th>
          <th>Target</th>
          <th>${deltaLabel}</th>
        </tr>
      </thead>
      <tbody>${body}</tbody>
    </table>`;
  }

  computeWeekendCallDeltas() {
    const state = this.store.getState();
    const counts = new Map();
    const start = state.window ? getISOWeekStart(state.window.start) : null;
    for (const assignment of state.callAssignments) {
      if (assignment.type !== "weekend_noninvasive" && assignment.type !== "weekend_interventional") {
        continue;
      }
      const provider = providerIdFromAssignment(assignment);
      counts.set(provider, (counts.get(provider) ?? 0) + 1);
    }
    const targets = state.fairnessTargets?.weekendCall ?? {};
    const rows = [];
    for (const provider of Object.keys(targets)) {
      const target = targets[provider];
      const actual = counts.get(provider) ?? 0;
      rows.push({ provider, actual, target, delta: actual - target });
    }
    for (const [provider, actual] of counts.entries()) {
      if (typeof targets[provider] === "undefined") {
        rows.push({ provider, actual, target: 0, delta: actual });
      }
    }
    rows.sort((a, b) => b.delta - a.delta || a.provider.localeCompare(b.provider));
    return rows;
  }

  computeHospitalBalance() {
    const state = this.store.getState();
    const counts = new Map();
    const start = state.window ? getISOWeekStart(state.window.start) : null;
    for (const assignment of state.scheduleAssignments) {
      const siteType = assignment.site_type ?? assignment.siteType ?? assignment.site_type_code ?? "";
      if (siteType !== "hospital") {
        continue;
      }
      const provider = providerIdFromAssignment(assignment);
      counts.set(provider, (counts.get(provider) ?? 0) + 1);
    }
    const targets = state.fairnessTargets?.hospitalDays ?? {};
    const rows = [];
    for (const provider of Object.keys(targets)) {
      const target = targets[provider];
      const actual = counts.get(provider) ?? 0;
      rows.push({ provider, actual, target, delta: actual - target });
    }
    for (const [provider, actual] of counts.entries()) {
      if (typeof targets[provider] === "undefined") {
        rows.push({ provider, actual, target: 0, delta: actual });
      }
    }
    rows.sort((a, b) => b.delta - a.delta || a.provider.localeCompare(b.provider));
    return rows;
  }
}