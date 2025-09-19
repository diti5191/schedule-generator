import test from "node:test";
import assert from "node:assert/strict";

import { createAppStore } from "../src/store.js";
import { ScheduleBoard } from "../src/components/scheduleBoard.js";

class MockContainer {
  constructor() {
    this.innerHTML = "";
  }
}

test("schedule board groups assignments by day and block", () => {
  const store = createAppStore();
  store.setWindow({ start: "2026-01-05", end: "2026-03-27" });
  store.setSchedule([
    { date: "2026-01-05", block: "AM", site: "HH", provider: "JOO", role: "MD" },
    { date: "2026-01-05", block: "PM", site: "HH", provider: "KC", role: "APN" },
    { date: "2026-01-06", block: "AM", site: "WT", provider: "APZ", role: "MD" },
    { date: "2026-01-06", block: "PM", site: "WT", provider: "KC", role: "APN" },
  ]);
  store.setCallAssignments([
    { date: "2026-01-05", label: "Mon", type: "weekday_noninvasive", provider: "JOO" },
    { date: "2026-01-09", label: "Fri", type: "weekend_noninvasive", provider: "KC" },
  ]);

  const container = new MockContainer();
  const board = new ScheduleBoard(store, { container });
  assert.match(container.innerHTML, /HH: <strong>JOO/);
  assert.match(container.innerHTML, /Weekday Noninvasive/);
  assert.match(container.innerHTML, /Weekend Noninvasive/);

  board.setWeekStart("2026-01-12");
  assert.match(container.innerHTML, /Unassigned/);
});