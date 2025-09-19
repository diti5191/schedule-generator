import test from "node:test";
import assert from "node:assert/strict";

import { createAppStore } from "../src/store.js";
import { FairnessDashboard } from "../src/components/fairnessDashboard.js";

class MockContainer {
  constructor() {
    this.innerHTML = "";
  }
}

test("fairness dashboard reports deltas for configured targets", () => {
  const store = createAppStore();
  store.setWindow({ start: "2026-01-05", end: "2026-03-27" });
  store.setFairnessTargets({
    weekendCall: { JOO: 2, KC: 1 },
    hospitalDays: { JOO: 3, KC: 0 },
  });
  store.setCallAssignments([
    { date: "2026-01-10", type: "weekend_noninvasive", provider: "JOO" },
    { date: "2026-01-11", type: "weekend_noninvasive", provider: "JOO" },
    { date: "2026-01-11", type: "weekend_interventional", provider: "KC" },
  ]);
  store.setSchedule([
    { date: "2026-01-05", site_type: "hospital", provider: "JOO" },
    { date: "2026-01-06", site_type: "hospital", provider: "JOO" },
    { date: "2026-01-07", site_type: "hospital", provider: "KC" },
  ]);

  const container = new MockContainer();
  const dashboard = new FairnessDashboard(store, { container });
  assert.match(container.innerHTML, /Weekend Call/);
  assert.match(container.innerHTML, /JOO/);
  assert.match(container.innerHTML, /KC/);
  assert.match(container.innerHTML, /\+1\.00/);

  const weekendRows = dashboard.computeWeekendCallDeltas();
  const jooRow = weekendRows.find((row) => row.provider === "JOO");
  assert.equal(jooRow.actual, 2);
  assert.equal(jooRow.target, 2);
  assert.equal(jooRow.delta, 0);
});