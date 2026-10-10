import re
import sqlite3
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
SCHEMA = DATA_DIR / "schema.sql"
SEED = DATA_DIR / "synthetic-seed.sql"
CONTROLS = DATA_DIR / "validation-queries.sql"
DICTIONARY = DATA_DIR / "data-dictionary.md"

STATES = (
    "CREATED", "VALIDATED", "DISPATCHED", "IN_PROGRESS",
    "COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED",
)
EVENT_TYPES = ("TASK_STARTED", "TASK_COMPLETED", "TASK_FAILED", "TASK_TIMEOUT")
ERROR_CODES = (
    "INVALID_BARCODE", "UNKNOWN_OR_INACTIVE_SKU", "INVALID_QUANTITY",
    "DUPLICATE_PALLET", "NO_AVAILABLE_LOCATION", "DEVICE_OFFLINE", "PALLET_JAM",
    "TASK_TIMEOUT", "INVALID_TRANSITION", "UNKNOWN_TASK", "DUPLICATE_EVENT",
    "RETRY_LIMIT_REACHED", "CANCELLATION_NOT_ALLOWED",
)

EXPECTED_COLUMNS = {
    "sku": ("sku_id", "barcode", "name", "description", "is_active", "compatibility_key"),
    "location": (
        "location_id", "location_code", "zone_code", "zone_priority",
        "compatibility_key", "pallet_capacity", "used_pallet_count",
    ),
    "device": ("device_id", "device_name", "device_type", "status"),
    "pallet": (
        "pallet_id", "receipt_barcode", "sku_id", "lot_code", "quantity",
        "received_at", "current_location_id",
    ),
    "movement_task": (
        "task_id", "pallet_id", "destination_location_id", "device_id", "state",
        "retry_count", "failure_count", "correlation_id", "created_at", "validated_at",
        "dispatched_at", "completed_at",
    ),
    "device_command": (
        "command_id", "task_id", "device_id", "attempt_number", "command_status",
        "correlation_id", "sent_at",
    ),
    "wcs_event": (
        "event_id", "task_id", "device_id", "event_type", "correlation_id",
        "event_at", "simulated", "payload_json",
    ),
    "inventory_movement": (
        "movement_id", "task_id", "pallet_id", "from_location_id", "to_location_id",
        "source_event_id", "committed_at",
    ),
    "exception_case": (
        "exception_id", "task_id", "pallet_id", "exception_type", "status",
        "failure_count", "retry_count", "reason", "opened_at", "updated_at", "resolved_at",
    ),
}

CONTROL_IDS = (
    "CTRL_01_DUPLICATE_PALLET_IDS",
    "CTRL_02_INVALID_LOCATION_COUNTS",
    "CTRL_03_INVALID_TASK_STATES",
    "CTRL_04_COMPLETED_TASK_INVENTORY_COUNT",
    "CTRL_05_DUPLICATE_EVENT_IDS",
    "CTRL_06_OPEN_EXCEPTION_COUNTS",
    "METRIC_01_COMPLETION_RATE",
    "METRIC_02_EXCEPTION_RATE",
    "METRIC_03_FIRST_PASS_SUCCESS_RATE",
    "METRIC_04_AVERAGE_SIMULATED_CYCLE_TIME",
)


def _database(schema_text=None, *, seed=True):
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(schema_text if schema_text is not None else SCHEMA.read_text(encoding="utf-8"))
    if seed:
        connection.executescript(SEED.read_text(encoding="utf-8"))
    return connection


def _insert_pallet_and_task(
    connection,
    suffix,
    *,
    state="VALIDATED",
    retry_count=0,
    failure_count=0,
    dispatched_at=None,
    completed_at=None,
):
    pallet_id = f"PLT-SYN-{suffix}"
    task_id = f"TASK-SYN-{suffix}"
    correlation_id = f"CORR-SYN-{suffix}"
    connection.execute(
        "INSERT INTO pallet VALUES (?, ?, 'SKU-DEMO-A', ?, 10, '2026-01-01T00:00:00Z', NULL)",
        (pallet_id, f"RCPT{str(suffix).zfill(6)}", f"LOT-{suffix}"),
    )
    connection.execute(
        """
        INSERT INTO movement_task (
            task_id, pallet_id, destination_location_id, device_id, state,
            retry_count, failure_count, correlation_id, created_at, validated_at,
            dispatched_at, completed_at
        ) VALUES (?, ?, 'LOC-DEMO-A01', 'DEV-DEMO-CONV', ?, ?, ?, ?,
                  '2026-01-01T00:00:00Z', '2026-01-01T00:00:10Z', ?, ?)
        """,
        (task_id, pallet_id, state, retry_count, failure_count, correlation_id, dispatched_at, completed_at),
    )
    return pallet_id, task_id, correlation_id


