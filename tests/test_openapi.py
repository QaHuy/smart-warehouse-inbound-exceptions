import copy
import json
import re
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENAPI = PROJECT_ROOT / "api" / "openapi.yaml"
SRS = PROJECT_ROOT / "docs" / "04-srs-fsd-lite.md"
TASK_STATE = PROJECT_ROOT / "diagrams" / "task-state.md"

STATES = [
    "CREATED", "VALIDATED", "DISPATCHED", "IN_PROGRESS",
    "COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED",
]
EVENT_TYPES = ["TASK_STARTED", "TASK_COMPLETED", "TASK_FAILED", "TASK_TIMEOUT"]
ERROR_CODES = [
    "INVALID_BARCODE", "UNKNOWN_OR_INACTIVE_SKU", "INVALID_QUANTITY",
    "DUPLICATE_PALLET", "NO_AVAILABLE_LOCATION", "DEVICE_OFFLINE", "PALLET_JAM",
    "TASK_TIMEOUT", "INVALID_TRANSITION", "UNKNOWN_TASK", "DUPLICATE_EVENT",
    "RETRY_LIMIT_REACHED", "CANCELLATION_NOT_ALLOWED",
]
OPERATIONS = {
    ("/pallets", "post"),
    ("/tasks/{taskId}/dispatch", "post"),
    ("/wcs/events", "post"),
    ("/tasks/{taskId}/retry", "post"),
    ("/tasks/{taskId}/cancel", "post"),
    ("/tasks", "get"),
    ("/inventory", "get"),
    ("/metrics", "get"),
}
HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
WHOLE_SECOND_UTC_PATTERN = "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
REQUIRED_ERRORS = {
    ("/pallets", "post"): {"400", "409", "422"},
    ("/tasks/{taskId}/dispatch", "post"): {"404", "409", "503"},
    ("/wcs/events", "post"): {"400", "404", "409"},
    ("/tasks/{taskId}/retry", "post"): {"404", "409"},
    ("/tasks/{taskId}/cancel", "post"): {"404", "409"},
    ("/tasks", "get"): set(),
    ("/inventory", "get"): set(),
    ("/metrics", "get"): set(),
}


def _load():
    return json.loads(OPENAPI.read_text(encoding="utf-8"))


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _resolve(document, ref):
    assert ref.startswith("#/"), f"Only local references are allowed: {ref}"
    value = document
    for part in ref[2:].split("/"):
        value = value[part.replace("~1", "/").replace("~0", "~")]
    return value


def _resolved(document, value):
    return _resolve(document, value["$ref"]) if isinstance(value, dict) and "$ref" in value else value


def _assert_instance_valid(document, schema, value, path="example"):
    schema = _resolved(document, schema)
    expected_type = schema.get("type")
    allowed_types = expected_type if isinstance(expected_type, list) else [expected_type]
    if value is None:
        assert "null" in allowed_types, f"{path} unexpectedly null"
        return
    if expected_type is not None:
        type_checks = {
            "object": lambda item: isinstance(item, dict),
            "array": lambda item: isinstance(item, list),
            "string": lambda item: isinstance(item, str),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
            "boolean": lambda item: isinstance(item, bool),
            "null": lambda item: item is None,
        }
        assert any(type_checks[kind](value) for kind in allowed_types), f"{path} has wrong type"
    if "const" in schema:
        assert value == schema["const"], f"{path} violates const"
    if "enum" in schema:
        assert value in schema["enum"], f"{path} is outside enum"
    if isinstance(value, str):
        assert len(value) >= schema.get("minLength", 0), f"{path} is too short"
        if "pattern" in schema:
            assert re.search(schema["pattern"], value), f"{path} violates pattern"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema:
            assert value >= schema["minimum"], f"{path} is below minimum"
        if "maximum" in schema:
            assert value <= schema["maximum"], f"{path} is above maximum"
    if isinstance(value, dict):
        for required in schema.get("required", []):
            assert required in value, f"{path} missing {required}"
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            assert set(value) <= set(properties), f"{path} has additional property"
        for name, child in value.items():
            if name in properties:
                _assert_instance_valid(document, properties[name], child, f"{path}.{name}")
    if isinstance(value, list) and "items" in schema:
        for index, child in enumerate(value):
            _assert_instance_valid(document, schema["items"], child, f"{path}[{index}]")


def _assert_examples_valid(document):
    for path, method in OPERATIONS:
        operation = document["paths"][path][method]
        if method == "post":
            media = operation["requestBody"]["content"]["application/json"]
            _assert_instance_valid(document, media["schema"], media["example"], f"{method} {path} request")
        for status, raw_response in operation["responses"].items():
            response = _resolved(document, raw_response)
            media = response.get("content", {}).get("application/json")
            if not media:
                continue
            if "example" in media:
                _assert_instance_valid(document, media["schema"], media["example"], f"{method} {path} {status}")
            for name, example in media.get("examples", {}).items():
                _assert_instance_valid(document, media["schema"], example["value"], f"{method} {path} {status} {name}")


