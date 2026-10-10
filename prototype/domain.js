const ALLOWED_CANCELLATION_STATES = new Set([
  "CREATED", "VALIDATED", "DISPATCHED", "IN_PROGRESS", "FAILED", "TIMED_OUT",
]);

const EVENT_TRANSITIONS = {
  TASK_STARTED: { from: new Set(["DISPATCHED"]), to: "IN_PROGRESS" },
  TASK_COMPLETED: { from: new Set(["DISPATCHED", "IN_PROGRESS"]), to: "COMPLETED" },
  TASK_FAILED: { from: new Set(["DISPATCHED", "IN_PROGRESS"]), to: "FAILED" },
  TASK_TIMEOUT: { from: new Set(["DISPATCHED", "IN_PROGRESS"]), to: "TIMED_OUT" },
};

const clone = (value) => structuredClone(value);
const success = (value) => ({ ok: true, value: clone(value) });
const failure = (code, message, value) => ({
  ok: false,
  error: { code, message },
  ...(value === undefined ? {} : { value: clone(value) }),
});

function wholeSecondUtc(value) {
  return typeof value === "string"
    && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value)
    && !Number.isNaN(Date.parse(value));
}

export function createWarehouse(initialState) {
  return new WarehouseStore(initialState);
}

class WarehouseStore {
  constructor(initialState) {
    this.state = clone(initialState);
    for (const key of ["pallets", "tasks", "commands", "events", "inventoryMovements", "exceptions", "audit"]) {
      this.state[key] ??= [];
    }
    this.clockMs = Date.parse(this.state.clockStart ?? "2026-01-01T00:00:00Z");
    this.clockStepMs = (this.state.clockStepSeconds ?? 10) * 1000;
    this.counters = {
      task: this.state.tasks.length,
      command: this.state.commands.length,
      movement: this.state.inventoryMovements.length,
      exception: this.state.exceptions.length,
      audit: this.state.audit.length,
    };
    this.state.tasks = this.state.tasks.map((task) => ({
      palletId: null,
      destinationLocationId: null,
      deviceId: this.state.defaultDeviceId,
      correlationId: `CORR-${task.id}`,
      retryCount: 0,
      failureCount: 0,
      createdAt: null,
      validatedAt: null,
      dispatchedAt: null,
      completedAt: null,
      stateHistory: [],
      ...task,
    }));
  }

  _now() {
    const value = new Date(this.clockMs).toISOString().replace(".000Z", "Z");
    this.clockMs += this.clockStepMs;
    return value;
  }

  _id(kind, prefix) {
    this.counters[kind] += 1;
    return `${prefix}-${String(this.counters[kind]).padStart(3, "0")}`;
  }

  _audit({ action, actor = "WMS", entityId = null, correlationId = null, priorState = null, newState = null, details = null, timestamp = null }) {
    const entry = {
      id: this._id("audit", "AUD-DEMO"),
      action,
      actor,
      entityId,
      correlationId,
      priorState,
      newState,
      details,
      timestamp: timestamp ?? this._now(),
    };
    this.state.audit.push(entry);
    return entry;
  }

  _transition(task, newState, action, timestamp = null) {
    const priorState = task.state;
    task.state = newState;
    const at = timestamp ?? this._now();
    task.stateHistory ??= [];
    task.stateHistory.push({ state: newState, at });
    this._audit({
      action,
      entityId: task.id,
      correlationId: task.correlationId,
      priorState,
      newState,
      timestamp: at,
    });
  }

  _createException({ type, reason, task = null, palletId = null, status = "open" }) {
    const timestamp = this._now();
    const item = {
      id: this._id("exception", "EXC-DEMO"),
      taskId: task?.id ?? null,
      palletId: palletId ?? task?.palletId ?? null,
      type,
      status,
      reason,
      failureCount: task?.failureCount ?? 0,
      retryCount: task?.retryCount ?? 0,
      openedAt: timestamp,
      updatedAt: timestamp,
    };
    this.state.exceptions.push(item);
    this._audit({
      action: "EXCEPTION_OPENED",
      entityId: item.id,
      correlationId: task?.correlationId ?? null,
      details: type,
      timestamp,
    });
    return item;
  }

  _activeException(taskId) {
    return [...this.state.exceptions].reverse().find(
      (item) => item.taskId === taskId && item.status === "open",
    ) ?? null;
  }

