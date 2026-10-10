import { createWarehouse } from "./domain.js";
import { createSyntheticState } from "./synthetic-data.js";

let warehouse = createWarehouse(createSyntheticState());
let eventSequence = 0;
let lastCompletionEvent = null;

const byId = (id) => document.getElementById(id);
const views = [...document.querySelectorAll(".view")];
const navButtons = [...document.querySelectorAll(".nav-button")];

function statusTone(state) {
  if (["COMPLETED", "resolved"].includes(state)) return "success";
  if (["FAILED", "TIMED_OUT", "open"].includes(state)) return "warning";
  if (["CANCELLED", "escalated"].includes(state)) return "danger";
  return "neutral";
}

function status(message, tone = "neutral") {
  const target = byId("live-status");
  target.textContent = message;
  target.className = `live-status${tone === "neutral" ? "" : ` is-${tone}`}`;
}

function showView(viewId) {
  for (const view of views) view.hidden = view.id !== viewId;
  for (const button of navButtons) {
    const active = button.dataset.view === viewId;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  }
}

function cell(row, value, className = "") {
  const td = document.createElement("td");
  td.textContent = value ?? "—";
  if (className) td.className = className;
  row.append(td);
  return td;
}

function pill(row, value) {
  const td = document.createElement("td");
  const span = document.createElement("span");
  span.className = "status-pill";
  span.dataset.tone = statusTone(value);
  span.textContent = value;
  td.append(span);
  row.append(td);
}

function emptyRow(tableBody, columns, message) {
  const row = document.createElement("tr");
  const td = cell(row, message, "empty-cell");
  td.colSpan = columns;
  tableBody.append(row);
}

function formatRate(value) {
  return value === null ? "N/A" : `${Math.round(value * 100)}%`;
}

function renderMetrics() {
  const metrics = warehouse.getMetrics();
  byId("metric-dispatched").textContent = metrics.dispatchedCount;
  byId("metric-completion").textContent = formatRate(metrics.completionRate);
  byId("metric-exception").textContent = formatRate(metrics.exceptionRate);
  byId("metric-first-pass").textContent = formatRate(metrics.firstPassSuccessRate);
  byId("metric-cycle").textContent = metrics.averageSimulatedCycleTimeSeconds === null
    ? "N/A"
    : `${metrics.averageSimulatedCycleTimeSeconds}s`;
}

function renderTasks(snapshot) {
  const table = byId("task-table");
  const select = byId("task-select");
  const selected = select.value;
  table.replaceChildren();
  select.replaceChildren();

  if (!snapshot.tasks.length) {
    emptyRow(table, 7, "No movement tasks.");
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No tasks available";
    select.append(option);
    return;
  }

  for (const task of snapshot.tasks) {
    const option = document.createElement("option");
    option.value = task.id;
    option.textContent = `${task.id} · ${task.state}`;
    select.append(option);

    const row = document.createElement("tr");
    cell(row, task.id);
    cell(row, task.palletId);
    cell(row, task.destinationLocationId);
    pill(row, task.state);
    cell(row, task.retryCount);
    cell(row, task.failureCount);
    cell(row, task.correlationId);
    table.append(row);
  }

  if ([...select.options].some((option) => option.value === selected)) select.value = selected;
}

function renderExceptions(snapshot) {
  const table = byId("exception-table");
  table.replaceChildren();
  if (!snapshot.exceptions.length) emptyRow(table, 7, "No exceptions.");

  for (const exception of [...snapshot.exceptions].reverse()) {
    const row = document.createElement("tr");
    cell(row, exception.id);
    cell(row, exception.type);
    cell(row, exception.taskId ?? exception.palletId);
    pill(row, exception.status);
    cell(row, exception.failureCount ?? 0);
    cell(row, exception.retryCount ?? 0);
    cell(row, exception.reason);
    table.append(row);
  }

  byId("exception-open").textContent = snapshot.exceptions.filter((item) => item.status === "open").length;
  byId("exception-escalated").textContent = snapshot.exceptions.filter((item) => item.status === "escalated").length;
  byId("exception-closed").textContent = snapshot.exceptions.filter((item) => ["resolved", "cancelled"].includes(item.status)).length;
}