def _assert_operation_contract(document):
    actual = {
        (path, method)
        for path, path_item in document["paths"].items()
        for method in path_item
        if method in HTTP_METHODS
    }
    assert actual == OPERATIONS
    operation_ids = []
    for operation_key in OPERATIONS:
        path, method = operation_key
        operation = document["paths"][path][method]
        assert operation.get("summary")
        operation_ids.append(operation.get("operationId"))
        assert operation.get("x-requirements")
        assert operation.get("x-business-rules")
        correlation = [
            _resolved(document, parameter)
            for parameter in operation.get("parameters", [])
            if _resolved(document, parameter).get("name") == "X-Correlation-Id"
        ]
        assert len(correlation) == 1
        assert correlation[0]["in"] == "header" and correlation[0]["required"] is True
        if "{taskId}" in path:
            task_parameters = [
                _resolved(document, parameter)
                for parameter in operation.get("parameters", [])
                if _resolved(document, parameter).get("name") == "taskId"
            ]
            assert len(task_parameters) == 1
            assert task_parameters[0]["in"] == "path" and task_parameters[0]["required"] is True
        if method == "post":
            assert operation.get("requestBody", {}).get("required") is True
            request_media = operation["requestBody"]["content"]["application/json"]
            assert request_media.get("schema") and request_media.get("example") is not None
        responses = operation["responses"]
        assert any(status.startswith("2") for status in responses)
        assert REQUIRED_ERRORS[operation_key] <= set(responses)
        assert any("example" in node or "examples" in node for node in _walk(operation))
    assert None not in operation_ids
    assert len(operation_ids) == len(set(operation_ids)) == 8


def test_json_compatible_yaml_has_exact_openapi_surface_and_portability_note():
    document = _load()
    assert document["openapi"] == "3.1.0"
    assert "JSON-compatible YAML 1.2" in document["x-portfolio-note"]
    assert "servers" not in document
    assert "security" not in document
    _assert_operation_contract(document)


def test_every_reference_resolves_locally_and_contract_has_no_remote_or_auth_claim():
    document = _load()
    references = [node["$ref"] for node in _walk(document) if "$ref" in node]
    assert references
    for ref in references:
        assert _resolve(document, ref) is not None
    serialized = json.dumps(document)
    assert "http" + "://" not in serialized and "https" + "://" not in serialized
    assert '"servers"' not in serialized
    assert '"securitySchemes"' not in serialized


def test_sql_state_event_and_error_vocabularies_match_task_2_and_3_exactly():
    document = _load()
    schemas = document["components"]["schemas"]
    assert schemas["TaskState"]["enum"] == STATES
    assert schemas["WcsEventType"]["enum"] == EVENT_TYPES
    assert schemas["ErrorCode"]["enum"] == ERROR_CODES
    source_contract = SRS.read_text(encoding="utf-8") + TASK_STATE.read_text(encoding="utf-8")
    assert all(f"`{value}`" in source_contract for value in STATES + EVENT_TYPES + ERROR_CODES)


def test_requests_responses_envelopes_required_fields_and_simulation_marker_are_explicit():
    document = _load()
    schemas = document["components"]["schemas"]
    assert schemas["PalletCreateRequest"]["required"] == [
        "pallet_id", "receipt_barcode", "sku_id", "lot_code", "quantity"
    ]
    assert schemas["WcsEventRequest"]["required"] == [
        "event_id", "task_id", "device_id", "event_type", "correlation_id", "event_at", "simulated"
    ]
    assert schemas["WcsEventRequest"]["properties"]["simulated"] == {
        "type": "boolean", "const": True, "description": "Always true: WCS/device evidence is simulated."
    }
    assert schemas["Task"]["required"] == [
        "task_id", "pallet_id", "destination_location_id", "device_id", "state",
        "retry_count", "failure_count", "correlation_id", "created_at"
    ]
    assert schemas["Error"]["required"] == ["code", "message", "correlation_id"]
    for name in (
        "PalletEnvelope", "TaskEnvelope", "EventEnvelope", "TaskListEnvelope",
        "InventoryListEnvelope", "MetricsEnvelope",
    ):
        assert schemas[name]["required"] == ["ok", "value"]
        assert schemas[name]["properties"]["ok"]["const"] is True
    assert schemas["ErrorEnvelope"]["required"] == ["ok", "error"]
    assert schemas["ErrorEnvelope"]["properties"]["ok"]["const"] is False


