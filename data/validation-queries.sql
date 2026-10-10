-- Standalone, read-only SQLite controls for the synthetic portfolio contract.
-- Rate values are fractions in [0, 1]. Empty denominators and empty completed
-- cohorts deliberately return SQL NULL; the later read model displays N/A.

-- CONTROL: CTRL_01_DUPLICATE_PALLET_IDS
SELECT pallet_id, COUNT(*) AS row_count
FROM pallet
GROUP BY pallet_id
HAVING COUNT(*) > 1;

-- CONTROL: CTRL_02_INVALID_LOCATION_COUNTS
SELECT location_id, pallet_capacity, used_pallet_count
FROM location
WHERE typeof(pallet_capacity) <> 'integer'
   OR pallet_capacity <= 0
   OR typeof(used_pallet_count) <> 'integer'
   OR used_pallet_count < 0
   OR used_pallet_count > pallet_capacity;

-- CONTROL: CTRL_03_INVALID_TASK_STATES
SELECT task_id, state
FROM movement_task
WHERE state NOT IN (
    'CREATED', 'VALIDATED', 'DISPATCHED', 'IN_PROGRESS',
    'COMPLETED', 'FAILED', 'TIMED_OUT', 'CANCELLED'
);

-- CONTROL: CTRL_04_COMPLETED_TASK_INVENTORY_COUNT
SELECT task.task_id, COUNT(movement.movement_id) AS movement_count
FROM movement_task AS task
LEFT JOIN inventory_movement AS movement ON movement.task_id = task.task_id
WHERE task.state = 'COMPLETED'
GROUP BY task.task_id
HAVING COUNT(movement.movement_id) <> 1;

-- CONTROL: CTRL_05_DUPLICATE_EVENT_IDS
SELECT event_id, COUNT(*) AS row_count
FROM wcs_event
GROUP BY event_id
HAVING COUNT(*) > 1;

-- CONTROL: CTRL_06_OPEN_EXCEPTION_COUNTS
SELECT exception_type, status, COUNT(*) AS exception_count
FROM exception_case
WHERE status = 'open'
GROUP BY exception_type, status
ORDER BY exception_type, status;

-- CONTROL: METRIC_01_COMPLETION_RATE
SELECT
    'Completion Rate' AS metric_name,
    COALESCE(SUM(CASE WHEN state = 'COMPLETED' THEN 1 ELSE 0 END), 0) AS numerator,
    COUNT(*) AS denominator,
    CASE
        WHEN COUNT(*) = 0 THEN NULL
        ELSE SUM(CASE WHEN state = 'COMPLETED' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
    END AS metric_value
FROM movement_task
WHERE dispatched_at IS NOT NULL;

-- CONTROL: METRIC_02_EXCEPTION_RATE
SELECT
    'Exception Rate' AS metric_name,
    COALESCE(SUM(CASE WHEN failure_count > 0 THEN 1 ELSE 0 END), 0) AS numerator,
    COUNT(*) AS denominator,
    CASE
        WHEN COUNT(*) = 0 THEN NULL
        ELSE SUM(CASE WHEN failure_count > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
    END AS metric_value
FROM movement_task
WHERE dispatched_at IS NOT NULL;

-- CONTROL: METRIC_03_FIRST_PASS_SUCCESS_RATE
SELECT
    'First Pass Success Rate' AS metric_name,
    COALESCE(SUM(CASE WHEN state = 'COMPLETED' AND retry_count = 0 THEN 1 ELSE 0 END), 0) AS numerator,
    COUNT(*) AS denominator,
    CASE
        WHEN COUNT(*) = 0 THEN NULL
        ELSE SUM(CASE WHEN state = 'COMPLETED' AND retry_count = 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
    END AS metric_value
FROM movement_task
WHERE dispatched_at IS NOT NULL;

-- CONTROL: METRIC_04_AVERAGE_SIMULATED_CYCLE_TIME
SELECT
    'Average Simulated Cycle Time' AS metric_name,
    COUNT(*) AS completed_task_count,
    AVG(strftime('%s', completed_at) - strftime('%s', dispatched_at)) AS metric_value_seconds
FROM movement_task
WHERE dispatched_at IS NOT NULL
  AND state = 'COMPLETED'
  AND completed_at IS NOT NULL;
