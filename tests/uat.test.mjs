import assert from "node:assert/strict";
import test from "node:test";

import { createWarehouse } from "../prototype/domain.js";
import { createSyntheticState } from "../prototype/synthetic-data.js";


const store = (overrides = {}) => createWarehouse(createSyntheticState(overrides));

function receiveAndAssign(warehouse, palletId = "PLT-UAT-001") {
  assert.equal(warehouse.receivePallet({
    palletId,
    receiptBarcode: `RCPT-${palletId}`,
    skuId: "SKU-DEMO-A",
    lotCode: "LOT-UAT-01",
    quantity: 10,
  }).ok, true);
  const assignment = warehouse.assignLocation(palletId);
  assert.equal(assignment.ok, true);
  return assignment.value.task;
}

function event(task, eventId, eventType, minute = "10", extra = {}) {
  return {
    eventId,
    taskId: task.id,
    deviceId: task.deviceId,
    eventType,
    correlationId: task.correlationId,
    eventAt: `2026-01-01T00:${minute}:00Z`,
    simulated: true,
    ...extra,
  };
}

test("UAT-01 happy path commits one inventory movement", () => {
  const warehouse = store();
  const task = receiveAndAssign(warehouse);
  assert.equal(warehouse.dispatchTask(task.id).ok, true);
  assert.equal(warehouse.applyWcsEvent(event(task, "EVT-UAT-01-A", "TASK_STARTED", "10")).ok, true);
  assert.equal(warehouse.applyWcsEvent(event(task, "EVT-UAT-01-B", "TASK_COMPLETED", "12")).ok, true);
  const snapshot = warehouse.getSnapshot();
  assert.equal(snapshot.tasks[0].state, "COMPLETED");
  assert.equal(snapshot.inventoryMovements.length, 1);
});

test("UAT-02 malformed receipt barcode is rejected without a pallet", () => {
  const warehouse = store();
  const result = warehouse.receivePallet({ palletId: "PLT-UAT-002", receiptBarcode: "bad barcode", skuId: "SKU-DEMO-A", lotCode: "LOT-UAT", quantity: 1 });
  assert.equal(result.error.code, "INVALID_BARCODE");
  assert.equal(warehouse.getSnapshot().pallets.length, 0);
});

test("UAT-03 unknown or inactive SKU is rejected", () => {
  const warehouse = store();
  const result = warehouse.receivePallet({ palletId: "PLT-UAT-003", receiptBarcode: "RCPT-UAT-003", skuId: "SKU-DEMO-C", lotCode: "LOT-UAT", quantity: 1 });
  assert.equal(result.error.code, "UNKNOWN_OR_INACTIVE_SKU");
  assert.equal(warehouse.getSnapshot().tasks.length, 0);
});

test("UAT-04 zero quantity is rejected", () => {
  const warehouse = store();
  const result = warehouse.receivePallet({ palletId: "PLT-UAT-004", receiptBarcode: "RCPT-UAT-004", skuId: "SKU-DEMO-A", lotCode: "LOT-UAT", quantity: 0 });
  assert.equal(result.error.code, "INVALID_QUANTITY");
  assert.equal(warehouse.getSnapshot().pallets.length, 0);
});

test("UAT-05 duplicate pallet preserves the original record", () => {
  const warehouse = store();
  const input = { palletId: "PLT-UAT-005", receiptBarcode: "RCPT-UAT-005", skuId: "SKU-DEMO-A", lotCode: "LOT-UAT", quantity: 8 };
  assert.equal(warehouse.receivePallet(input).ok, true);
  assert.equal(warehouse.receivePallet({ ...input, quantity: 99 }).error.code, "DUPLICATE_PALLET");
  assert.equal(warehouse.getSnapshot().pallets[0].quantity, 8);
});

test("UAT-06 no compatible capacity creates an exception and no task", () => {
  const warehouse = store({ locations: [{ id: "LOC-FULL", code: "A01", zonePriority: 1, compatibilityKey: "AMBIENT", capacity: 1, used: 1 }] });
  warehouse.receivePallet({ palletId: "PLT-UAT-006", receiptBarcode: "RCPT-UAT-006", skuId: "SKU-DEMO-A", lotCode: "LOT-UAT", quantity: 1 });
  assert.equal(warehouse.assignLocation("PLT-UAT-006").error.code, "NO_AVAILABLE_LOCATION");
  assert.equal(warehouse.getSnapshot().tasks.length, 0);
});

test("UAT-07 offline initial dispatch fails without creating a command or retry", () => {
  const warehouse = store({ deviceStatus: "offline" });
  const task = receiveAndAssign(warehouse, "PLT-UAT-007");
  assert.equal(warehouse.dispatchTask(task.id).error.code, "DEVICE_OFFLINE");
  const snapshot = warehouse.getSnapshot();
  assert.equal(snapshot.tasks[0].retryCount, 0);
  assert.equal(snapshot.commands.length, 0);
});

