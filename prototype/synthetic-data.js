const clone = (value) => structuredClone(value);

const DEFAULT_STATE = {
  clockStart: "2026-01-01T00:00:00Z",
  clockStepSeconds: 10,
  defaultDeviceId: "DEV-DEMO-CONV",
  skus: [
    { id: "SKU-DEMO-A", barcode: "SKU-A-001", name: "Demo ambient item A", active: true, compatibilityKey: "AMBIENT" },
    { id: "SKU-DEMO-B", barcode: "SKU-B-001", name: "Demo ambient item B", active: true, compatibilityKey: "AMBIENT" },
    { id: "SKU-DEMO-C", barcode: "SKU-C-001", name: "Demo chilled item C", active: false, compatibilityKey: "CHILLED" },
  ],
  locations: [
    { id: "LOC-DEMO-A01", code: "A01", zonePriority: 1, compatibilityKey: "AMBIENT", capacity: 2, used: 0 },
    { id: "LOC-DEMO-A02", code: "A02", zonePriority: 1, compatibilityKey: "AMBIENT", capacity: 1, used: 0 },
    { id: "LOC-DEMO-B01", code: "B01", zonePriority: 2, compatibilityKey: "AMBIENT", capacity: 2, used: 0 },
    { id: "LOC-DEMO-C01", code: "C01", zonePriority: 3, compatibilityKey: "CHILLED", capacity: 1, used: 0 },
  ],
  devices: [
    { id: "DEV-DEMO-CONV", name: "Synthetic conveyor", type: "conveyor", status: "online" },
    { id: "DEV-DEMO-LIFT", name: "Synthetic lift", type: "lift", status: "online" },
    { id: "DEV-DEMO-ROBOT", name: "Synthetic robot", type: "robot", status: "offline" },
  ],
  pallets: [],
  tasks: [],
  commands: [],
  events: [],
  inventoryMovements: [],
  exceptions: [],
  audit: [],
};

export function createSyntheticState(overrides = {}) {
  const state = clone(DEFAULT_STATE);
  for (const [key, value] of Object.entries(overrides)) {
    if (key !== "deviceStatus") state[key] = clone(value);
  }
  if (overrides.deviceStatus) {
    const device = state.devices.find((item) => item.id === state.defaultDeviceId);
    if (device) device.status = overrides.deviceStatus;
  }
  return state;
}
