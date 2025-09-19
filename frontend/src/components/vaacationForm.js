import { computeImpact } from "../store.js";
import { eachWeekdayBetween, formatDisplay, toISODate } from "../utils/date.js";

function createNullContainer() {
  return {
    _html: "",
    set innerHTML(value) {
      this._html = value;
    },
    get innerHTML() {
      return this._html;
    },
    querySelector() {
      return null;
    },
  };
}

function formatStatus(status) {
  return `<span class="pill ${status.toLowerCase()}">${status}</span>`;
}

function describeSpan(start, end) {
  const weekdays = eachWeekdayBetween(start, end);
  if (weekdays.length === 1) {
    const date = weekdays[0];
    const formatted = formatDisplay(date);
    return formatted;
  }
  const first = formatDisplay(weekdays[0]);
  const last = formatDisplay(weekdays[weekdays.length - 1]);
  return `${first} → ${last}`;
}

export class VacationRequestForm {
  constructor(store, options = {}) {
    this.store = store;
    this.formContainer = options.form ?? options.container ?? createNullContainer();
    this.allowanceContainer = options.allowance ?? createNullContainer();
    this.year = options.year ?? null;
    this.unsubscribe = this.store.subscribe(() => this.render());
    this.render();
  }

  destroy() {
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  }

  createDraft(payload) {
    return this.store.createVacationDraft(payload);
  }

  submit(id, actor = "user") {
    return this.store.submitVacationRequest(id, actor);
  }

  approve(id, approverId) {
    return this.store.approveVacationRequest(id, approverId);
  }

  deny(id, approverId, notes = "") {
    return this.store.denyVacationRequest(id, approverId, notes);
  }

  listRequests() {
    return this.store.getState().vacations;
  }

  render() {
    const state = this.store.getState();
    this.renderForm(state);
    this.renderAllowances(state);
  }

  renderForm(state) {
    const providerOptions = state.providers
      .map((provider) => `<option value="${provider.id}">${provider.initials ?? provider.full_name ?? provider.fullName ?? provider.id}</option>`)
      .join("");
    const requests = state.vacations
      .slice()
      .sort((a, b) => (a.startDate < b.startDate ? -1 : 1))
      .map((request) => {
        const span = describeSpan(request.startDate, request.endDate);
        return `<tr>
          <td>${request.id}</td>
          <td>${request.providerId}</td>
          <td>${request.block}</td>
          <td>${span}</td>
          <td>${formatStatus(request.status)}</td>
        </tr>`;
      })
      .join("");
    const content = `<form class="vacation-form" data-testid="vacation-form">
        <label>
          Provider
          <select name="provider" required>${providerOptions}</select>
        </label>
        <label>
          Block
          <select name="block" required>
            <option value="AM">AM</option>
            <option value="PM">PM</option>
            <option value="FULLDAY">Full Day</option>
            <option value="FULLWEEK">Full Week</option>
          </select>
        </label>
        <label>
          Start
          <input type="date" name="start" required />
        </label>
        <label>
          End
          <input type="date" name="end" />
        </label>
        <button type="submit">Create Draft</button>
      </form>
      <h3>Requests</h3>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Provider</th>
            <th>Block</th>
            <th>Span</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${requests || '<tr><td colspan="5">No requests yet</td></tr>'}
        </tbody>
      </table>`;
    this.formContainer.innerHTML = content;
    this.attachSubmitListener();
  }

  renderAllowances(state) {
    const activeYear = this.resolveActiveYear(state);
    const rows = state.providers
      .map((provider) => {
        const allowance = state.allowances?.[provider.id]?.[activeYear];
        if (!allowance) {
          return `<tr><td>${provider.id}</td><td colspan="3">n/a</td></tr>`;
        }
        const amQuota = allowance.amQuota === null ? "—" : `${allowance.amUsed}/${allowance.amQuota}`;
        const pmQuota = allowance.pmQuota === null ? "—" : `${allowance.pmUsed}/${allowance.pmQuota}`;
        const total = `${allowance.daysUsed}/${allowance.daysTotal}`;
        return `<tr>
          <td>${provider.id}</td>
          <td>${total}</td>
          <td>${amQuota}</td>
          <td>${pmQuota}</td>
        </tr>`;
      })
      .join("");
    const content = `<div class="allowance-card">
      <p>Tracking allowances for <strong>${activeYear}</strong>. Totals update automatically as requests are approved.</p>
      <table>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Days Used</th>
            <th>AM Units</th>
            <th>PM Units</th>
          </tr>
        </thead>
        <tbody>
          ${rows || '<tr><td colspan="4">No providers loaded</td></tr>'}
        </tbody>
      </table>
    </div>`;
    this.allowanceContainer.innerHTML = content;
  }

  resolveActiveYear(state) {
    if (this.year) {
      return this.year;
    }
    if (state.window?.start) {
      return Number.parseInt(state.window.start.slice(0, 4), 10);
    }
    const now = new Date();
    return now.getUTCFullYear();
  }

  attachSubmitListener() {
    if (typeof window === "undefined") {
      return;
    }
    const form = this.formContainer.querySelector("form");
    if (!form) {
      return;
    }
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const formData = new FormData(form);
      const providerId = formData.get("provider");
      const block = formData.get("block");
      const start = formData.get("start");
      const end = formData.get("end") || start;
      const payload = {
        providerId,
        block,
        startDate: toISODate(start),
        endDate: toISODate(end),
        actor: "ui",
      };
      this.createDraft(payload);
    });
  }

  getAllowanceImpact(block, startDate, endDate) {
    return computeImpact(block, startDate, endDate ?? startDate);
  }
}