  _updateException(item, task, status = item.status) {
    if (!item) return null;
    item.status = status;
    item.failureCount = task.failureCount;
    item.retryCount = task.retryCount;
    item.updatedAt = this._now();
    this._audit({
      action: status === "escalated" ? "EXCEPTION_ESCALATED" : "EXCEPTION_UPDATED",
      entityId: item.id,
      correlationId: task.correlationId,
      details: `${item.type}:${status}`,
      timestamp: item.updatedAt,
    });
    return item;
  }

  receivePallet(input) {
    const palletId = String(input?.palletId ?? "").trim();
    const receiptBarcode = String(input?.receiptBarcode ?? "").trim();
    const skuId = String(input?.skuId ?? "").trim();
    const lotCode = String(input?.lotCode ?? "").trim();
    const quantity = input?.quantity;

    if (!/^[A-Z0-9-]+$/.test(receiptBarcode)) {
      this._createException({ type: "INVALID_BARCODE", reason: "Barcode must use uppercase letters, numbers, or hyphens.", palletId: palletId || null });
      return failure("INVALID_BARCODE", "Barcode is blank or malformed.");
    }
    const sku = this.state.skus.find((item) => item.id === skuId && item.active === true);
    if (!sku) {
      this._createException({ type: "UNKNOWN_OR_INACTIVE_SKU", reason: "SKU is unknown or inactive.", palletId: palletId || null });
      return failure("UNKNOWN_OR_INACTIVE_SKU", "SKU is unknown or inactive.");
    }
    if (!Number.isInteger(quantity) || quantity <= 0) {
      this._createException({ type: "INVALID_QUANTITY", reason: "Quantity must be a positive integer.", palletId: palletId || null });
      return failure("INVALID_QUANTITY", "Quantity must be a positive integer.");
    }
    if (!palletId || !lotCode) {
      this._createException({ type: "INVALID_BARCODE", reason: "Pallet and lot identities are required.", palletId: palletId || null });
      return failure("INVALID_BARCODE", "Pallet ID and lot code are required.");
    }
    if (this.state.pallets.some((item) => item.id === palletId)) {
      this._createException({ type: "DUPLICATE_PALLET", reason: "Pallet identity already exists.", palletId });
      return failure("DUPLICATE_PALLET", "Pallet identity already exists.");
    }

    const receivedAt = this._now();
    const pallet = {
      id: palletId,
      receiptBarcode,
      skuId,
      lotCode,
      quantity,
      receivedAt,
      currentLocationId: null,
    };
    this.state.pallets.push(pallet);
    this._audit({ action: "PALLET_RECEIVED", actor: "Inbound operator", entityId: pallet.id, timestamp: receivedAt });
    return success({ pallet });
  }

  assignLocation(palletId) {
    const pallet = this.state.pallets.find((item) => item.id === palletId);
    if (!pallet) return failure("UNKNOWN_TASK", "Pallet is not available for assignment.");
    if (this.state.tasks.some((item) => item.palletId === palletId)) {
      return failure("INVALID_TRANSITION", "A movement task already exists for this pallet.");
    }
    const sku = this.state.skus.find((item) => item.id === pallet.skuId);
    const location = this.state.locations
      .filter((item) => item.compatibilityKey === sku.compatibilityKey && item.used < item.capacity)
      .sort((left, right) => left.zonePriority - right.zonePriority || left.code.localeCompare(right.code))[0];
    if (!location) {
      const exception = this._createException({
        type: "NO_AVAILABLE_LOCATION",
        reason: "No compatible location remains below capacity.",
        palletId,
      });
      return failure("NO_AVAILABLE_LOCATION", "No compatible location is available.", { exception });
    }

    const createdAt = this._now();
    const taskNumber = this.counters.task + 1;
    const task = {
      id: this._id("task", "TASK-DEMO"),
      palletId,
      destinationLocationId: location.id,
      deviceId: this.state.defaultDeviceId,
      state: "CREATED",
      retryCount: 0,
      failureCount: 0,
      correlationId: `CORR-DEMO-${String(taskNumber).padStart(3, "0")}`,
      createdAt,
      validatedAt: null,
      dispatchedAt: null,
      completedAt: null,
      stateHistory: [{ state: "CREATED", at: createdAt }],
    };
    this.state.tasks.push(task);
    this._audit({ action: "TASK_CREATED", entityId: task.id, correlationId: task.correlationId, newState: "CREATED", timestamp: createdAt });
    const validatedAt = this._now();
    task.validatedAt = validatedAt;
    this._transition(task, "VALIDATED", "TASK_VALIDATED", validatedAt);
    return success({ pallet, location, task });
  }