test("UAT-08 pallet jam creates a failed task and visible exception", () => {
  const warehouse = store();
  const task = receiveAndAssign(warehouse, "PLT-UAT-008");
  warehouse.dispatchTask(task.id);
  warehouse.applyWcsEvent(event(task, "EVT-UAT-08", "TASK_FAILED", "10", { reasonCode: "PALLET_JAM" }));
  const snapshot = warehouse.getSnapshot();
  assert.equal(snapshot.tasks[0].state, "FAILED");
  assert.equal(snapshot.activeExceptions[0].type, "PALLET_JAM");
});

test("UAT-09 timeout creates a timed-out task and visible exception", () => {
  const warehouse = store();
  const task = receiveAndAssign(warehouse, "PLT-UAT-009");
  warehouse.dispatchTask(task.id);
  warehouse.applyWcsEvent(event(task, "EVT-UAT-09", "TASK_TIMEOUT", "10"));
  const snapshot = warehouse.getSnapshot();
  assert.equal(snapshot.tasks[0].state, "TIMED_OUT");
  assert.equal(snapshot.activeExceptions[0].type, "TASK_TIMEOUT");
});

test("UAT-10 eligible retry dispatches after device recovery", () => {
  const warehouse = store({ deviceStatus: "offline" });
  const task = receiveAndAssign(warehouse, "PLT-UAT-010");
  warehouse.dispatchTask(task.id);
  warehouse.setDeviceStatus(task.deviceId, "online");
  const retry = warehouse.retryTask(task.id);
  assert.equal(retry.ok, true);
  assert.equal(retry.value.task.state, "DISPATCHED");
  assert.equal(retry.value.command.attemptNumber, 1);
});

test("UAT-11 third failure escalates and creates no third retry command", () => {
  const warehouse = store({ deviceStatus: "offline" });
  const task = receiveAndAssign(warehouse, "PLT-UAT-011");
  warehouse.dispatchTask(task.id);
  warehouse.retryTask(task.id);
  const result = warehouse.retryTask(task.id);
  assert.equal(result.error.code, "RETRY_LIMIT_REACHED");
  assert.equal(result.value.exception.status, "escalated");
  assert.equal(warehouse.getSnapshot().commands.length, 0);
});

test("UAT-12 cancellation is allowed from timeout and rejected after completion", () => {
  const warehouse = store();
  const timedOut = receiveAndAssign(warehouse, "PLT-UAT-012-A");
  warehouse.dispatchTask(timedOut.id);
  warehouse.applyWcsEvent(event(timedOut, "EVT-UAT-12-A", "TASK_TIMEOUT", "10"));
  assert.equal(warehouse.cancelTask(timedOut.id).value.task.state, "CANCELLED");

  const completed = receiveAndAssign(warehouse, "PLT-UAT-012-B");
  warehouse.dispatchTask(completed.id);
  warehouse.applyWcsEvent(event(completed, "EVT-UAT-12-B", "TASK_COMPLETED", "20"));
  assert.equal(warehouse.cancelTask(completed.id).error.code, "CANCELLATION_NOT_ALLOWED");
});

test("UAT-13 duplicate event returns success without a second mutation", () => {
  const warehouse = store();
  const task = receiveAndAssign(warehouse, "PLT-UAT-013");
  warehouse.dispatchTask(task.id);
  const completion = event(task, "EVT-UAT-13", "TASK_COMPLETED", "10");
  assert.equal(warehouse.applyWcsEvent(completion).value.duplicate, false);
  const replay = warehouse.applyWcsEvent(completion);
  assert.equal(replay.value.duplicate, true);
  assert.equal(replay.value.inventoryMutated, false);
  assert.equal(warehouse.getSnapshot().inventoryMovements.length, 1);
});

test("UAT-14 metrics reconcile to the fixed dispatched cohort", () => {
  const warehouse = store({ tasks: [
    { id: "TASK-UAT-1", state: "COMPLETED", retryCount: 0, failureCount: 0, dispatchedAt: "2026-01-01T00:00:00Z", completedAt: "2026-01-01T00:01:00Z" },
    { id: "TASK-UAT-2", state: "COMPLETED", retryCount: 1, failureCount: 1, dispatchedAt: "2026-01-01T00:00:00Z", completedAt: "2026-01-01T00:03:00Z" },
    { id: "TASK-UAT-3", state: "FAILED", retryCount: 2, failureCount: 3, dispatchedAt: "2026-01-01T00:00:00Z", completedAt: null },
    { id: "TASK-UAT-4", state: "TIMED_OUT", retryCount: 0, failureCount: 1, dispatchedAt: "2026-01-01T00:00:00Z", completedAt: null },
    { id: "TASK-UAT-5", state: "VALIDATED", retryCount: 0, failureCount: 0, dispatchedAt: null, completedAt: null },
  ] });
  assert.deepEqual(warehouse.getMetrics(), {
    dispatchedCount: 4,
    completionRate: 0.5,
    exceptionRate: 0.75,
    firstPassSuccessRate: 0.25,
    averageSimulatedCycleTimeSeconds: 120,
  });
});