def _unique_columns(connection, table):
    unique = set()
    pk = tuple(
        row[1]
        for row in sorted(connection.execute(f"PRAGMA table_info({table})"), key=lambda row: row[5])
        if row[5]
    )
    if pk:
        unique.add(pk)
    for row in connection.execute(f"PRAGMA index_list({table})"):
        if row[2]:
            unique.add(tuple(item[2] for item in connection.execute(f"PRAGMA index_info({row[1]})")))
    return unique


def _assert_public_schema_contract(schema_text):
    connection = _database(schema_text, seed=False)
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    assert tables == set(EXPECTED_COLUMNS)
    for table, expected in EXPECTED_COLUMNS.items():
        table_info = list(connection.execute(f"PRAGMA table_info({table})"))
        assert tuple(row[1] for row in table_info) == expected
        primary_key_rows = [row for row in table_info if row[5] > 0]
        assert len(primary_key_rows) == 1
        assert primary_key_rows[0][3] == 1, f"{table} primary key must be explicitly NOT NULL"
    assert ("event_id",) in _unique_columns(connection, "wcs_event")
    assert ("task_id",) in _unique_columns(connection, "inventory_movement")
    assert ("source_event_id",) in _unique_columns(connection, "inventory_movement")
    task_sql = schema_text[
        schema_text.index("CREATE TABLE movement_task"):schema_text.index("CREATE TABLE device_command")
    ]
    state_check = re.search(
        r"state\s+TEXT\s+NOT\s+NULL\s+CHECK\s*\(state\s+IN\s*\((.*?)\)\s*\)",
        task_sql,
        re.DOTALL | re.IGNORECASE,
    )
    assert state_check
    assert tuple(re.findall(r"'([^']+)'", state_check.group(1))) == STATES


def _assert_precompletion_insert_blocked(schema_text):
    connection = _database(schema_text)
    pallet_id, task_id, correlation_id = _insert_pallet_and_task(
        connection, "998", state="DISPATCHED", dispatched_at="2026-01-01T00:00:20Z"
    )
    connection.execute(
        "INSERT INTO wcs_event VALUES ('EVT-MUT-998', ?, 'DEV-DEMO-CONV', 'TASK_COMPLETED', ?, '2026-01-01T00:01:00Z', 1, '{}')",
        (task_id, correlation_id),
    )
    blocked = False
    try:
        connection.execute(
            "INSERT INTO inventory_movement VALUES ('MOV-MUT-998', ?, ?, NULL, 'LOC-DEMO-A01', 'EVT-MUT-998', '2026-01-01T00:01:00Z')",
            (task_id, pallet_id),
        )
    except sqlite3.IntegrityError:
        blocked = True
    assert blocked, "inventory insert before task completion was not blocked"


def _assert_noncompletion_source_blocked(schema_text):
    connection = _database(schema_text)
    pallet_id, task_id, correlation_id = _insert_pallet_and_task(
        connection,
        "997",
        state="COMPLETED",
        dispatched_at="2026-01-01T00:00:20Z",
        completed_at="2026-01-01T00:01:00Z",
    )
    connection.execute(
        "INSERT INTO wcs_event VALUES ('EVT-MUT-997', ?, 'DEV-DEMO-CONV', 'TASK_FAILED', ?, '2026-01-01T00:01:00Z', 1, '{}')",
        (task_id, correlation_id),
    )
    blocked = False
    try:
        connection.execute(
            "INSERT INTO inventory_movement VALUES ('MOV-MUT-997', ?, ?, NULL, 'LOC-DEMO-A01', 'EVT-MUT-997', '2026-01-01T00:01:00Z')",
            (task_id, pallet_id),
        )
    except sqlite3.IntegrityError:
        blocked = True
    assert blocked, "non-completion event authorized inventory movement"


