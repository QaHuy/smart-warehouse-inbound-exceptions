import assert from "node:assert/strict";
import test from "node:test";

import { createWarehouse } from "../prototype/domain.js";
import { createSyntheticState } from "../prototype/synthetic-data.js";


function store(overrides = {}) {
  return createWarehouse(createSyntheticState(overrides));
}

function receiveAndAssign(warehouse, palletId = "PLT-DEMO-001") {
  const receipt = warehouse.receivePallet({
    palletId,
    receiptBarcode: `RCPT-${palletId}`,
    skuId: "SKU-DEMO-A",
    lotCode: "LOT-DEMO-01",
    quantity: 10,
  });
  assert.equal(receipt.ok, true);
  const assignment = warehouse.assignLocation(palletId);
  assert.equal(assignment.ok, true);
  return assignment.value.task;
}

test("valid receipt stays unassigned until deterministic location selection creates a validated task", () => {
  const warehouse = store({
    locations: [
      { id: "LOC-DEMO-B02", code: "B02", zonePriority: 2, compatibilityKey: "AMBIENT", capacity: 2, used: 0 },
      { id: "LOC-DEMO-A02", code: "A02", zonePriority: 1, compatibilityKey: "AMBIENT", capacity: 2, used: 0 },
      { id: "LOC-DEMO-A01", code: "A01", zonePriority: 1, compatibilityKey: "AMBIENT", capacity: 2, used: 0 },
      { id: "LOC-DEMO-C01", code: "C01", zonePriority: 0, compatibilityKey: "CHILLED", capacity: 2, used: 0 },
    ],
  });

  const receipt = warehouse.receivePallet({
    palletId: "PLT-DEMO-001",
    receiptBarcode: "RCPT-DEMO-001",
    skuId: "SKU-DEMO-A",
    lotCode: "LOT-DEMO-01",
    quantity: 10,
  });
  assert.equal(receipt.ok, true);
  assert.equal(receipt.value.pallet.currentLocationId, null);
  assert.equal(warehouse.getSnapshot().tasks.length, 0);

  const assignment = warehouse.assignLocation("PLT-DEMO-001");
  assert.equal(assignment.ok, true);
  assert.equal(assignment.value.location.id, "LOC-DEMO-A01");
  assert.equal(assignment.value.task.state, "VALIDATED");
  assert.deepEqual(assignment.value.task.stateHistory.map((entry) => entry.state), ["CREATED", "VALIDATED"]);
});

test("receipt validation rejects malformed, unknown, non-positive, and duplicate input without partial mutation", () => {
  const warehouse = store();
  const valid = {
    palletId: "PLT-DEMO-001",
    receiptBarcode: "RCPT-DEMO-001",
    skuId: "SKU-DEMO-A",
    lotCode: "LOT-DEMO-01",
    quantity: 10,
  };

  assert.equal(warehouse.receivePallet({ ...valid, palletId: "PLT-BAD-01", receiptBarcode: "bad barcode" }).error.code, "INVALID_BARCODE");
  assert.equal(warehouse.receivePallet({ ...valid, palletId: "PLT-BAD-02", skuId: "SKU-UNKNOWN" }).error.code, "UNKNOWN_OR_INACTIVE_SKU");
  assert.equal(warehouse.receivePallet({ ...valid, palletId: "PLT-BAD-03", quantity: 0 }).error.code, "INVALID_QUANTITY");
  assert.equal(warehouse.receivePallet({ ...valid, palletId: "PLT-BAD-04", quantity: 1.5 }).error.code, "INVALID_QUANTITY");
  assert.equal(warehouse.receivePallet(valid).ok, true);
  assert.equal(warehouse.receivePallet({ ...valid, quantity: 99 }).error.code, "DUPLICATE_PALLET");
  assert.equal(warehouse.getSnapshot().pallets.length, 1);
  assert.equal(warehouse.getSnapshot().pallets[0].quantity, 10);
});

test("no compatible capacity creates one visible exception and no movement task", () => {
  const warehouse = store({
    locations: [
      { id: "LOC-DEMO-A01", code: "A01", zonePriority: 1, compatibilityKey: "AMBIENT", capacity: 1, used: 1 },
      { id: "LOC-DEMO-C01", code: "C01", zonePriority: 0, compatibilityKey: "CHILLED", capacity: 3, used: 0 },
    ],
  });
  warehouse.receivePallet({
    palletId: "PLT-DEMO-001",
    receiptBarcode: "RCPT-DEMO-001",
    skuId: "SKU-DEMO-A",
    lotCode: "LOT-DEMO-01",
    quantity: 10,
  });

  const result = warehouse.assignLocation("PLT-DEMO-001");
  assert.equal(result.ok, false);
  assert.equal(result.error.code, "NO_AVAILABLE_LOCATION");
  const snapshot = warehouse.getSnapshot();
  assert.equal(snapshot.tasks.length, 0);
  assert.equal(snapshot.activeExceptions.length, 1);
  assert.equal(snapshot.activeExceptions[0].type, "NO_AVAILABLE_LOCATION");
});

