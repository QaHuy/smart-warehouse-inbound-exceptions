# Evidence assets

The PNG files in this folder are reproducible screenshots of the local-only static prototype. They contain synthetic demo identifiers only.

- `01-inbound-workbench.png`: initial operator workbench and explicit simulation disclosure.
- `02-happy-path-inventory.png`: successful completion with exactly-once inventory evidence.
- `03-offline-escalation.png`: device-offline retry limit and escalated exception.
- `04-duplicate-event.png`: duplicate-event replay with one committed movement.

Reproduce while the local prototype server is running:

```powershell
chrome.exe --headless --disable-gpu --hide-scrollbars --window-size=1440,1200 --screenshot=<output.png> <local-url>
```