def _assert_dictionary_coverage(text):
    actual = [
        (table, column)
        for table, column, _ in re.findall(r"^\| `([a-z_]+)\.([a-z_]+)` \|(.+)$", text, re.MULTILINE)
    ]
    expected = [(table, column) for table, columns in EXPECTED_COLUMNS.items() for column in columns]
    assert len(actual) == len(set(actual)) == 69
    assert set(actual) == set(expected)


def _parse_controls(text):
    matches = re.findall(
        r"(?ms)^-- CONTROL: ([A-Z0-9_]+)\s*\r?\n(.*?;)(?=\s*^-- CONTROL:|\s*\Z)",
        text,
    )
    return {control_id: sql.strip() for control_id, sql in matches}


def _metric_fixture(connection):
    fixtures = (
        ("001", "COMPLETED", 0, 0, "2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z"),
        ("002", "COMPLETED", 1, 1, "2026-01-01T00:00:00Z", "2026-01-01T00:03:00Z"),
        ("003", "FAILED", 0, 1, "2026-01-01T00:00:00Z", None),
        ("004", "TIMED_OUT", 1, 1, "2026-01-01T00:00:00Z", None),
        ("005", "VALIDATED", 0, 0, None, None),
    )
    for suffix, state, retry, failure, dispatched, completed in fixtures:
        pallet_id, task_id, correlation_id = _insert_pallet_and_task(
            connection, suffix, state=state, retry_count=retry, failure_count=failure,
            dispatched_at=dispatched, completed_at=completed,
        )
        if state == "COMPLETED":
            event_id = f"EVT-SYN-{suffix}"
            connection.execute(
                "INSERT INTO wcs_event VALUES (?, ?, 'DEV-DEMO-CONV', 'TASK_COMPLETED', ?, ?, 1, '{}')",
                (event_id, task_id, correlation_id, completed),
            )
            connection.execute(
                "INSERT INTO inventory_movement VALUES (?, ?, ?, NULL, 'LOC-DEMO-A01', ?, ?)",
                (f"MOV-SYN-{suffix}", task_id, pallet_id, event_id, completed),
            )
    connection.executemany(
        "INSERT INTO exception_case VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            (
                "EXC-SYN-001", "TASK-SYN-003", "PLT-SYN-003", "DEVICE_OFFLINE", "open",
                1, 0, "Synthetic offline evidence.", "2026-01-01T00:01:00Z",
                "2026-01-01T00:01:00Z", None,
            ),
            (
                "EXC-SYN-002", "TASK-SYN-004", "PLT-SYN-004", "TASK_TIMEOUT", "open",
                1, 1, "Synthetic timeout evidence.", "2026-01-01T00:02:00Z",
                "2026-01-01T00:02:00Z", None,
            ),
            (
                "EXC-SYN-003", "TASK-SYN-002", "PLT-SYN-002", "PALLET_JAM", "resolved",
                1, 1, "Synthetic resolved jam.", "2026-01-01T00:01:00Z",
                "2026-01-01T00:02:00Z", "2026-01-01T00:02:00Z",
            ),
        ),
    )


def test_schema_has_exact_tables_columns_keys_and_foreign_keys():
    _assert_public_schema_contract(SCHEMA.read_text(encoding="utf-8"))
    connection = _database(seed=False)
    foreign_key_tables = {
        table: {row[2] for row in connection.execute(f"PRAGMA foreign_key_list({table})")}
        for table in EXPECTED_COLUMNS
    }
    assert foreign_key_tables["pallet"] == {"sku", "location"}
    assert foreign_key_tables["movement_task"] == {"pallet", "location", "device"}
    assert foreign_key_tables["device_command"] == {"movement_task", "device"}
    assert foreign_key_tables["wcs_event"] == {"movement_task", "device"}
    assert foreign_key_tables["inventory_movement"] == {"movement_task", "pallet", "location", "wcs_event"}
    assert foreign_key_tables["exception_case"] == {"movement_task", "pallet"}


