-- Portfolio decision: a local SQLite contract for a synthetic simulator only.
-- This is not a production schema and is not connected to a real WMS or WCS.
PRAGMA foreign_keys = ON;

CREATE TABLE sku (
    sku_id TEXT PRIMARY KEY NOT NULL,
    barcode TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    is_active INTEGER NOT NULL CHECK (typeof(is_active) = 'integer' AND is_active IN (0, 1)),
    compatibility_key TEXT NOT NULL
);

CREATE TABLE location (
    location_id TEXT PRIMARY KEY NOT NULL,
    location_code TEXT NOT NULL UNIQUE,
    zone_code TEXT NOT NULL,
    zone_priority INTEGER NOT NULL CHECK (typeof(zone_priority) = 'integer' AND zone_priority >= 0),
    compatibility_key TEXT NOT NULL,
    pallet_capacity INTEGER NOT NULL CHECK (typeof(pallet_capacity) = 'integer' AND pallet_capacity > 0),
    used_pallet_count INTEGER NOT NULL DEFAULT 0 CHECK (
        typeof(used_pallet_count) = 'integer'
        AND used_pallet_count >= 0
        AND used_pallet_count <= pallet_capacity
    )
);

CREATE TABLE device (
    device_id TEXT PRIMARY KEY NOT NULL,
    device_name TEXT NOT NULL,
    device_type TEXT NOT NULL CHECK (device_type IN ('conveyor', 'lift', 'robot')),
    status TEXT NOT NULL CHECK (status IN ('online', 'offline'))
);

CREATE TABLE pallet (
    pallet_id TEXT PRIMARY KEY NOT NULL,
    receipt_barcode TEXT NOT NULL,
    sku_id TEXT NOT NULL REFERENCES sku(sku_id),
    lot_code TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (typeof(quantity) = 'integer' AND quantity > 0),
    received_at TEXT NOT NULL CHECK (received_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(received_at) IS NOT NULL),
    current_location_id TEXT REFERENCES location(location_id)
);

CREATE TABLE movement_task (
    task_id TEXT PRIMARY KEY NOT NULL,
    pallet_id TEXT NOT NULL UNIQUE REFERENCES pallet(pallet_id),
    destination_location_id TEXT NOT NULL REFERENCES location(location_id),
    device_id TEXT NOT NULL REFERENCES device(device_id),
    state TEXT NOT NULL CHECK (state IN (
        'CREATED', 'VALIDATED', 'DISPATCHED', 'IN_PROGRESS',
        'COMPLETED', 'FAILED', 'TIMED_OUT', 'CANCELLED'
    )),
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (typeof(retry_count) = 'integer' AND retry_count BETWEEN 0 AND 2),
    failure_count INTEGER NOT NULL DEFAULT 0 CHECK (typeof(failure_count) = 'integer' AND failure_count BETWEEN 0 AND 3),
    correlation_id TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (created_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(created_at) IS NOT NULL),
    validated_at TEXT CHECK (validated_at IS NULL OR (validated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(validated_at) IS NOT NULL)),
    dispatched_at TEXT CHECK (dispatched_at IS NULL OR (dispatched_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(dispatched_at) IS NOT NULL)),
    completed_at TEXT CHECK (completed_at IS NULL OR (completed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(completed_at) IS NOT NULL))
);

CREATE TABLE device_command (
    command_id TEXT PRIMARY KEY NOT NULL,
    task_id TEXT NOT NULL REFERENCES movement_task(task_id),
    device_id TEXT NOT NULL REFERENCES device(device_id),
    attempt_number INTEGER NOT NULL CHECK (typeof(attempt_number) = 'integer' AND attempt_number BETWEEN 0 AND 2),
    command_status TEXT NOT NULL CHECK (command_status IN ('CREATED', 'SENT', 'ACCEPTED', 'FAILED', 'TIMED_OUT', 'CANCELLED')),
    correlation_id TEXT NOT NULL,
    sent_at TEXT NOT NULL CHECK (sent_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(sent_at) IS NOT NULL),
    UNIQUE (task_id, attempt_number)
);