test("online dispatch and valid WCS events commit inventory exactly once", () => {
  const warehouse = store();
  const task = receiveAndAssign(warehouse);

  const dispatch = warehouse.dispatchTask(task.id);
  assert.equal(dispatch.ok, true);
  assert.equal(dispatch.value.task.state, "DISPATCHED");
  assert.equal(dispatch.value.command.attemptNumber, 0);

  const started = warehouse.applyWcsEvent({
    eventId: "EVT-DEMO-START-01",
    taskId: task.id,
    deviceId: task.deviceId,
    eventType: "TASK_STARTED",
    correlationId: task.correlationId,
    eventAt: "2026-01-01T00:01:00Z",
    simulated: true,
  });
  assert.equal(started.ok, true);
  assert.equal(started.value.task.state, "IN_PROGRESS");

  const completedEvent = {
    eventId: "EVT-DEMO-COMPLETE-01",
    taskId: task.id,
    deviceId: task.deviceId,
    eventType: "TASK_COMPLETED",
    correlationId: task.correlationId,
    eventAt: "2026-01-01T00:02:00Z",
    simulated: true,
  };
  const completed = warehouse.applyWcsEvent(completedEvent);
  assert.equal(completed.ok, true);
  assert.equal(completed.value.duplicate, false);
  assert.equal(completed.value.task.state, "COMPLETED");
  assert.equal(warehouse.getSnapshot().inventoryMovements.length, 1);

  const replay = warehouse.applyWcsEvent(completedEvent);
  assert.equal(replay.ok, true);
  assert.equal(replay.value.duplicate, true);
  assert.equal(replay.value.stateMutated, false);
  assert.equal(replay.value.inventoryMutated, false);
  assert.equal(warehouse.getSnapshot().inventoryMovements.length, 1);
});

test("unknown and out-of-sequence events fail closed without inventory mutation", () => {
  const warehouse = store();
  const task = receiveAndAssign(warehouse);
  const unknown = warehouse.applyWcsEvent({
    eventId: "EVT-DEMO-UNKNOWN",
    taskId: "TASK-UNKNOWN",
    deviceId: task.deviceId,
    eventType: "TASK_STARTED",
    correlationId: "CORR-UNKNOWN",
    eventAt: "2026-01-01T00:01:00Z",
    simulated: true,
  });
  assert.equal(unknown.error.code, "UNKNOWN_TASK");

  const invalid = warehouse.applyWcsEvent({
    eventId: "EVT-DEMO-EARLY-COMPLETE",
    taskId: task.id,
    deviceId: task.deviceId,
    eventType: "TASK_COMPLETED",
    correlationId: task.correlationId,
    eventAt: "2026-01-01T00:01:00Z",
    simulated: true,
  });
  assert.equal(invalid.error.code, "INVALID_TRANSITION");
  assert.equal(warehouse.getSnapshot().inventoryMovements.length, 0);
});

test("offline initial dispatch and two failed retries escalate on the third failure", () => {
  const warehouse = store({ deviceStatus: "offline" });
  const task = receiveAndAssign(warehouse);

  const initial = warehouse.dispatchTask(task.id);
  assert.equal(initial.ok, false);
  assert.equal(initial.error.code, "DEVICE_OFFLINE");
  assert.equal(initial.value.task.state, "FAILED");
  assert.equal(initial.value.task.failureCount, 1);
  assert.equal(initial.value.task.retryCount, 0);

  const retryOne = warehouse.retryTask(task.id);
  assert.equal(retryOne.error.code, "DEVICE_OFFLINE");
  assert.equal(retryOne.value.task.failureCount, 2);
  assert.equal(retryOne.value.task.retryCount, 1);
  assert.equal(retryOne.value.exception.status, "open");

  const retryTwo = warehouse.retryTask(task.id);
  assert.equal(retryTwo.error.code, "RETRY_LIMIT_REACHED");
  assert.equal(retryTwo.value.task.failureCount, 3);
  assert.equal(retryTwo.value.task.retryCount, 2);
  assert.equal(retryTwo.value.exception.status, "escalated");
  const commandCount = warehouse.getSnapshot().commands.length;

  const afterLimit = warehouse.retryTask(task.id);
  assert.equal(afterLimit.error.code, "RETRY_LIMIT_REACHED");
  assert.equal(warehouse.getSnapshot().commands.length, commandCount);
});