def test_all_primary_key_identifiers_are_not_null_and_null_replays_persist_nothing():
    connection = _database()
    for table in EXPECTED_COLUMNS:
        primary = [row for row in connection.execute(f"PRAGMA table_info({table})") if row[5] > 0]
        assert len(primary) == 1
        assert primary[0][3] == 1, table

    for suffix in ("NULL-A", "NULL-B"):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO pallet VALUES (NULL, ?, 'SKU-DEMO-A', 'LOT-NULL', 1, '2026-01-01T00:00:00Z', NULL)",
                (f"RCPT-{suffix}",),
            )
    assert connection.execute("SELECT COUNT(*) FROM pallet WHERE pallet_id IS NULL").fetchone()[0] == 0

    _, task_id, correlation_id = _insert_pallet_and_task(connection, "NULL-EVENT")
    for timestamp in ("2026-01-01T00:00:20Z", "2026-01-01T00:00:21Z"):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO wcs_event VALUES (NULL, ?, 'DEV-DEMO-CONV', 'TASK_STARTED', ?, ?, 1, '{}')",
                (task_id, correlation_id, timestamp),
            )
    assert connection.execute("SELECT COUNT(*) FROM wcs_event WHERE event_id IS NULL").fetchone()[0] == 0


def test_sql_timestamp_contract_accepts_whole_second_utc_only():
    connection = _database()
    connection.execute(
        "INSERT INTO pallet VALUES ('PLT-TIME-OK', 'RCPT-TIME-OK', 'SKU-DEMO-A', 'LOT-TIME', 1, '2026-01-01T00:00:00Z', NULL)"
    )
    for index, timestamp in enumerate((
        "2026-01-01T00:00:00.123Z",
        "2026-01-01T07:00:00+07:00",
        "not-a-timestamp",
    )):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO pallet VALUES (?, ?, 'SKU-DEMO-A', 'LOT-TIME', 1, ?, NULL)",
                (f"PLT-TIME-BAD-{index}", f"RCPT-TIME-BAD-{index}", timestamp),
            )


def test_seed_contains_only_the_approved_synthetic_master_profile():
    connection = _database()
    assert {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in EXPECTED_COLUMNS
    } == {
        "sku": 3, "location": 4, "device": 3, "pallet": 0,
        "movement_task": 0, "device_command": 0, "wcs_event": 0,
        "inventory_movement": 0, "exception_case": 0,
    }
    assert connection.execute("SELECT SUM(is_active) FROM sku").fetchone()[0] == 2
    assert connection.execute("SELECT COUNT(DISTINCT zone_code) FROM location").fetchone()[0] == 2
    assert connection.execute(
        "SELECT status, COUNT(*) FROM device GROUP BY status ORDER BY status"
    ).fetchall() == [("offline", 1), ("online", 2)]
    assert {row[0] for row in connection.execute("SELECT device_type FROM device")} == {
        "conveyor", "lift", "robot"
    }


def test_public_constraints_reject_invalid_identity_quantity_capacity_and_ownership():
    connection = _database()
    connection.execute(
        "INSERT INTO pallet VALUES ('PLT-SYN-X', 'RCPT000010', 'SKU-DEMO-A', 'LOT-X', 1, '2026-01-01T00:00:00Z', NULL)"
    )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO pallet VALUES ('PLT-SYN-X', 'RCPT000011', 'SKU-DEMO-A', 'LOT-Y', 1, '2026-01-01T00:00:00Z', NULL)"
        )
    for quantity in (0, -1, 1.5):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO pallet VALUES (?, ?, 'SKU-DEMO-A', 'LOT-BAD', ?, '2026-01-01T00:00:00Z', NULL)",
                (f"PLT-BAD-{quantity}", f"BAD{quantity}", quantity),
            )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO pallet VALUES ('PLT-UNKNOWN', 'UNKNOWN001', 'SKU-NOT-KNOWN', 'LOT-X', 1, '2026-01-01T00:00:00Z', NULL)"
        )
    for values in (("LOC-BAD-1", 0, 0), ("LOC-BAD-2", 1, -1), ("LOC-BAD-3", 1, 2), ("LOC-BAD-4", 1.5, 0)):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO location VALUES (?, ?, 'ZONE-X', 9, 'AMBIENT', ?, ?)",
                (values[0], values[0], values[1], values[2]),
            )
    for device_type, status in (("forklift", "online"), ("robot", "maintenance")):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO device VALUES (?, 'Synthetic invalid device', ?, ?)",
                (f"DEV-BAD-{device_type}", device_type, status),
            )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO pallet VALUES ('PLT-BAD-TIME', 'BADTIME001', 'SKU-DEMO-A', 'LOT-X', 1, 'xxxx-01-01T00:00:00Z', NULL)"
        )