CREATE TABLE wcs_event (
    event_id TEXT PRIMARY KEY NOT NULL,
    task_id TEXT NOT NULL REFERENCES movement_task(task_id),
    device_id TEXT NOT NULL REFERENCES device(device_id),
    event_type TEXT NOT NULL CHECK (event_type IN ('TASK_STARTED', 'TASK_COMPLETED', 'TASK_FAILED', 'TASK_TIMEOUT')),
    correlation_id TEXT NOT NULL,
    event_at TEXT NOT NULL CHECK (event_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(event_at) IS NOT NULL),
    simulated INTEGER NOT NULL DEFAULT 1 CHECK (typeof(simulated) = 'integer' AND simulated = 1),
    payload_json TEXT
);

CREATE TABLE inventory_movement (
    movement_id TEXT PRIMARY KEY NOT NULL,
    task_id TEXT NOT NULL UNIQUE REFERENCES movement_task(task_id),
    pallet_id TEXT NOT NULL REFERENCES pallet(pallet_id),
    from_location_id TEXT REFERENCES location(location_id),
    to_location_id TEXT NOT NULL REFERENCES location(location_id),
    source_event_id TEXT NOT NULL UNIQUE REFERENCES wcs_event(event_id),
    committed_at TEXT NOT NULL CHECK (committed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(committed_at) IS NOT NULL)
);

CREATE TABLE exception_case (
    exception_id TEXT PRIMARY KEY NOT NULL,
    task_id TEXT REFERENCES movement_task(task_id),
    pallet_id TEXT REFERENCES pallet(pallet_id),
    exception_type TEXT NOT NULL CHECK (exception_type IN (
        'INVALID_BARCODE', 'UNKNOWN_OR_INACTIVE_SKU', 'INVALID_QUANTITY',
        'DUPLICATE_PALLET', 'NO_AVAILABLE_LOCATION', 'DEVICE_OFFLINE',
        'PALLET_JAM', 'TASK_TIMEOUT', 'INVALID_TRANSITION', 'UNKNOWN_TASK',
        'DUPLICATE_EVENT', 'RETRY_LIMIT_REACHED', 'CANCELLATION_NOT_ALLOWED'
    )),
    status TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'escalated', 'cancelled')),
    failure_count INTEGER NOT NULL DEFAULT 0 CHECK (typeof(failure_count) = 'integer' AND failure_count BETWEEN 0 AND 3),
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (typeof(retry_count) = 'integer' AND retry_count BETWEEN 0 AND 2),
    reason TEXT NOT NULL,
    opened_at TEXT NOT NULL CHECK (opened_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(opened_at) IS NOT NULL),
    updated_at TEXT NOT NULL CHECK (updated_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(updated_at) IS NOT NULL),
    resolved_at TEXT CHECK (resolved_at IS NULL OR (resolved_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND datetime(resolved_at) IS NOT NULL))
);

CREATE TRIGGER inventory_movement_requires_completed_task
BEFORE INSERT ON inventory_movement
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1
    FROM movement_task AS task
    WHERE task.task_id = NEW.task_id
      AND task.pallet_id = NEW.pallet_id
      AND task.destination_location_id = NEW.to_location_id
      AND task.state = 'COMPLETED'
)
BEGIN
    SELECT RAISE(ABORT, 'inventory movement requires matching COMPLETED task');
END;

CREATE TRIGGER inventory_movement_requires_completion_event
BEFORE INSERT ON inventory_movement
FOR EACH ROW
WHEN NOT EXISTS (
    SELECT 1
    FROM wcs_event AS event
    WHERE event.event_id = NEW.source_event_id
      AND event.task_id = NEW.task_id
      AND event.event_type = 'TASK_COMPLETED'
)
BEGIN
    SELECT RAISE(ABORT, 'inventory movement requires matching TASK_COMPLETED event');
END;