test("jam and timeout events create visible exceptions and cancellation respects terminal states", () => {
  const warehouse = store();
  const jamTask = receiveAndAssign(warehouse, "PLT-DEMO-JAM");
  warehouse.dispatchTask(jamTask.id);
  const jam = warehouse.applyWcsEvent({
    eventId: "EVT-DEMO-JAM",
    taskId: jamTask.id,
    deviceId: jamTask.deviceId,
    eventType: "TASK_FAILED",
    reasonCode: "PALLET_JAM",
    correlationId: jamTask.correlationId,
    eventAt: "2026-01-01T00:03:00Z",
    simulated: true,
  });
  assert.equal(jam.ok, true);
  assert.equal(jam.value.task.state, "FAILED");
  assert.equal(warehouse.getSnapshot().activeExceptions.some((item) => item.type === "PALLET_JAM"), true);

  const timeoutTask = receiveAndAssign(warehouse, "PLT-DEMO-TIMEOUT");
  warehouse.dispatchTask(timeoutTask.id);
  const timeout = warehouse.applyWcsEvent({
    eventId: "EVT-DEMO-TIMEOUT",
    taskId: timeoutTask.id,
    deviceId: timeoutTask.deviceId,
    eventType: "TASK_TIMEOUT",
    correlationId: timeoutTask.correlationId,
    eventAt: "2026-01-01T00:04:00Z",
    simulated: true,
  });
  assert.equal(timeout.value.task.state, "TIMED_OUT");
  assert.equal(warehouse.cancelTask(timeoutTask.id).value.task.state, "CANCELLED");
  assert.equal(warehouse.cancelTask(timeoutTask.id).error.code, "CANCELLATION_NOT_ALLOWED");
});

test("metrics use only the dispatched cohort and preserve N/A for an empty cohort", () => {
  const empty = store();
  assert.deepEqual(empty.getMetrics(), {
    dispatchedCount: 0,
    completionRate: null,
    exceptionRate: null,
    firstPassSuccessRate: null,
    averageSimulatedCycleTimeSeconds: null,
  });

  const warehouse = store({
    tasks: [
      { id: "TASK-1", state: "COMPLETED", retryCount: 0, failureCount: 0, dispatchedAt: "2026-01-01T00:00:00Z", completedAt: "2026-01-01T00:01:00Z" },
      { id: "TASK-2", state: "COMPLETED", retryCount: 1, failureCount: 1, dispatchedAt: "2026-01-01T00:00:00Z", completedAt: "2026-01-01T00:03:00Z" },
      { id: "TASK-3", state: "FAILED", retryCount: 2, failureCount: 3, dispatchedAt: "2026-01-01T00:00:00Z", completedAt: null },
      { id: "TASK-4", state: "TIMED_OUT", retryCount: 0, failureCount: 1, dispatchedAt: "2026-01-01T00:00:00Z", completedAt: null },
      { id: "TASK-5", state: "VALIDATED", retryCount: 0, failureCount: 0, dispatchedAt: null, completedAt: null },
    ],
  });
  assert.deepEqual(warehouse.getMetrics(), {
    dispatchedCount: 4,
    completionRate: 0.5,
    exceptionRate: 0.75,
    firstPassSuccessRate: 0.25,
    averageSimulatedCycleTimeSeconds: 120,
  });
});

test("audit trail is chronological, complete for mutations, and returned as a defensive copy", () => {
  const warehouse = store();
  const task = receiveAndAssign(warehouse);
  warehouse.dispatchTask(task.id);
  warehouse.cancelTask(task.id);
  const audit = warehouse.getAuditTrail();
  assert.equal(audit.length > 0, true);
  for (const entry of audit) {
    assert.equal(Boolean(entry.id && entry.action && entry.actor && entry.timestamp), true);
  }
  assert.deepEqual([...audit].sort((a, b) => a.timestamp.localeCompare(b.timestamp)), audit);
  audit[0].action = "MUTATED-BY-CALLER";
  assert.notEqual(warehouse.getAuditTrail()[0].action, "MUTATED-BY-CALLER");
});