def test_state_event_device_command_and_counter_vocabularies_are_exact():
    connection = _database()
    _, task_id, correlation_id = _insert_pallet_and_task(connection, "100")
    for state in STATES:
        connection.execute("UPDATE movement_task SET state=? WHERE task_id=?", (state, task_id))
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("UPDATE movement_task SET state='REOPENED' WHERE task_id=?", (task_id,))
    for column, bad_value in (("retry_count", -1), ("retry_count", 3), ("failure_count", -1), ("failure_count", 4)):
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(f"UPDATE movement_task SET {column}=? WHERE task_id=?", (bad_value, task_id))
    for attempt in (0, 1, 2):
        connection.execute(
            "INSERT INTO device_command VALUES (?, ?, 'DEV-DEMO-CONV', ?, 'SENT', ?, '2026-01-01T00:00:20Z')",
            (f"CMD-SYN-{attempt}", task_id, attempt, correlation_id),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO device_command VALUES ('CMD-BAD', ?, 'DEV-DEMO-CONV', 3, 'SENT', ?, '2026-01-01T00:00:20Z')",
            (task_id, correlation_id),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("UPDATE device_command SET command_status='EXECUTING' WHERE command_id='CMD-SYN-0'")
    for index, event_type in enumerate(EVENT_TYPES):
        connection.execute(
            "INSERT INTO wcs_event VALUES (?, ?, 'DEV-DEMO-CONV', ?, ?, '2026-01-01T00:00:30Z', 1, '{}')",
            (f"EVT-SYN-TYPE-{index}", task_id, event_type, correlation_id),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO wcs_event VALUES ('EVT-EXTRA', ?, 'DEV-DEMO-CONV', 'TASK_ACCEPTED', ?, '2026-01-01T00:00:30Z', 1, '{}')",
            (task_id, correlation_id),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO wcs_event VALUES ('EVT-NOT-SIM', ?, 'DEV-DEMO-CONV', 'TASK_STARTED', ?, '2026-01-01T00:00:30Z', 0, '{}')",
            (task_id, correlation_id),
        )
    for index, error_code in enumerate(ERROR_CODES):
        connection.execute(
            "INSERT INTO exception_case VALUES (?, NULL, NULL, ?, 'open', 0, 0, 'Synthetic error evidence.', '2026-01-01T00:00:40Z', '2026-01-01T00:00:40Z', NULL)",
            (f"EXC-SYN-TYPE-{index}", error_code),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO exception_case VALUES ('EXC-EXTRA', NULL, NULL, 'UNLISTED_ERROR', 'open', 0, 0, 'Synthetic.', '2026-01-01T00:00:40Z', '2026-01-01T00:00:40Z', NULL)"
        )


def test_inventory_requires_matching_completed_task_and_completion_event_exactly_once():
    connection = _database()
    pallet_id, task_id, correlation_id = _insert_pallet_and_task(
        connection, "200", state="DISPATCHED", dispatched_at="2026-01-01T00:00:20Z"
    )
    connection.execute(
        "INSERT INTO wcs_event VALUES ('EVT-SYN-200', ?, 'DEV-DEMO-CONV', 'TASK_COMPLETED', ?, '2026-01-01T00:01:20Z', 1, '{}')",
        (task_id, correlation_id),
    )
    movement = (
        "MOV-SYN-200", task_id, pallet_id, None, "LOC-DEMO-A01", "EVT-SYN-200", "2026-01-01T00:01:20Z",
    )
    with pytest.raises(sqlite3.IntegrityError, match="COMPLETED"):
        connection.execute("INSERT INTO inventory_movement VALUES (?, ?, ?, ?, ?, ?, ?)", movement)
    assert connection.execute("SELECT COUNT(*) FROM inventory_movement").fetchone()[0] == 0
    connection.execute(
        "UPDATE movement_task SET state='COMPLETED', completed_at='2026-01-01T00:01:20Z' WHERE task_id=?",
        (task_id,),
    )
    connection.execute("INSERT INTO inventory_movement VALUES (?, ?, ?, ?, ?, ?, ?)", movement)
    assert connection.execute("SELECT COUNT(*) FROM inventory_movement").fetchone()[0] == 1
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO wcs_event VALUES ('EVT-SYN-200', ?, 'DEV-DEMO-CONV', 'TASK_COMPLETED', ?, '2026-01-01T00:01:20Z', 1, '{}')",
            (task_id, correlation_id),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO inventory_movement VALUES ('MOV-SYN-201', ?, ?, NULL, 'LOC-DEMO-A01', 'EVT-SYN-200', '2026-01-01T00:01:21Z')",
            (task_id, pallet_id),
        )
    assert connection.execute("SELECT COUNT(*) FROM inventory_movement").fetchone()[0] == 1


