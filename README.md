# Export As Glb Add-In

This Fusion 360 add-in exports CAD geometry to GLB files by:
1. Exporting Fusion geometry to a temporary STEP file.
2. Running a selected external Python interpreter.
3. Using cascadio to convert STEP to GLB.

## What It Can Export

- Full design export (from toolbar command).
- Selection export (from right-click context menu) for:
  - Component occurrences
  - Components
  - Bodies

For body-only export, the add-in creates a temporary component, copies the body into it, exports that, then cleans up.

## Main Commands

- Export as GLB
  - Added to the Solid workspace Scripts and Add-Ins panel.
  - Exports the full design root component.

- Export Selection as GLB
  - Appears in right-click menu when a supported entity is selected.
  - Exports only the selected item.

- Configure Export Python
  - Added to the Solid workspace Scripts and Add-Ins panel.
  - Lets you choose and save the Python interpreter used for export.

## Save Path and Naming

- A Save As dialog is shown before conversion.
- Default folder remembers your last export location.
- Default filename is based on:
  - Root component name (full export), or
  - Selected component/body name (selection export).
- Invalid filename characters are sanitized automatically.

## Python Interpreter and Dependencies

The add-in stores a configured Python interpreter and reuses it on later exports.

Use Configure Export Python to choose the interpreter:
- Auto-detected interpreters from PATH and common install locations.
- Optional manual path entry.
- Fusion embedded Python is labeled in the picker.

During export, if no valid interpreter is configured, the add-in prompts to configure one.

Before export, the add-in checks for required modules:
- numpy
- cascadio

If missing, it can prompt to install them into the selected interpreter.

## Typical Usage

1. Enable the add-in in Scripts and Add-Ins.
2. (Recommended once) Run Configure Export Python and select your preferred interpreter.
3. Trigger export by either:
   - Clicking Export as GLB in the toolbar, or
   - Right-clicking a selected component/body and choosing Export Selection as GLB.
4. Choose output path in Save As.
5. Allow dependency install if prompted.

## Notes

- Enabling the add-in should only register UI; it should not start export immediately.
- GLB is used consistently as the output format.
- If command labels do not refresh after edits, toggle the add-in off/on or restart Fusion.

## Troubleshooting

- No selection export menu item:
  - Ensure exactly one supported entity is selected.

- Dependency import failures:
  - Run Configure Export Python and choose a non-Fusion interpreter.
  - Install numpy + cascadio into that interpreter when prompted.

- Button not visible:
  - Reload the add-in and check the Solid workspace Scripts and Add-Ins panel.