function renderInventory(snapshot) {
  const table = byId("inventory-table");
  table.replaceChildren();
  if (!snapshot.inventoryMovements.length) emptyRow(table, 5, "No inventory movements.");
  for (const movement of [...snapshot.inventoryMovements].reverse()) {
    const row = document.createElement("tr");
    cell(row, movement.id);
    cell(row, movement.palletId);
    cell(row, movement.toLocationId);
    cell(row, movement.sourceEventId);
    cell(row, movement.committedAt);
    table.append(row);
  }
}

function renderAudit() {
  const table = byId("audit-table");
  const audit = warehouse.getAuditTrail();
  table.replaceChildren();
  if (!audit.length) emptyRow(table, 4, "No audit events.");
  for (const item of [...audit].reverse().slice(0, 16)) {
    const row = document.createElement("tr");
    cell(row, item.timestamp);
    cell(row, item.action);
    cell(row, item.entityId);
    cell(row, item.priorState || item.newState ? `${item.priorState ?? "—"} → ${item.newState ?? "—"}` : item.details);
    table.append(row);
  }
}

function render() {
  const snapshot = warehouse.getSnapshot();
  renderMetrics();
  renderTasks(snapshot);
  renderExceptions(snapshot);
  renderInventory(snapshot);
  renderAudit();
}

function explain(result, successMessage) {
  if (result.ok) {
    status(successMessage, "success");
    return true;
  }
  status(`${result.error.code}: ${result.error.message}`, "error");
  return false;
}

function receive(values) {
  const result = warehouse.receivePallet(values);
  explain(result, `Receipt accepted for ${values.palletId}. No movement task exists until location assignment.`);
  render();
  return result;
}

function assign(palletId) {
  const result = warehouse.assignLocation(palletId);
  if (result.ok) {
    const { location, task } = result.value;
    byId("assignment-result").textContent = `${location.code} selected. ${task.id} created and validated.`;
    status(`${task.id} assigned to ${location.code} using compatibility, capacity, zone priority, and code tie-break rules.`, "success");
  } else {
    byId("assignment-result").textContent = `${result.error.code}: ${result.error.message}`;
    status(`${result.error.code}: ${result.error.message}`, "error");
  }
  render();
  return result;
}

function selectedTask() {
  const taskId = byId("task-select").value;
  return warehouse.getSnapshot().tasks.find((task) => task.id === taskId) ?? null;
}

function dispatch(taskId) {
  const result = warehouse.dispatchTask(taskId);
  explain(result, `${taskId} dispatched; a simulated WCS command was recorded.`);
  render();
  return result;
}

function nextEvent(task, eventType, fixedId = null) {
  eventSequence += 1;
  const minute = String(Math.min(59, eventSequence + 10)).padStart(2, "0");
  return {
    eventId: fixedId ?? `EVT-DEMO-UI-${String(eventSequence).padStart(3, "0")}`,
    taskId: task.id,
    deviceId: task.deviceId,
    eventType,
    ...(eventType === "TASK_FAILED" ? { reasonCode: "PALLET_JAM" } : {}),
    correlationId: task.correlationId,
    eventAt: `2026-01-01T00:${minute}:00Z`,
    simulated: true,
  };
}

function applyEvent(task, eventType, event = null) {
  const payload = event ?? nextEvent(task, eventType);
  const result = warehouse.applyWcsEvent(payload);
  if (result.ok && result.value.duplicate) {
    status(`${payload.eventId} was a duplicate. State and inventory were not changed.`, "success");
  } else {
    explain(result, `${eventType} accepted for ${task.id}. State and controls were updated.`);
  }
  if (eventType === "TASK_COMPLETED" && result.ok && !result.value.duplicate) lastCompletionEvent = payload;
  render();
  return result;
}