def test_inventory_rejects_wrong_task_pallet_destination_or_source_event():
    connection = _database()
    pallet_id, task_id, correlation_id = _insert_pallet_and_task(
        connection, "300", state="COMPLETED", dispatched_at="2026-01-01T00:00:20Z",
        completed_at="2026-01-01T00:01:20Z",
    )
    _, other_task, other_correlation = _insert_pallet_and_task(
        connection, "301", state="FAILED", dispatched_at="2026-01-01T00:00:20Z", failure_count=1
    )
    connection.execute(
        "INSERT INTO wcs_event VALUES ('EVT-WRONG-TYPE', ?, 'DEV-DEMO-CONV', 'TASK_FAILED', ?, '2026-01-01T00:01:20Z', 1, '{}')",
        (task_id, correlation_id),
    )
    connection.execute(
        "INSERT INTO wcs_event VALUES ('EVT-WRONG-TASK', ?, 'DEV-DEMO-CONV', 'TASK_COMPLETED', ?, '2026-01-01T00:01:20Z', 1, '{}')",
        (other_task, other_correlation),
    )
    for event_id in ("EVT-WRONG-TYPE", "EVT-WRONG-TASK"):
        with pytest.raises(sqlite3.IntegrityError, match="TASK_COMPLETED"):
            connection.execute(
                "INSERT INTO inventory_movement VALUES (?, ?, ?, NULL, 'LOC-DEMO-A01', ?, '2026-01-01T00:01:20Z')",
                (f"MOV-{event_id}", task_id, pallet_id, event_id),
            )
    with pytest.raises(sqlite3.IntegrityError, match="COMPLETED"):
        connection.execute(
            "INSERT INTO inventory_movement VALUES ('MOV-WRONG-DEST', ?, ?, NULL, 'LOC-DEMO-B01', 'EVT-WRONG-TYPE', '2026-01-01T00:01:20Z')",
            (task_id, pallet_id),
        )


def test_validation_controls_execute_and_return_independent_worked_values():
    controls = _parse_controls(CONTROLS.read_text(encoding="utf-8"))
    assert tuple(controls) == CONTROL_IDS
    connection = _database()
    _metric_fixture(connection)
    for control_id in CONTROL_IDS[:5]:
        assert connection.execute(controls[control_id]).fetchall() == [], control_id
    assert connection.execute(controls["CTRL_06_OPEN_EXCEPTION_COUNTS"]).fetchall() == [
        ("DEVICE_OFFLINE", "open", 1), ("TASK_TIMEOUT", "open", 1),
    ]
    expected_metrics = {
        "METRIC_01_COMPLETION_RATE": ("Completion Rate", 2, 4, 0.5),
        "METRIC_02_EXCEPTION_RATE": ("Exception Rate", 3, 4, 0.75),
        "METRIC_03_FIRST_PASS_SUCCESS_RATE": ("First Pass Success Rate", 1, 4, 0.25),
        "METRIC_04_AVERAGE_SIMULATED_CYCLE_TIME": ("Average Simulated Cycle Time", 2, 120.0),
    }
    for control_id, expected in expected_metrics.items():
        assert connection.execute(controls[control_id]).fetchone() == expected


def test_metric_controls_return_null_for_an_empty_dispatched_cohort():
    controls = _parse_controls(CONTROLS.read_text(encoding="utf-8"))
    connection = _database()
    for control_id in CONTROL_IDS[6:9]:
        row = connection.execute(controls[control_id]).fetchone()
        assert row[1:3] == (0, 0)
        assert row[3] is None
    assert connection.execute(
        controls["METRIC_04_AVERAGE_SIMULATED_CYCLE_TIME"]
    ).fetchone() == ("Average Simulated Cycle Time", 0, None)