  _createCommand(task) {
    const sentAt = this._now();
    const command = {
      id: this._id("command", "CMD-DEMO"),
      taskId: task.id,
      deviceId: task.deviceId,
      attemptNumber: task.retryCount,
      status: "SENT",
      correlationId: task.correlationId,
      sentAt,
    };
    this.state.commands.push(command);
    this._audit({ action: "COMMAND_SENT", actor: "WMS", entityId: command.id, correlationId: task.correlationId, details: task.id, timestamp: sentAt });
    return command;
  }

  dispatchTask(taskId) {
    const task = this.state.tasks.find((item) => item.id === taskId);
    if (!task) return failure("UNKNOWN_TASK", "Movement task was not found.");
    if (task.state !== "VALIDATED") return failure("INVALID_TRANSITION", "Only a validated task can be dispatched.");
    const device = this.state.devices.find((item) => item.id === task.deviceId);
    if (!device || device.status !== "online") {
      task.failureCount += 1;
      this._transition(task, "FAILED", "DEVICE_OFFLINE");
      const exception = this._createException({ type: "DEVICE_OFFLINE", reason: "The simulated device is offline.", task });
      return failure("DEVICE_OFFLINE", "The simulated device is offline.", { task, exception, commandCreated: false });
    }
    const command = this._createCommand(task);
    const dispatchedAt = this._now();
    task.dispatchedAt ??= dispatchedAt;
    this._transition(task, "DISPATCHED", "TASK_DISPATCHED", dispatchedAt);
    return success({ task, command });
  }

  applyWcsEvent(event) {
    if (this.state.events.some((item) => item.eventId === event?.eventId)) {
      return success({
        eventId: event.eventId,
        taskId: event.taskId,
        duplicate: true,
        stateMutated: false,
        inventoryMutated: false,
      });
    }
    const task = this.state.tasks.find((item) => item.id === event?.taskId);
    if (!task) {
      this._audit({ action: "UNKNOWN_EVENT_TASK", actor: "WMS event intake", entityId: event?.eventId ?? null, details: event?.taskId ?? null });
      return failure("UNKNOWN_TASK", "The event could not be correlated to a movement task.");
    }
    const transition = EVENT_TRANSITIONS[event?.eventType];
    const wellFormed = event?.simulated === true
      && typeof event?.eventId === "string" && event.eventId.length > 0
      && event?.deviceId === task.deviceId
      && event?.correlationId === task.correlationId
      && wholeSecondUtc(event?.eventAt);
    if (!wellFormed || !transition || !transition.from.has(task.state)) {
      this._audit({ action: "EVENT_REJECTED", actor: "WMS event intake", entityId: event?.eventId ?? null, correlationId: task.correlationId, priorState: task.state, details: event?.eventType ?? null });
      return failure("INVALID_TRANSITION", "The event is malformed, uncorrelated, or invalid for the current state.");
    }

    const eventRecord = clone(event);
    this.state.events.push(eventRecord);
    this._audit({ action: "EVENT_ACCEPTED", actor: "WMS event intake", entityId: event.eventId, correlationId: task.correlationId, priorState: task.state, newState: transition.to, timestamp: event.eventAt });
    this._transition(task, transition.to, event.eventType, event.eventAt);

    let inventoryMutated = false;
    let exception = null;
    if (event.eventType === "TASK_COMPLETED") {
      task.completedAt = event.eventAt;
      if (!this.state.inventoryMovements.some((item) => item.taskId === task.id)) {
        const pallet = this.state.pallets.find((item) => item.id === task.palletId);
        const location = this.state.locations.find((item) => item.id === task.destinationLocationId);
        const movement = {
          id: this._id("movement", "MOV-DEMO"),
          taskId: task.id,
          palletId: task.palletId,
          fromLocationId: pallet.currentLocationId,
          toLocationId: task.destinationLocationId,
          sourceEventId: event.eventId,
          committedAt: event.eventAt,
        };
        pallet.currentLocationId = task.destinationLocationId;
        location.used += 1;
        this.state.inventoryMovements.push(movement);
        this._audit({ action: "INVENTORY_COMMITTED", entityId: movement.id, correlationId: task.correlationId, details: task.destinationLocationId, timestamp: event.eventAt });
        inventoryMutated = true;
      }
      const active = this._activeException(task.id);
      if (active) this._updateException(active, task, "resolved");
    } else if (event.eventType === "TASK_FAILED" || event.eventType === "TASK_TIMEOUT") {
      task.failureCount += 1;
      const type = event.eventType === "TASK_TIMEOUT" ? "TASK_TIMEOUT" : (event.reasonCode === "PALLET_JAM" ? "PALLET_JAM" : "PALLET_JAM");
      exception = this._activeException(task.id) ?? this._createException({ type, reason: type === "PALLET_JAM" ? "A simulated pallet jam was reported." : "The simulated task timed out.", task });
      if (task.failureCount >= 3) this._updateException(exception, task, "escalated");
      else this._updateException(exception, task, "open");
    }

    return success({ event: eventRecord, task, exception, duplicate: false, stateMutated: true, inventoryMutated });
  }

