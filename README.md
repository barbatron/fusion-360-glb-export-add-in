# Export As Glb Add-In

This Fusion 360 add-in exports CAD geometry to GLB files by:
1. Exporting Fusion geometry to a temporary STEP file.
2. Running a selected external Python interpreter.
3. Using cascadio to convert STEP to GLB.

If you are new to Fusion's app ecosystem, this project is an add-in (not a one-off script). Add-ins can stay enabled between sessions and can optionally run on startup.

Fusion loads this add-in from your local AddIns folder:
- Windows: %AppData%\Autodesk\Autodesk Fusion 360\API\AddIns
- macOS: ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns

## Installation

This add-in is not currently published to the Autodesk Marketplace. You can still install it in a few clicks using one of the options below.

### One-liner install scripts

PowerShell (Windows):

```powershell
powershell -ExecutionPolicy Bypass -Command "iwr -UseBasicParsing https://raw.githubusercontent.com/barbatron/fusion-360-glb-export-add-in/main/install-addin.ps1 | iex"
```

Bash (macOS):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/barbatron/fusion-360-glb-export-add-in/main/install-addin.sh)"
```

Both scripts download the latest ZIP from GitHub and install the add-in into the Fusion AddIns directory under the correct folder name: Export As Glb.

### Option 1: Download ZIP from GitHub

1. Open the repository page:
  https://github.com/barbatron/fusion-360-glb-export-add-in
2. Click Code, then Download ZIP.
3. Extract the ZIP.
4. Copy the Export As Glb folder (the folder containing Export As Glb.manifest and Export As Glb.py) into your Fusion AddIns directory:
  - Windows: %AppData%\Autodesk\Autodesk Fusion 360\API\AddIns
  - macOS: ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns

### Option 2: Clone from GitHub

1. Clone the repository:

```bash
git clone https://github.com/barbatron/fusion-360-glb-export-add-in.git
```

2. Copy the Export As Glb folder (the folder containing Export As Glb.manifest and Export As Glb.py) into your Fusion AddIns directory:
  - Windows: %AppData%\Autodesk\Autodesk Fusion 360\API\AddIns
  - macOS: ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns

NOTE: The .manifest and .py files should end up in this subdirectory under AddIns/: Autodesk/Autodesk Fusion 360/API/AddIns/Export As Glb/

After placing files under AddIns, open Scripts and Add-Ins in Fusion, find Export As Glb under the Add-Ins tab, enable Run, and optionally enable Run on Startup.

When running, the add-in registers toolbar commands in the Solid workspace Scripts and Add-Ins panel, plus a right-click command for supported selections.

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

- Configure Python for GLB exports
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

Use the "Configure Python for GLB exports" command to select a specific Python interpreter:
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
2. (Recommended once) Run Configure Python for GLB exports and select your preferred interpreter.
   - If you are not sure whether Python is installed, check first:
     - Windows (PowerShell): py -3 --version (or python --version)
     - macOS (Terminal): python3 --version
   - If the command is not found, install Python 3.10+ from [Python's official download page](https://www.python.org/downloads/).
3. Trigger export by either:
   - Clicking Export as GLB in the toolbar, or
   - Right-clicking a selected component/body and choosing Export Selection as GLB.
4. Choose output path in Save As.
5. Allow dependency install if prompted.

## Why external interpreter is used

Fusion won't keep external dependencies installed into its own Python environment.

Vendoring `numpy` and `cascadio` into the add-in was considered but I opted out of this approach due to higher maintenance overhead and native binary compatibility caveats across Fusion/Python/platform updates. For me, this setup works fine at the cost of a slightly slower export and subprocess windows popping up. Suggestions and ideas for improvements are very welcome!

## Troubleshooting

- No selection export menu item:
  - Ensure exactly one supported entity is selected.

- Dependency import failures:
  - Run Configure Python for GLB exports and choose a non-Fusion interpreter.
  - Install numpy + cascadio into that interpreter when prompted.

- Button not visible:
  - Reload the add-in and check the Solid workspace Scripts and Add-Ins panel.