def test_dictionary_covers_every_physical_column_once_with_required_semantics():
    text = DICTIONARY.read_text(encoding="utf-8")
    rows = re.findall(r"^\| `([a-z_]+)\.([a-z_]+)` \|(.+)$", text, re.MULTILINE)
    _assert_dictionary_coverage(text)
    for table, column, remainder in rows:
        cells = [cell.strip() for cell in remainder.rstrip().rstrip("|").split("|")]
        assert len(cells) == 8, f"{table}.{column} must have all dictionary fields"
        assert all(cells), f"{table}.{column} has an empty dictionary field"
        assert re.search(r"`(?:FR|BR|NFR)-\d{2}`", cells[6]), f"{table}.{column} lacks a valid link"
        assert "PII" in cells[7]
    required_sections = (
        "## Status, disclosure, and evidence boundary", "## Logical ERD",
        "## Business glossary", "## Entity dictionary", "## Physical column dictionary",
        "## API to schema to read-model and metric lineage", "## Metric contract",
        "## Conflict and gap log", "## Human review boundary",
    )
    assert all(section in text for section in required_sections)
    assert "```mermaid" in text and "erDiagram" in text
    assert "Currency" in text and "N/A" in text and "NULL" in text
    for table in EXPECTED_COLUMNS:
        identifier = EXPECTED_COLUMNS[table][0]
        row = next(remainder for row_table, column, remainder in rows if row_table == table and column == identifier)
        nullable = [cell.strip() for cell in row.rstrip().rstrip("|").split("|")][2]
        assert nullable == "No", f"{table}.{identifier} dictionary nullability drift"


def test_dictionary_erd_lineage_and_timestamp_precision_match_physical_and_api_contracts():
    text = DICTIONARY.read_text(encoding="utf-8")
    assert 'LOCATION o|--o{ INVENTORY_MOVEMENT : "is previous location for"' in text
    assert 'LOCATION ||--o{ INVENTORY_MOVEMENT : "is destination for"' in text
    pallet_lineage = next(
        line for line in text.splitlines() if line.startswith("| `POST /pallets` |")
    )
    assert "`movement_task`" in pallet_lineage
    assert "validated task" in pallet_lineage.lower()
    assert "`FR-05`" in pallet_lineage
    assert "API/domain orchestration" in pallet_lineage
    assert "database trigger" not in pallet_lineage.lower()
    assert "whole-second UTC" in text
    assert "fractional seconds" in text
    assert "offset" in text


def test_mutations_are_rejected_by_schema_trigger_and_dictionary_guards():
    schema_text = SCHEMA.read_text(encoding="utf-8")
    without_unique_event = schema_text.replace("event_id TEXT PRIMARY KEY NOT NULL", "event_id TEXT NOT NULL", 1)
    with pytest.raises(AssertionError):
        _assert_public_schema_contract(without_unique_event)

    extra_state = schema_text.replace("'CANCELLED'\n    )),", "'CANCELLED', 'paused'\n    )),", 1)
    with pytest.raises(AssertionError):
        _assert_public_schema_contract(extra_state)

    missing_pk_not_null = schema_text.replace("pallet_id TEXT PRIMARY KEY NOT NULL", "pallet_id TEXT PRIMARY KEY", 1)
    with pytest.raises(AssertionError):
        _assert_public_schema_contract(missing_pk_not_null)

    trigger_pattern = re.compile(
        r"CREATE TRIGGER inventory_movement_requires_completed_task.*?END;", re.DOTALL
    )
    no_completed_trigger = trigger_pattern.sub("", schema_text, count=1)
    with pytest.raises(AssertionError):
        _assert_precompletion_insert_blocked(no_completed_trigger)

    event_trigger_pattern = re.compile(
        r"CREATE TRIGGER inventory_movement_requires_completion_event.*?END;", re.DOTALL
    )
    no_event_trigger = event_trigger_pattern.sub("", schema_text, count=1)
    with pytest.raises(AssertionError):
        _assert_noncompletion_source_blocked(no_event_trigger)

    dictionary_text = DICTIONARY.read_text(encoding="utf-8")
    omitted = re.sub(r"(?m)^\| `wcs_event\.event_id` \|.*\r?\n", "", dictionary_text, count=1)
    with pytest.raises(AssertionError):
        _assert_dictionary_coverage(omitted)


def test_task4_artifacts_contain_no_remote_or_private_material():
    files = (SCHEMA, SEED, CONTROLS, DICTIONARY, PROJECT_ROOT / "api" / "openapi.yaml")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for pattern in (
        r"(?i)\bkakadata\b", r"https?://",
        r"(?i)\b(?:password|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*[^\s,}]+",
        r"(?i)[A-Z]:\\Users\\",
    ):
        assert re.search(pattern, combined) is None, pattern