def test_every_api_datetime_uses_exact_whole_second_utc_precision_and_examples_validate():
    document = _load()
    datetime_schemas = [
        node for node in _walk(document)
        if node.get("format") == "date-time"
    ]
    assert datetime_schemas
    assert all(schema.get("pattern") == WHOLE_SECOND_UTC_PATTERN for schema in datetime_schemas)
    pattern = re.compile(WHOLE_SECOND_UTC_PATTERN)
    assert pattern.fullmatch("2026-01-01T00:00:00Z")
    assert not pattern.fullmatch("2026-01-01T00:00:00.123Z")
    assert not pattern.fullmatch("2026-01-01T07:00:00+07:00")
    assert not pattern.fullmatch("not-a-timestamp")
    _assert_examples_valid(document)


def test_duplicate_event_is_successful_and_does_not_describe_a_second_mutation():
    document = _load()
    operation = document["paths"]["/wcs/events"]["post"]
    success = operation["responses"]["200"]
    examples = success["content"]["application/json"]["examples"]
    duplicate = examples["duplicate"]["value"]
    assert duplicate["ok"] is True
    assert duplicate["value"]["duplicate"] is True
    assert duplicate["value"]["state_mutated"] is False
    assert duplicate["value"]["inventory_mutated"] is False
    assert document["components"]["schemas"]["WcsEventRequest"]["properties"]["event_id"]["description"].startswith(
        "Idempotency key"
    )


def test_dispatch_success_returns_the_command_identity_persisted_before_state_change():
    document = _load()
    success = document["paths"]["/tasks/{taskId}/dispatch"]["post"]["responses"]["200"]
    media = success["content"]["application/json"]
    assert media["schema"]["$ref"] == "#/components/schemas/DispatchEnvelope"
    value = media["example"]["value"]
    assert value["command"]["command_id"] == "CMD-SYN-101"
    assert value["command"]["attempt_number"] == 0
    assert value["command"]["task_id"] == value["task"]["task_id"]
    assert value["command"]["correlation_id"] == value["task"]["correlation_id"]
    assert value["task"]["state"] == "DISPATCHED"
    schemas = document["components"]["schemas"]
    assert schemas["DeviceCommand"]["required"] == [
        "command_id", "task_id", "device_id", "attempt_number",
        "command_status", "correlation_id", "sent_at",
    ]
    assert schemas["DispatchResult"]["required"] == ["task", "command"]
    assert schemas["DispatchEnvelope"]["required"] == ["ok", "value"]


def _assert_retry_contract(document):
    operation = document["paths"]["/tasks/{taskId}/retry"]["post"]
    assert set(operation["responses"]) == {"200", "404", "409", "503"}
    success = operation["responses"]["200"]["content"]["application/json"]["example"]
    assert success["value"]["state"] == "DISPATCHED"
    assert success["value"]["retry_count"] == 1

    offline_response = _resolve(document, operation["responses"]["503"]["$ref"])
    offline = offline_response["content"]["application/json"]["example"]
    assert offline["error"]["code"] == "DEVICE_OFFLINE"
    assert offline["value"] == {
        "task_id": "TASK-SYN-102",
        "state": "FAILED",
        "retry_count": 1,
        "failure_count": 2,
        "exception_status": "open",
        "command_created": False,
    }

    conflict_response = _resolve(document, operation["responses"]["409"]["$ref"])
    examples = conflict_response["content"]["application/json"]["examples"]
    invalid = examples["invalidOrigin"]["value"]
    exhausted = examples["retryLimit"]["value"]
    assert invalid["error"]["code"] == "INVALID_TRANSITION"
    assert invalid["value"]["state_mutated"] is False
    assert invalid["value"]["command_created"] is False
    assert exhausted["error"]["code"] == "RETRY_LIMIT_REACHED"
    assert exhausted["value"]["state"] == "FAILED"
    assert exhausted["value"]["retry_count"] == 2
    assert exhausted["value"]["failure_count"] == 3
    assert exhausted["value"]["exception_status"] == "escalated"
    assert exhausted["value"]["third_retry_command_created"] is False


def test_retry_contract_distinguishes_success_offline_invalid_origin_limit_and_not_found():
    _assert_retry_contract(_load())


