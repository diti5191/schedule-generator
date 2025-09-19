import test from "node:test";
import assert from "node:assert/strict";

import { createAppStore, computeImpact } from "../src/store.js";
import { VacationRequestForm } from "../src/components/vacationForm.js";

class MockContainer {
  constructor() {
    this.innerHTML = "";
  }
  querySelector() {
    return null;
  }
}

test("vacation workflow enforces holidays and updates allowances", () => {
  const store = createAppStore();
  store.setWindow({ start: "2026-01-05", end: "2026-03-27" });
  store.setProviders([
    { id: "JOO", initials: "JOO" },
  ]);
  store.setAllowances([
    { providerId: "JOO", year: 2026, days_total: 20, days_used: 0, am_quota: 10, pm_quota: 10, am_used: 0, pm_used: 0 },
  ]);
  store.setHolidays([
    { date: "2026-01-19", is_office_closed: true },
  ]);

  const formContainer = new MockContainer();
  const allowanceContainer = new MockContainer();
  const form = new VacationRequestForm(store, { form: formContainer, allowance: allowanceContainer, year: 2026 });

  const draft = form.createDraft({
    providerId: "JOO",
    block: "FULLDAY",
    startDate: "2026-01-06",
    endDate: "2026-01-06",
  });
  assert.equal(draft.status, "DRAFT");

  const submitted = form.submit(draft.id, "tester");
  assert.equal(submitted.status, "SUBMITTED");

  const approved = form.approve(draft.id, "chief");
  assert.equal(approved.status, "APPROVED");

  const allowance = store.getState().allowances.JOO[2026];
  assert.equal(allowance.daysUsed, 1);
  assert.equal(allowance.amUsed, 1);
  assert.equal(allowance.pmUsed, 1);

  assert.match(formContainer.innerHTML, /VR-00001/);
  assert.match(allowanceContainer.innerHTML, /1\/20/);

  assert.throws(
    () =>
      form.createDraft({
        providerId: "JOO",
        block: "AM",
        startDate: "2026-01-19",
        endDate: "2026-01-19",
      }),
    /holiday/i,
  );
});

test("impact calculation handles full week spans", () => {
  const impact = computeImpact("FULLWEEK", "2026-02-02", "2026-02-06");
  assert.equal(impact.days, 5);
  assert.equal(impact.am, 5);
  assert.equal(impact.pm, 5);
});