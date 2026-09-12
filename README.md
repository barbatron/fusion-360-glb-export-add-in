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

## Save Path and Naming

- A Save As dialog is shown before conversion.
- Default folder remembers your last export location.
- Default filename is based on:
  - Root component name (full export), or
  - Selected component/body name (selection export).
- Invalid filename characters are sanitized automatically.

## Python Interpreter and Dependencies

The add-in lets you choose a Python interpreter each run:
- Auto-detected interpreters from PATH and common install locations.
- Optional manual path entry.
- Fusion embedded Python is labeled in the picker.

Before export, the add-in checks for required modules:
- numpy
- cascadio

If missing, it can prompt to install them into the selected interpreter.

## Typical Usage

1. Enable the add-in in Scripts and Add-Ins.
2. Trigger export by either:
   - Clicking Export as GLB in the toolbar, or
   - Right-clicking a selected component/body and choosing Export Selection as GLB.
3. Choose output path in Save As.
4. Choose Python interpreter.
5. Allow dependency install if prompted.

## Notes

- Enabling the add-in should only register UI; it should not start export immediately.
- GLB is used consistently as the output format.
- If command labels do not refresh after edits, toggle the add-in off/on or restart Fusion.

## Troubleshooting

- No selection export menu item:
  - Ensure exactly one supported entity is selected.

- Dependency import failures:
  - Choose a non-Fusion interpreter and install numpy + cascadio there.

- Button not visible:
  - Reload the add-in and check the Solid workspace Scripts and Add-Ins panel.