function reset(deviceStatus = "online") {
  warehouse = createWarehouse(createSyntheticState({ deviceStatus }));
  eventSequence = 0;
  lastCompletionEvent = null;
  byId("assignment-result").textContent = "No location assigned yet.";
  render();
}

function createScenarioTask(palletId) {
  const receipt = receive({
    palletId,
    receiptBarcode: `RCPT-${palletId}`,
    skuId: "SKU-DEMO-A",
    lotCode: "LOT-DEMO-01",
    quantity: 10,
  });
  if (!receipt.ok) return null;
  const assignment = assign(palletId);
  return assignment.ok ? assignment.value.task : null;
}

function runScenario(name) {
  if (name === "happy") {
    reset("online");
    const task = createScenarioTask("PLT-DEMO-HAPPY");
    dispatch(task.id);
    applyEvent(task, "TASK_STARTED");
    applyEvent(task, "TASK_COMPLETED");
    showView("inventory-view");
    status("Happy path complete: inventory committed once after a valid completion event.", "success");
  }

  if (name === "offline") {
    reset("offline");
    const task = createScenarioTask("PLT-DEMO-OFFLINE");
    dispatch(task.id);
    warehouse.retryTask(task.id);
    warehouse.retryTask(task.id);
    render();
    showView("exception-view");
    status("Offline scenario complete: initial failure plus two failed retries produced an escalated exception; no third retry command exists.", "error");
  }

  if (name === "duplicate") {
    reset("online");
    const task = createScenarioTask("PLT-DEMO-DUPLICATE");
    dispatch(task.id);
    applyEvent(task, "TASK_STARTED");
    const completion = nextEvent(task, "TASK_COMPLETED", "EVT-DEMO-DUPLICATE");
    applyEvent(task, "TASK_COMPLETED", completion);
    applyEvent(task, "TASK_COMPLETED", completion);
    showView("inventory-view");
    status("Duplicate event replayed: one accepted event and one inventory movement remain; the replay caused no mutation.", "success");
  }
}

for (const button of navButtons) button.addEventListener("click", () => showView(button.dataset.view));
for (const button of document.querySelectorAll("[data-scenario]")) button.addEventListener("click", () => runScenario(button.dataset.scenario));

byId("receipt-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  receive({
    palletId: String(data.get("palletId")).trim(),
    receiptBarcode: String(data.get("receiptBarcode")).trim(),
    skuId: String(data.get("skuId")),
    lotCode: String(data.get("lotCode")).trim(),
    quantity: Number(data.get("quantity")),
  });
});

byId("assign-location").addEventListener("click", () => assign(byId("pallet-id").value.trim()));
byId("dispatch-task").addEventListener("click", () => {
  const task = selectedTask();
  if (!task) return status("Create and select a movement task first.", "error");
  dispatch(task.id);
});
byId("send-event").addEventListener("click", () => {
  const task = selectedTask();
  if (!task) return status("Create and select a movement task first.", "error");
  applyEvent(task, byId("event-type").value);
});
byId("retry-task").addEventListener("click", () => {
  const task = selectedTask();
  if (!task) return status("Create and select a movement task first.", "error");
  const result = warehouse.retryTask(task.id);
  explain(result, `${task.id} retry command accepted.`);
  render();
});
byId("cancel-task").addEventListener("click", () => {
  const task = selectedTask();
  if (!task) return status("Create and select a movement task first.", "error");
  const result = warehouse.cancelTask(task.id);
  explain(result, `${task.id} cancelled.`);
  render();
});
byId("reset-demo").addEventListener("click", () => {
  reset();
  showView("inbound-view");
  status("Demo reset. All synthetic in-memory records were cleared.");
});

render();

const requestedScenario = new URLSearchParams(window.location.search).get("scenario");
if (["happy", "offline", "duplicate"].includes(requestedScenario)) runScenario(requestedScenario);
