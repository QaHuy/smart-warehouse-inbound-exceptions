import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict, deque
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DIAGRAM_DIR = PROJECT_ROOT / "diagrams"
AS_IS = DIAGRAM_DIR / "as-is-inbound.bpmn"
TO_BE = DIAGRAM_DIR / "to-be-inbound.bpmn"
CONTEXT = DIAGRAM_DIR / "system-context.md"
SEQUENCE = DIAGRAM_DIR / "wms-wcs-sequence.md"
STATE = DIAGRAM_DIR / "task-state.md"
DIAGRAM_FILES = (AS_IS, TO_BE, CONTEXT, SEQUENCE, STATE)
MARKDOWN_FILES = (CONTEXT, SEQUENCE, STATE)

DISCLOSURE = (
    "Personal WMS/WCS portfolio case study using synthetic data. "
    "WCS behavior and device events are simulated."
)
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
NS = {"bpmn": BPMN_NS}
EXACT_STATES = {
    "CREATED",
    "VALIDATED",
    "DISPATCHED",
    "IN_PROGRESS",
    "COMPLETED",
    "FAILED",
    "TIMED_OUT",
    "CANCELLED",
}
ALLOWED_TRANSITIONS = {
    ("CREATED", "VALIDATED"),
    ("CREATED", "CANCELLED"),
    ("VALIDATED", "DISPATCHED"),
    ("VALIDATED", "FAILED"),
    ("VALIDATED", "CANCELLED"),
    ("DISPATCHED", "IN_PROGRESS"),
    ("DISPATCHED", "COMPLETED"),
    ("DISPATCHED", "FAILED"),
    ("DISPATCHED", "TIMED_OUT"),
    ("DISPATCHED", "CANCELLED"),
    ("IN_PROGRESS", "COMPLETED"),
    ("IN_PROGRESS", "FAILED"),
    ("IN_PROGRESS", "TIMED_OUT"),
    ("IN_PROGRESS", "CANCELLED"),
    ("FAILED", "DISPATCHED"),
    ("FAILED", "CANCELLED"),
    ("TIMED_OUT", "DISPATCHED"),
    ("TIMED_OUT", "CANCELLED"),
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require_sources() -> None:
    if any(not path.is_file() for path in DIAGRAM_FILES):
        pytest.skip("diagram source set is not complete yet")


def _parse(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _all_ids(root: ET.Element) -> dict[str, ET.Element]:
    return {element.attrib["id"]: element for element in root.iter() if "id" in element.attrib}


def _owner_process(element: ET.Element, parent_map: dict[ET.Element, ET.Element]) -> str | None:
    current = element
    while current in parent_map:
        current = parent_map[current]
        if _local_name(current.tag) == "process":
            return current.attrib["id"]
    return None


def _process_graph(process: ET.Element) -> tuple[dict[str, set[str]], set[str], set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    starts = {e.attrib["id"] for e in process.findall("bpmn:startEvent", NS)}
    ends = {e.attrib["id"] for e in process.findall("bpmn:endEvent", NS)}
    for flow in process.findall("bpmn:sequenceFlow", NS):
        graph[flow.attrib["sourceRef"]].add(flow.attrib["targetRef"])
    return graph, starts, ends


def _reachable(graph: dict[str, set[str]], origins: set[str]) -> set[str]:
    seen = set(origins)
    queue = deque(origins)
    while queue:
        for target in graph.get(queue.popleft(), set()):
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return seen


def _graph_for_process(root: ET.Element, process_id: str) -> tuple[dict[str, set[str]], set[str]]:
    process = next(
        process
        for process in root.findall("bpmn:process", NS)
        if process.attrib["id"] == process_id
    )
    graph, starts, _ = _process_graph(process)
    return graph, starts


def _dominates(
    graph: dict[str, set[str]], origins: set[str], mandatory: str, target: str
) -> bool:
    without_mandatory = {
        source: {item for item in targets if item != mandatory}
        for source, targets in graph.items()
        if source != mandatory
    }
    return target not in _reachable(without_mandatory, origins - {mandatory})


def _assert_lane_integrity(root: ET.Element) -> None:
    ids = _all_ids(root)
    parent_map = {child: parent for parent in root.iter() for child in parent}
    assignments: Counter[str] = Counter()
    for process in root.findall("bpmn:process", NS):
        process_id = process.attrib["id"]
        for lane in process.findall(".//bpmn:lane", NS):
            for node_ref in lane.findall("bpmn:flowNodeRef", NS):
                target_id = (node_ref.text or "").strip()
                assert target_id in ids, (lane.attrib["id"], target_id)
                assert _owner_process(ids[target_id], parent_map) == process_id, (
                    lane.attrib["id"],
                    target_id,
                )
                assignments[target_id] += 1
    assert all(count == 1 for count in assignments.values()), assignments
    flow_node_tags = {
        "startEvent",
        "endEvent",
        "task",
        "userTask",
        "serviceTask",
        "sendTask",
        "receiveTask",
        "manualTask",
        "exclusiveGateway",
        "parallelGateway",
        "intermediateCatchEvent",
        "intermediateThrowEvent",
        "subProcess",
    }
    top_level_nodes = {
        element.attrib["id"]
        for process in root.findall("bpmn:process", NS)
        if process.find("bpmn:laneSet", NS) is not None
        for element in process
        if "id" in element.attrib and _local_name(element.tag) in flow_node_tags
    }
    assert set(assignments) == top_level_nodes, sorted(top_level_nodes - set(assignments))


def _bounds_by_semantic_ref(root: ET.Element) -> dict[str, tuple[float, float, float, float]]:
    bounds: dict[str, tuple[float, float, float, float]] = {}
    for shape in (element for element in root.iter() if _local_name(element.tag) == "BPMNShape"):
        bound = next((child for child in shape if _local_name(child.tag) == "Bounds"), None)
        assert bound is not None, shape.attrib["id"]
        bounds[shape.attrib["bpmnElement"]] = tuple(
            float(bound.attrib[key]) for key in ("x", "y", "width", "height")
        )
    return bounds


def _point_touches_shape_boundary(
    point: tuple[float, float],
    bounds: tuple[float, float, float, float],
    element: ET.Element,
    tolerance: float = 1.5,
) -> bool:
    point_x, point_y = point
    x, y, width, height = bounds
    tag = _local_name(element.tag)
    center_x, center_y = x + width / 2, y + height / 2
    radius_x, radius_y = width / 2, height / 2

    if tag in {"exclusiveGateway", "parallelGateway"}:
        normalized = abs(point_x - center_x) / radius_x + abs(point_y - center_y) / radius_y
        return abs(normalized - 1.0) * min(radius_x, radius_y) <= tolerance

    if tag in {
        "startEvent",
        "endEvent",
        "intermediateCatchEvent",
        "intermediateThrowEvent",
    }:
        normalized = (
            ((point_x - center_x) / radius_x) ** 2
            + ((point_y - center_y) / radius_y) ** 2
        ) ** 0.5
        return abs(normalized - 1.0) * min(radius_x, radius_y) <= tolerance

    within_x = x - tolerance <= point_x <= x + width + tolerance
    within_y = y - tolerance <= point_y <= y + height + tolerance
    on_vertical = abs(point_x - x) <= tolerance or abs(point_x - (x + width)) <= tolerance
    on_horizontal = abs(point_y - y) <= tolerance or abs(point_y - (y + height)) <= tolerance
    return (on_vertical and within_y) or (on_horizontal and within_x)


def _assert_flow_edge_endpoints_touch_shapes(root: ET.Element) -> None:
    ids = _all_ids(root)
    bounds = _bounds_by_semantic_ref(root)
    edges = {
        edge.attrib["bpmnElement"]: edge
        for edge in root.iter()
        if _local_name(edge.tag) == "BPMNEdge"
    }
    flows = [
        flow
        for process in root.findall("bpmn:process", NS)
        for flow in process.findall("bpmn:sequenceFlow", NS)
    ] + root.findall(".//bpmn:messageFlow", NS)
    for flow in flows:
        flow_id = flow.attrib["id"]
        source_id = flow.attrib["sourceRef"]
        target_id = flow.attrib["targetRef"]
        assert source_id in bounds and target_id in bounds, (flow_id, source_id, target_id)
        assert flow_id in edges, flow_id
        waypoints = [
            (float(point.attrib["x"]), float(point.attrib["y"]))
            for point in edges[flow_id]
            if _local_name(point.tag) == "waypoint"
        ]
        assert len(waypoints) >= 2, flow_id
        assert _point_touches_shape_boundary(waypoints[0], bounds[source_id], ids[source_id]), (
            flow_id,
            "source",
            source_id,
            waypoints[0],
        )
        assert _point_touches_shape_boundary(waypoints[-1], bounds[target_id], ids[target_id]), (
            flow_id,
            "target",
            target_id,
            waypoints[-1],
        )


def _assert_exact_gateway_routes(root: ET.Element) -> None:
    ids = _all_ids(root)
    flows_by_source: dict[str, dict[str, ET.Element]] = defaultdict(dict)
    for flow in root.findall(".//bpmn:sequenceFlow", NS):
        flows_by_source[flow.attrib["sourceRef"]][flow.attrib["id"]] = flow
    expectations = {
        "Gateway_Event_Valid": (
            "Unique event valid for current state?",
            {
                "Flow_Ops_Invalid_Event": (
                    "No",
                    "event_valid = false",
                    "Task_Record_Invalid_Event",
                ),
                "Flow_Ops_Valid_Event": (
                    "Yes",
                    "event_valid = true",
                    "Task_Intake_Route_Validated_Event",
                ),
            },
        ),
        "Gateway_Third_Failure": (
            "Third failure overall?",
            {
                "Flow_Ops_Third_Yes": (
                    "Yes",
                    "failure_count = 3",
                    "Task_Escalate",
                ),
                "Flow_Ops_Third_No": (
                    "No",
                    "failure_count < 3",
                    "Task_Show_Exception",
                ),
            },
        ),
    }
    for gateway_id, (question, expected_flows) in expectations.items():
        assert gateway_id in ids
        assert ids[gateway_id].attrib.get("name") == question
        outgoing = flows_by_source[gateway_id]
        assert set(outgoing) == set(expected_flows), (gateway_id, sorted(outgoing))
        for flow_id, (label, condition, target_id) in expected_flows.items():
            flow = outgoing[flow_id]
            assert flow.attrib.get("name") == label, flow_id
            condition_node = flow.find("bpmn:conditionExpression", NS)
            assert condition_node is not None, flow_id
            assert (condition_node.text or "").strip() == condition, flow_id
            assert flow.attrib["targetRef"] == target_id, flow_id


def _assert_independent_event_intake_lifecycle(root: ET.Element) -> None:
    ids = _all_ids(root)
    intake = ids.get("Process_Event_Intake")
    assert intake is not None and _local_name(intake.tag) == "process"
    participants = {
        participant.attrib["id"]: participant.attrib["processRef"]
        for participant in root.findall(".//bpmn:participant", NS)
    }
    assert participants.get("Participant_Event_Intake") == "Process_Event_Intake"
    assert "SubProcess_Terminal_Event_Intake" not in ids

    graph, starts, ends = _process_graph(intake)
    assert starts == {"Start_Event_Intake"}
    assert ends
    start = ids["Start_Event_Intake"]
    assert start.find("bpmn:messageEventDefinition", NS) is not None
    required = {
        "Task_Intake_Lookup_Event_Context",
        "Gateway_Intake_Context_Valid",
        "Gateway_Duplicate_Event",
        "Gateway_Event_Valid",
        "Task_Record_Invalid_Event",
        "Task_Return_Duplicate",
        "Task_Validate_WCS_Event",
        "Task_Intake_Route_Validated_Event",
    }
    assert required <= set(ids), sorted(required - set(ids))

    assert _dominates(
        graph,
        starts,
        "Task_Intake_Lookup_Event_Context",
        "Task_Intake_Route_Validated_Event",
    )
    assert _dominates(
        graph,
        starts,
        "Gateway_Duplicate_Event",
        "Task_Intake_Route_Validated_Event",
    )
    assert _dominates(
        graph,
        starts,
        "Gateway_Event_Valid",
        "Task_Intake_Route_Validated_Event",
    )
    assert "Task_Return_Duplicate" not in _reachable(
        graph, {"Task_Intake_Route_Validated_Event"}
    )
    assert any(
        end_id in _reachable(graph, {"Task_Return_Duplicate"}) for end_id in ends
    )
    assert any(
        end_id in _reachable(graph, {"Task_Record_Invalid_Event"}) for end_id in ends
    )

    lookup_name = ids["Task_Intake_Lookup_Event_Context"].attrib.get("name", "").lower()
    for token in ("required payload", "task", "correlation", "current state", "event_id"):
        assert token in lookup_name
    duplicate_name = ids["Task_Return_Duplicate"].attrib.get("name", "").lower()
    assert all(token in duplicate_name for token in ("duplicate", "success", "no state", "inventory"))
    invalid_name = ids["Task_Record_Invalid_Event"].attrib.get("name", "").lower()
    assert all(token in invalid_name for token in ("diagnostic audit", "no state", "inventory"))

    documentation = " ".join(intake.itertext()).lower()
    for token in (
        "independent intake instance",
        "after the related inbound process has ended",
        "non-terminal or terminal task",
        "without state or inventory mutation",
    ):
        assert token in documentation

    message_flows = {
        flow.attrib["id"]: (flow.attrib["sourceRef"], flow.attrib["targetRef"])
        for flow in root.findall(".//bpmn:messageFlow", NS)
    }
    assert message_flows.get("Message_Route_Validated_Event") == (
        "Task_Intake_Route_Validated_Event",
        "Task_Receive_WCS_Event",
    )
    for flow_id in ("Message_Completion", "Message_Failure", "Message_Timeout"):
        assert message_flows[flow_id][1] == "Start_Event_Intake"


def _assert_lane_geometry_and_no_overlaps(root: ET.Element) -> None:
    ids = _all_ids(root)
    bounds = _bounds_by_semantic_ref(root)
    node_to_lane: dict[str, str] = {}
    for lane in root.findall(".//bpmn:lane", NS):
        assert lane.attrib["id"] in bounds, lane.attrib["id"]
        for node_ref in lane.findall("bpmn:flowNodeRef", NS):
            node_id = (node_ref.text or "").strip()
            assert node_id not in node_to_lane, node_id
            node_to_lane[node_id] = lane.attrib["id"]

    for node_id, lane_id in node_to_lane.items():
        assert node_id in ids and node_id in bounds, node_id
        x, y, width, height = bounds[node_id]
        lane_x, lane_y, lane_width, lane_height = bounds[lane_id]
        center_x, center_y = x + width / 2, y + height / 2
        assert lane_x <= center_x <= lane_x + lane_width, (node_id, lane_id, "x")
        assert lane_y <= center_y <= lane_y + lane_height, (node_id, lane_id, "y")

    flow_node_tags = {
        "startEvent",
        "endEvent",
        "task",
        "userTask",
        "serviceTask",
        "sendTask",
        "receiveTask",
        "manualTask",
        "exclusiveGateway",
        "parallelGateway",
        "intermediateCatchEvent",
        "intermediateThrowEvent",
        "subProcess",
    }
    overlaps = []
    for process in root.findall("bpmn:process", NS):
        node_ids = [
            element.attrib["id"]
            for element in process
            if "id" in element.attrib and _local_name(element.tag) in flow_node_tags
        ]
        for index, left_id in enumerate(node_ids):
            lx, ly, lw, lh = bounds[left_id]
            for right_id in node_ids[index + 1 :]:
                rx, ry, rw, rh = bounds[right_id]
                overlap_x = min(lx + lw, rx + rw) - max(lx, rx)
                overlap_y = min(ly + lh, ry + rh) - max(ly, ry)
                if overlap_x > 0 and overlap_y > 0:
                    overlaps.append((left_id, right_id, overlap_x * overlap_y))
    assert not overlaps, overlaps


def _assert_event_validation_before_inventory(root: ET.Element) -> None:
    operations_graph, operations_starts = _graph_for_process(root, "Process_Operations")
    intake_graph, intake_starts = _graph_for_process(root, "Process_Event_Intake")
    required = {
        "Task_Intake_Lookup_Event_Context",
        "Task_Validate_WCS_Event",
        "Gateway_Event_Valid",
        "Task_Record_Invalid_Event",
        "Task_Intake_Route_Validated_Event",
        "Task_Apply_Completed",
        "Task_Commit_Inventory",
        "Task_Receive_WCS_Event",
    }
    assert required <= set(_all_ids(root)), sorted(required - set(_all_ids(root)))
    assert _dominates(
        intake_graph,
        intake_starts,
        "Task_Intake_Lookup_Event_Context",
        "Task_Intake_Route_Validated_Event",
    )
    assert _dominates(
        intake_graph,
        intake_starts,
        "Task_Validate_WCS_Event",
        "Task_Intake_Route_Validated_Event",
    )
    assert _dominates(
        intake_graph,
        intake_starts,
        "Gateway_Event_Valid",
        "Task_Intake_Route_Validated_Event",
    )
    assert _dominates(
        operations_graph,
        operations_starts,
        "Task_Apply_Completed",
        "Task_Commit_Inventory",
    )
    message_flows = {
        flow.attrib["id"]: (flow.attrib["sourceRef"], flow.attrib["targetRef"])
        for flow in root.findall(".//bpmn:messageFlow", NS)
    }
    assert message_flows.get("Message_Route_Validated_Event") == (
        "Task_Intake_Route_Validated_Event",
        "Task_Receive_WCS_Event",
    )
    assert intake_graph["Task_Record_Invalid_Event"] == {"End_Intake_Invalid"}
    invalid = _all_ids(root)["Task_Record_Invalid_Event"].attrib.get("name", "")
    assert all(token in invalid for token in ("diagnostic audit", "no state", "inventory"))


def _assert_cancellation_semantics(root: ET.Element) -> None:
    graph, starts = _graph_for_process(root, "Process_Operations")
    ids = _all_ids(root)
    required = {
        "Task_Show_PreTask_Exception",
        "End_PreTask_Exception",
        "Task_Check_Cancellation_Eligibility",
        "Gateway_Cancellation_Allowed",
        "Task_Proposed_Cancel",
    }
    assert required <= set(ids), sorted(required - set(ids))
    assert "Task_Proposed_Cancel" not in _reachable(graph, {"Task_Show_PreTask_Exception"})
    assert "End_PreTask_Exception" in _reachable(graph, {"Task_Show_PreTask_Exception"})
    assert _dominates(graph, starts, "Task_Check_Cancellation_Eligibility", "Task_Proposed_Cancel")
    assert _dominates(graph, starts, "Gateway_Cancellation_Allowed", "Task_Proposed_Cancel")
    guard = ids["Task_Check_Cancellation_Eligibility"].attrib.get("name", "")
    assert "existing task" in guard.lower()
    for state in ("CREATED", "VALIDATED", "DISPATCHED", "IN_PROGRESS", "FAILED", "TIMED_OUT"):
        assert state in guard
    assert "COMPLETED" not in guard and "CANCELLED" not in guard


def _assert_failure_escalation_order(root: ET.Element) -> None:
    graph, starts = _graph_for_process(root, "Process_Operations")
    ids = _all_ids(root)
    required = {
        "Task_Record_Initial_Failure",
        "Task_Update_Failure_Evidence",
        "Gateway_Third_Failure",
        "Task_Escalate",
        "Gateway_Eligible_Recovery",
    }
    assert required <= set(ids), sorted(required - set(ids))
    incoming = defaultdict(set)
    for source, targets in graph.items():
        for target in targets:
            incoming[target].add(source)
    assert incoming["Gateway_Third_Failure"] == {
        "Task_Record_Initial_Failure",
        "Task_Update_Failure_Evidence",
    }
    assert _dominates(graph, starts, "Gateway_Third_Failure", "Gateway_Eligible_Recovery")
    assert graph["Gateway_Third_Failure"] >= {"Task_Escalate"}
    update_name = ids["Task_Update_Failure_Evidence"].attrib.get("name", "")
    assert all(token in update_name for token in ("FAILED / TIMED_OUT", "failure evidence", "exception"))


def _assert_duplicate_event_semantics(root: ET.Element) -> None:
    graph, starts = _graph_for_process(root, "Process_Event_Intake")
    ids = _all_ids(root)
    assert graph["Task_Return_Duplicate"] == {"End_Intake_Duplicate"}
    assert _dominates(
        graph,
        starts,
        "Gateway_Duplicate_Event",
        "Task_Intake_Route_Validated_Event",
    )
    intake_text = " ".join(ids["Process_Event_Intake"].itertext()).lower()
    assert "non-terminal or terminal task" in intake_text
    assert "after the related inbound process has ended" in intake_text
    assert "without state or inventory mutation" in intake_text


def _assert_exact_state_source(text: str) -> None:
    block = _mermaid_block(text)
    found_states: set[str] = set()
    transitions: set[tuple[str, str]] = set()
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if "-->" not in line:
            continue
        expression = line.split(":", 1)[0]
        nodes = [item.strip() for item in expression.split("-->")]
        for node in nodes:
            if node != "[*]":
                assert node in EXACT_STATES, node
                found_states.add(node)
        for source, target in zip(nodes, nodes[1:]):
            if source != "[*]" and target != "[*]":
                transitions.add((source, target))
    assert found_states == EXACT_STATES
    assert transitions == ALLOWED_TRANSITIONS


def _assert_no_direct_ui_mutation_edge(text: str) -> None:
    block = _mermaid_block(text)
    forbidden = re.compile(
        r"(?mi)^\s*UI\s*[-.=]+>\s*(?:\|[^|]*\|\s*)?(DB|CONVEYOR|LIFT|ROBOT)\b"
    )
    assert not forbidden.search(block)


def _mermaid_block(text: str) -> str:
    match = re.search(r"(?ms)^```mermaid\s*\n(.*?)^```\s*$", text)
    assert match, "missing Mermaid fenced block"
    assert len(re.findall(r"(?m)^```mermaid\s*$", text)) == 1
    return match.group(1)


def test_required_diagram_sources_exist():
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in DIAGRAM_FILES if not path.is_file()]
    assert not missing, f"Missing five-source diagram contract: {missing}"


def test_every_source_has_disclosure_and_human_boundary():
    _require_sources()
    for path in MARKDOWN_FILES:
        text = _read(path)
        assert DISCLOSURE in text, path.name
        assert re.search(r"human review|human confirmation|process owner", text, re.IGNORECASE), path.name

    for path in (AS_IS, TO_BE):
        text = _read(path)
        assert DISCLOSURE in text, path.name
        assert re.search(r"human|process-owner|process owner", text, re.IGNORECASE), path.name


@pytest.mark.parametrize("path", (AS_IS, TO_BE), ids=lambda path: path.name)
def test_bpmn_xml_ids_references_process_events_and_flow_boundaries(path: Path):
    _require_sources()
    root = _parse(path)
    assert root.tag == f"{{{BPMN_NS}}}definitions"
    elements = [element for element in root.iter() if "id" in element.attrib]
    ids = [element.attrib["id"] for element in elements]
    assert len(ids) == len(set(ids)), [item for item, count in Counter(ids).items() if count > 1]
    by_id = _all_ids(root)
    parent_map = {child: parent for parent in root.iter() for child in parent}

    for element in root.iter():
        for attribute in (
            "sourceRef",
            "targetRef",
            "processRef",
            "bpmnElement",
            "attachedToRef",
            "default",
        ):
            if attribute in element.attrib:
                assert element.attrib[attribute] in by_id, (path.name, element.attrib["id"], attribute)

    processes = root.findall("bpmn:process", NS)
    assert processes
    for process in processes:
        graph, starts, ends = _process_graph(process)
        assert starts and ends, process.attrib["id"]
        reachable = _reachable(graph, starts)
        assert ends & reachable, f"{process.attrib['id']} has no reachable end"

    for flow in root.findall(".//bpmn:sequenceFlow", NS):
        source_owner = _owner_process(by_id[flow.attrib["sourceRef"]], parent_map)
        target_owner = _owner_process(by_id[flow.attrib["targetRef"]], parent_map)
        flow_owner = _owner_process(flow, parent_map)
        assert source_owner == target_owner == flow_owner, flow.attrib["id"]

    participants = {
        participant.attrib["id"]: participant.attrib["processRef"]
        for participant in root.findall(".//bpmn:participant", NS)
    }
    assert len(set(participants.values())) == len(participants.values())
    for flow in root.findall(".//bpmn:messageFlow", NS):
        source = by_id[flow.attrib["sourceRef"]]
        target = by_id[flow.attrib["targetRef"]]
        source_owner = participants.get(flow.attrib["sourceRef"]) or _owner_process(source, parent_map)
        target_owner = participants.get(flow.attrib["targetRef"]) or _owner_process(target, parent_map)
        assert source_owner and target_owner and source_owner != target_owner, flow.attrib["id"]
    _assert_lane_integrity(root)


def test_as_is_is_an_assumed_manual_baseline_with_two_explicit_outcomes():
    _require_sources()
    text = _read(AS_IS)
    required = (
        "assumed illustrative baseline",
        "process-owner validation",
        "Manual barcode / SKU / quantity check",
        "Spreadsheet / location lookup",
        "Verbal or informal device coordination",
        "Late exception discovery",
        "Manual inventory update",
        "Pallet stored",
        "Exception unresolved",
    )
    for phrase in required:
        assert phrase in text, phrase
    assert re.search(r"not observed|no observation|not based on observation", text, re.IGNORECASE)


@pytest.mark.parametrize("path", (AS_IS, TO_BE), ids=lambda path: path.name)
def test_bpmn_gateways_are_questions_with_labelled_outgoing_paths(path: Path):
    _require_sources()
    root = _parse(path)
    flows_by_source: dict[str, list[ET.Element]] = defaultdict(list)
    for flow in root.findall(".//bpmn:sequenceFlow", NS):
        flows_by_source[flow.attrib["sourceRef"]].append(flow)
    gateways = root.findall(".//bpmn:exclusiveGateway", NS)
    assert gateways
    for gateway in gateways:
        assert gateway.attrib.get("name", "").strip().endswith("?"), gateway.attrib["id"]
        outgoing = flows_by_source[gateway.attrib["id"]]
        assert len(outgoing) >= 2, gateway.attrib["id"]
        assert all(flow.attrib.get("name", "").strip() for flow in outgoing), gateway.attrib["id"]


@pytest.mark.parametrize("path", (AS_IS, TO_BE), ids=lambda path: path.name)
def test_bpmn_diagram_interchange_covers_all_nodes_and_flows(path: Path):
    _require_sources()
    root = _parse(path)
    flow_node_tags = {
        "startEvent",
        "endEvent",
        "task",
        "userTask",
        "serviceTask",
        "sendTask",
        "receiveTask",
        "manualTask",
        "exclusiveGateway",
        "parallelGateway",
        "intermediateCatchEvent",
        "intermediateThrowEvent",
    }
    node_ids = {
        element.attrib["id"]
        for process in root.findall("bpmn:process", NS)
        for element in process
        if "id" in element.attrib and _local_name(element.tag) in flow_node_tags
    }
    shape_refs = {
        element.attrib["bpmnElement"]
        for element in root.iter()
        if _local_name(element.tag) == "BPMNShape"
    }
    flow_ids = {
        flow.attrib["id"]
        for process in root.findall("bpmn:process", NS)
        for flow in process.findall("bpmn:sequenceFlow", NS)
    } | {
        flow.attrib["id"] for flow in root.findall(".//bpmn:messageFlow", NS)
    }
    edge_refs = {
        element.attrib["bpmnElement"]
        for element in root.iter()
        if _local_name(element.tag) == "BPMNEdge"
    }
    assert node_ids <= shape_refs, sorted(node_ids - shape_refs)
    assert flow_ids <= edge_refs, sorted(flow_ids - edge_refs)


@pytest.mark.parametrize("path", (AS_IS, TO_BE), ids=lambda path: path.name)
def test_bpmn_lane_geometry_has_no_outside_centers_or_positive_area_overlaps(path: Path):
    _require_sources()
    _assert_lane_geometry_and_no_overlaps(_parse(path))


@pytest.mark.parametrize("path", (AS_IS, TO_BE), ids=lambda path: path.name)
def test_bpmn_flow_edges_touch_actual_source_and_target_shape_boundaries(path: Path):
    _require_sources()
    _assert_flow_edge_endpoints_touch_shapes(_parse(path))


def test_to_be_has_exact_lanes_and_reachable_required_concepts():
    _require_sources()
    root = _parse(TO_BE)
    lanes = [lane.attrib.get("name") for lane in root.findall(".//bpmn:lane", NS)]
    assert Counter(lanes) == Counter(("Operator", "WMS", "WCS Simulator", "Maintenance"))

    text = _read(TO_BE)
    concepts = (
        "Scan / create inbound receipt",
        "Validate barcode, SKU, quantity, duplicate ID",
        "Select deterministic compatible location",
        "Create and validate movement task",
        "Dispatch simulated WCS command",
        "Execute simulated movement",
        "Apply TASK_COMPLETED",
        "Commit inventory exactly once",
        "Show exception in queue",
        "Retry 1",
        "Retry 2",
        "Third failure overall?",
        "Escalate exception; no third retry",
        "Proposed cancellation",
        "Duplicate event_id?",
        "Return duplicate success; no mutation",
    )
    for concept in concepts:
        assert concept in text, concept

    for process in root.findall("bpmn:process", NS):
        graph, starts, ends = _process_graph(process)
        reachable = _reachable(graph, starts)
        flow_node_tags = {
            "startEvent",
            "endEvent",
            "task",
            "userTask",
            "serviceTask",
            "sendTask",
            "receiveTask",
            "manualTask",
            "exclusiveGateway",
            "parallelGateway",
            "intermediateCatchEvent",
            "intermediateThrowEvent",
        }
        node_ids = {
            element.attrib["id"]
            for element in process
            if "id" in element.attrib and _local_name(element.tag) in flow_node_tags
        }
        assert node_ids <= reachable, (process.attrib["id"], sorted(node_ids - reachable))
        reverse: dict[str, set[str]] = defaultdict(set)
        for source, targets in graph.items():
            for target in targets:
                reverse[target].add(source)
        can_reach_end = _reachable(reverse, ends)
        assert node_ids <= can_reach_end, (process.attrib["id"], sorted(node_ids - can_reach_end))


def test_to_be_validates_every_unique_event_before_state_or_inventory_mutation():
    _require_sources()
    _assert_event_validation_before_inventory(_parse(TO_BE))


def test_to_be_separates_pre_task_errors_and_guards_task_cancellation():
    _require_sources()
    _assert_cancellation_semantics(_parse(TO_BE))


def test_to_be_updates_failure_then_checks_escalation_before_retry_eligibility():
    _require_sources()
    _assert_failure_escalation_order(_parse(TO_BE))


def test_to_be_duplicate_intake_continues_wait_and_handles_terminal_replay():
    _require_sources()
    _assert_duplicate_event_semantics(_parse(TO_BE))


def test_to_be_gateway_labels_are_bound_to_exact_destinations():
    _require_sources()
    _assert_exact_gateway_routes(_parse(TO_BE))


def test_to_be_event_intake_is_independent_and_accepts_terminal_replay():
    _require_sources()
    _assert_independent_event_intake_lifecycle(_parse(TO_BE))


def test_mermaid_documents_have_required_structure_and_types():
    _require_sources()
    expectations = {
        CONTEXT: ("flowchart", ("Operator UI", "WMS Demo", "SQLite contract database", "WCS Simulator", "Conveyor Simulator", "Lift Simulator", "Robot Simulator")),
        SEQUENCE: ("sequenceDiagram", ("alt Full or no compatible location", "else Compatible location available", "alt Device offline", "Retry 1", "Retry 2", "third failure", "alt Timeout", "alt Duplicate completion event")),
        STATE: ("stateDiagram-v2", tuple(EXACT_STATES)),
    }
    for path, (diagram_type, tokens) in expectations.items():
        text = _read(path)
        assert re.search(r"(?m)^# .+", text)
        for section in ("Scope and reading guide", "Business walkthrough", "Linked requirements and rules", "Assumptions and gaps", "Human review boundary"):
            assert f"## {section}" in text, (path.name, section)
        block = _mermaid_block(text)
        assert re.search(rf"(?m)^\s*{re.escape(diagram_type)}\b", block)
        for token in tokens:
            assert token in block, (path.name, token)


def test_context_enforces_wms_owned_mutation_and_simulation_boundaries():
    _require_sources()
    text = _read(CONTEXT)
    block = _mermaid_block(text)
    assert "No direct database or device mutation" in block
    assert "owns validation, task state, inventory decisions" in block
    assert "simulated command" in block
    assert "simulated device event" in block
    _assert_no_direct_ui_mutation_edge(text)


def test_sequence_covers_happy_path_and_all_explicit_exception_branches():
    _require_sources()
    block = _mermaid_block(_read(SEQUENCE))
    required = (
        "TASK_COMPLETED",
        "Commit inventory exactly once",
        "NO_AVAILABLE_LOCATION",
        "VALIDATED to FAILED",
        "failure count 1, retry count 0",
        "FAILED to DISPATCHED to FAILED",
        "Escalate on failure 3; no third retry command",
        "TIMED_OUT",
        "duplicate: true",
        "No second state or inventory mutation",
    )
    for phrase in required:
        assert phrase in block, phrase
    assert block.count("alt ") >= 4
    assert "else " in block


def test_state_diagram_uses_exact_states_and_exact_br05_transitions():
    _require_sources()
    text = _read(STATE)
    block = _mermaid_block(text)
    transitions = set(
        re.findall(
            r"(?m)^\s*(CREATED|VALIDATED|DISPATCHED|IN_PROGRESS|COMPLETED|FAILED|TIMED_OUT|CANCELLED)\s+-->\s+"
            r"(CREATED|VALIDATED|DISPATCHED|IN_PROGRESS|COMPLETED|FAILED|TIMED_OUT|CANCELLED)\s*:",
            block,
        )
    )
    assert transitions == ALLOWED_TRANSITIONS
    state_tokens = set(re.findall(r"\b[A-Z][A-Z_]+\b", block))
    allowed_non_states = {
        "TASK_ACCEPTED",
        "TASK_STARTED",
        "TASK_COMPLETED",
        "TASK_FAILED",
        "TASK_TIMEOUT",
        "CANCEL",
        "VALID",
    }
    assert state_tokens - EXACT_STATES <= allowed_non_states, sorted(state_tokens - EXACT_STATES)
    assert "COMPLETED --> [*]" in block
    assert "CANCELLED --> [*]" in block
    assert re.search(r"COMPLETED.+terminal", text, re.IGNORECASE)
    assert re.search(r"CANCELLED.+terminal", text, re.IGNORECASE)
    _assert_exact_state_source(text)


def test_state_document_has_matrix_transition_table_traceability_and_open_questions():
    _require_sources()
    text = _read(STATE)
    assert "## State × Event matrix" in text
    for marker in ("VALID", "FORBIDDEN", "N/A/UNDEFINED"):
        assert marker in text
    assert "## Transition table" in text
    for heading in ("Current state", "Event / action", "Guard", "Next state", "Effect", "Actor", "Audit evidence", "Linked rules"):
        assert heading in text
    for rule in ("BR-05", "BR-06", "BR-07", "BR-08", "BR-09"):
        assert rule in text
    questions = (
        "cancellation during physical motion",
        "late events after cancellation",
        "acknowledgement timing",
        "event ordering",
    )
    for question in questions:
        assert question in text.lower()


def test_diagram_sources_have_no_external_private_or_unsupported_material():
    _require_sources()
    text = "\n".join(_read(path) for path in DIAGRAM_FILES)
    # Namespace identifiers are part of the BPMN 2.0 XML grammar, not remote
    # renderers or linked assets.
    text = re.sub(r"http://www\.omg\.org/spec/(?:BPMN|DD|DI|DC)/[^\s\"']+", "", text)
    text = text.replace("http://www.w3.org/2001/XMLSchema-instance", "")
    banned_patterns = (
        r"(?i)https?://",
        r"(?i)github\.com",
        r"(?i)[A-Z]:\\Users\\",
        r"(?i)kakadata",
        r"(?i)kakaonline",
        r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]",
        r"(?i)\b(measured savings|measured improvement|guaranteed benefit|ROI)\b",
        r"(?i)\b(production deployed|production validated|live warehouse)\b",
        r"(?i)(mermaid\.ink|kroki|plantuml\.com|bpmn\.io)",
        r"(?i)<(?:image|script|link)\b[^>]*(?:href|src)=",
    )
    for pattern in banned_patterns:
        assert not re.search(pattern, text), pattern


def test_mutation_dangling_lane_flow_node_reference_is_rejected():
    _require_sources()
    root = ET.fromstring(_read(TO_BE))
    lane_ref = root.find(".//bpmn:lane/bpmn:flowNodeRef", NS)
    assert lane_ref is not None
    lane_ref.text = "Missing_Flow_Node"
    with pytest.raises(AssertionError):
        _assert_lane_integrity(root)


def test_mutation_completion_inventory_order_reversal_is_rejected():
    _require_sources()
    root = ET.fromstring(_read(TO_BE))
    by_id = _all_ids(root)
    by_id["Flow_Ops_Completion_To_Apply"].set("targetRef", "Task_Commit_Inventory")
    by_id["Flow_Ops_Apply_To_Commit"].set("sourceRef", "Task_Commit_Inventory")
    by_id["Flow_Ops_Apply_To_Commit"].set("targetRef", "Task_Apply_Completed")
    by_id["Flow_Ops_Commit_To_End"].set("sourceRef", "Task_Apply_Completed")
    with pytest.raises(AssertionError):
        _assert_event_validation_before_inventory(root)


def test_mutation_lowercase_extra_state_and_transition_is_rejected():
    _require_sources()
    text = _read(STATE).replace(
        "    COMPLETED --> [*]",
        "    COMPLETED --> reopened --> CREATED\n    COMPLETED --> [*]",
        1,
    )
    assert "COMPLETED --> reopened --> CREATED" in text
    with pytest.raises(AssertionError):
        _assert_exact_state_source(text)


def test_mutation_alternate_ui_to_database_arrow_is_rejected():
    _require_sources()
    text = _read(CONTEXT).replace("flowchart LR", "flowchart LR\n    UI ==> DB", 1)
    with pytest.raises(AssertionError):
        _assert_no_direct_ui_mutation_edge(text)


def test_mutation_event_validation_yes_no_branch_swap_is_rejected():
    _require_sources()
    root = ET.fromstring(_read(TO_BE))
    ids = _all_ids(root)
    invalid_name = ids["Flow_Ops_Invalid_Event"].attrib["name"]
    valid_name = ids["Flow_Ops_Valid_Event"].attrib["name"]
    ids["Flow_Ops_Invalid_Event"].set("name", valid_name)
    ids["Flow_Ops_Valid_Event"].set("name", invalid_name)
    with pytest.raises(AssertionError):
        _assert_exact_gateway_routes(root)


def test_mutation_third_failure_yes_no_branch_swap_is_rejected():
    _require_sources()
    root = ET.fromstring(_read(TO_BE))
    ids = _all_ids(root)
    yes_name = ids["Flow_Ops_Third_Yes"].attrib["name"]
    no_name = ids["Flow_Ops_Third_No"].attrib["name"]
    ids["Flow_Ops_Third_Yes"].set("name", no_name)
    ids["Flow_Ops_Third_No"].set("name", yes_name)
    with pytest.raises(AssertionError):
        _assert_exact_gateway_routes(root)


def test_mutation_event_intake_attached_to_ended_parent_is_rejected():
    _require_sources()
    root = ET.fromstring(_read(TO_BE))
    ids = _all_ids(root)
    participant = ids["Participant_Event_Intake"]
    participant.set("processRef", "Process_Operations")
    with pytest.raises(AssertionError):
        _assert_independent_event_intake_lifecycle(root)