  retryTask(taskId) {
    const task = this.state.tasks.find((item) => item.id === taskId);
    if (!task) return failure("UNKNOWN_TASK", "Movement task was not found.");
    if (!["FAILED", "TIMED_OUT"].includes(task.state)) return failure("INVALID_TRANSITION", "Retry is allowed only from FAILED or TIMED_OUT.");
    let exception = this._activeException(task.id);
    if (task.retryCount >= 2 || task.failureCount >= 3 || !exception) {
      if (exception) exception = this._updateException(exception, task, "escalated");
      return failure("RETRY_LIMIT_REACHED", "No third retry command is allowed.", { task, exception, thirdRetryCommandCreated: false });
    }

    task.retryCount += 1;
    this._transition(task, "DISPATCHED", "TASK_RETRY_REQUESTED");
    const device = this.state.devices.find((item) => item.id === task.deviceId);
    if (!device || device.status !== "online") {
      task.failureCount += 1;
      this._transition(task, "FAILED", "DEVICE_OFFLINE");
      const escalated = task.failureCount >= 3;
      exception = this._updateException(exception, task, escalated ? "escalated" : "open");
      const code = escalated ? "RETRY_LIMIT_REACHED" : "DEVICE_OFFLINE";
      const message = escalated ? "The third failure escalated the exception; no third retry is allowed." : "The simulated device remains offline.";
      return failure(code, message, { task, exception, commandCreated: false });
    }

    const command = this._createCommand(task);
    return success({ task, command });
  }

  cancelTask(taskId) {
    const task = this.state.tasks.find((item) => item.id === taskId);
    if (!task) return failure("UNKNOWN_TASK", "Movement task was not found.");
    if (!ALLOWED_CANCELLATION_STATES.has(task.state)) {
      return failure("CANCELLATION_NOT_ALLOWED", "Cancellation is not allowed from the current state.");
    }
    this._transition(task, "CANCELLED", "TASK_CANCELLED");
    const exception = this._activeException(task.id);
    if (exception) this._updateException(exception, task, "cancelled");
    return success({ task });
  }

  setDeviceStatus(deviceId, status) {
    const device = this.state.devices.find((item) => item.id === deviceId);
    if (!device || !["online", "offline"].includes(status)) return failure("INVALID_TRANSITION", "Device or status is invalid.");
    device.status = status;
    this._audit({ action: "DEVICE_STATUS_CHANGED", actor: "WCS simulator", entityId: deviceId, details: status });
    return success({ device });
  }

  getMetrics() {
    const cohort = this.state.tasks.filter((task) => task.dispatchedAt !== null && task.dispatchedAt !== undefined);
    const dispatchedCount = cohort.length;
    if (dispatchedCount === 0) {
      return {
        dispatchedCount: 0,
        completionRate: null,
        exceptionRate: null,
        firstPassSuccessRate: null,
        averageSimulatedCycleTimeSeconds: null,
      };
    }
    const completed = cohort.filter((task) => task.state === "COMPLETED");
    const cycleTimes = completed
      .filter((task) => task.completedAt)
      .map((task) => (Date.parse(task.completedAt) - Date.parse(task.dispatchedAt)) / 1000);
    return {
      dispatchedCount,
      completionRate: completed.length / dispatchedCount,
      exceptionRate: cohort.filter((task) => task.failureCount > 0).length / dispatchedCount,
      firstPassSuccessRate: completed.filter((task) => task.retryCount === 0).length / dispatchedCount,
      averageSimulatedCycleTimeSeconds: cycleTimes.length
        ? cycleTimes.reduce((sum, value) => sum + value, 0) / cycleTimes.length
        : null,
    };
  }

  getAuditTrail() {
    return clone([...this.state.audit].sort((left, right) => left.timestamp.localeCompare(right.timestamp)));
  }

  getSnapshot() {
    return clone({
      pallets: this.state.pallets,
      tasks: this.state.tasks,
      commands: this.state.commands,
      events: this.state.events,
      inventoryMovements: this.state.inventoryMovements,
      exceptions: this.state.exceptions,
      activeExceptions: this.state.exceptions.filter((item) => item.status === "open"),
      devices: this.state.devices,
      locations: this.state.locations,
      metrics: this.getMetrics(),
    });
  }
}