def test_error_responses_reuse_specific_catalogued_examples():
    document = _load()
    responses = document["components"]["responses"]
    expected = {
        "ValidationError": "INVALID_QUANTITY",
        "ConflictError": "DUPLICATE_PALLET",
        "NoAvailableLocationError": "NO_AVAILABLE_LOCATION",
        "DeviceOfflineError": "DEVICE_OFFLINE",
        "InvalidTransitionError": "INVALID_TRANSITION",
        "RetryLimitError": "RETRY_LIMIT_REACHED",
        "CancellationNotAllowedError": "CANCELLATION_NOT_ALLOWED",
        "NotFoundError": "UNKNOWN_TASK",
    }
    for name, code in expected.items():
        response = responses[name]
        assert response["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorEnvelope"
        assert response["content"]["application/json"]["example"]["error"]["code"] == code


def test_requirement_rule_links_are_valid_and_cover_high_risk_contracts():
    document = _load()
    valid_fr = {f"FR-{number:02d}" for number in range(1, 11)}
    valid_br = {f"BR-{number:02d}" for number in range(1, 11)}
    used_fr = set()
    used_br = set()
    for path, method in OPERATIONS:
        operation = document["paths"][path][method]
        used_fr.update(operation["x-requirements"])
        used_br.update(operation["x-business-rules"])
    assert used_fr <= valid_fr and used_br <= valid_br
    assert {"FR-01", "FR-06", "FR-07", "FR-09", "FR-10"} <= used_fr
    assert {"BR-05", "BR-06", "BR-07", "BR-08", "BR-09", "BR-10"} <= used_br


def test_openapi_mutations_break_reference_and_required_error_guards():
    document = _load()
    broken = copy.deepcopy(document)
    broken["paths"]["/wcs/events"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] = "#/components/schemas/MissingEnvelope"
    with pytest.raises(KeyError):
        for node in _walk(broken):
            if "$ref" in node:
                _resolve(broken, node["$ref"])

    missing_error = copy.deepcopy(document)
    del missing_error["paths"]["/tasks/{taskId}/retry"]["post"]["responses"]["409"]
    with pytest.raises(AssertionError):
        _assert_operation_contract(missing_error)


def test_http_body_header_example_timestamp_and_retry_mutations_are_rejected():
    document = _load()

    extra_method = copy.deepcopy(document)
    extra_method["paths"]["/tasks"]["delete"] = copy.deepcopy(extra_method["paths"]["/tasks"]["get"])
    extra_method["paths"]["/tasks"]["delete"]["operationId"] = "deleteTasks"
    with pytest.raises(AssertionError):
        _assert_operation_contract(extra_method)

    for path, method in OPERATIONS:
        if method != "post":
            continue
        missing_body = copy.deepcopy(document)
        del missing_body["paths"][path][method]["requestBody"]
        with pytest.raises(AssertionError):
            _assert_operation_contract(missing_body)

    optional_header = copy.deepcopy(document)
    optional_header["components"]["parameters"]["CorrelationId"]["required"] = False
    with pytest.raises(AssertionError):
        _assert_operation_contract(optional_header)

    for path, method in OPERATIONS:
        missing_header = copy.deepcopy(document)
        operation = missing_header["paths"][path][method]
        operation["parameters"] = [
            parameter for parameter in operation["parameters"]
            if _resolved(missing_header, parameter).get("name") != "X-Correlation-Id"
        ]
        with pytest.raises(AssertionError):
            _assert_operation_contract(missing_header)

    negative_quantity = copy.deepcopy(document)
    negative_quantity["paths"]["/pallets"]["post"]["requestBody"]["content"]["application/json"]["example"]["quantity"] = -1
    with pytest.raises(AssertionError):
        _assert_examples_valid(negative_quantity)

    invalid_response = copy.deepcopy(document)
    invalid_response["paths"]["/metrics"]["get"]["responses"]["200"]["content"]["application/json"]["example"]["value"]["completion_rate"] = 1.5
    with pytest.raises(AssertionError):
        _assert_examples_valid(invalid_response)

    fractional_event = copy.deepcopy(document)
    fractional_event["paths"]["/wcs/events"]["post"]["requestBody"]["content"]["application/json"]["example"]["event_at"] = "2026-01-01T00:02:10.123Z"
    with pytest.raises(AssertionError):
        _assert_examples_valid(fractional_event)

    missing_retry_offline = copy.deepcopy(document)
    del missing_retry_offline["paths"]["/tasks/{taskId}/retry"]["post"]["responses"]["503"]
    with pytest.raises(AssertionError):
        _assert_retry_contract(missing_retry_offline)

    missing_invalid_origin = copy.deepcopy(document)
    conflict = _resolve(
        missing_invalid_origin,
        missing_invalid_origin["paths"]["/tasks/{taskId}/retry"]["post"]["responses"]["409"]["$ref"],
    )
    del conflict["content"]["application/json"]["examples"]["invalidOrigin"]
    with pytest.raises((AssertionError, KeyError)):
        _assert_retry_contract(missing_invalid_origin)

    missing_retry_limit = copy.deepcopy(document)
    conflict = _resolve(
        missing_retry_limit,
        missing_retry_limit["paths"]["/tasks/{taskId}/retry"]["post"]["responses"]["409"]["$ref"],
    )
    del conflict["content"]["application/json"]["examples"]["retryLimit"]
    with pytest.raises((AssertionError, KeyError)):
        _assert_retry_contract(missing_retry_limit)
