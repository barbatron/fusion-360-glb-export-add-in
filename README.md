# Export As Glb Add-In

This Fusion 360 add-in exports CAD geometry to GLB files by:
1. Exporting Fusion geometry to a temporary STEP file.
2. Running a selected external Python interpreter.
3. Using cascadio to convert STEP to GLB.

## Autodesk App Submission Package

Autodesk requires all product files to be submitted in a single ZIP file.

This repository includes a Makefile target that builds:
- dist/Export-As-Glb-submission.zip

From the add-in folder, run:

```bash
make package
```

On Windows, if GNU Make is not installed, run the PowerShell packager directly:

```powershell
.\package-submission.ps1
```

The package includes required files:
- Export As Glb.manifest
- Export As Glb.py

It also includes helpful supporting files:
- LICENSE
- README.md
- addon-icon.svg

Clean build artifacts:

```bash
make clean
```

## Installation

### Option 1: Autodesk App Store (recommended)

1. Open the Fusion category in Autodesk App Store:
  https://apps.autodesk.com/FUSION/en/Home/Index
2. Search for Export As Glb.
3. Install the add-in from the listing and restart Fusion if prompted.

### Option 2: Download ZIP from GitHub

1. Open the repository page:
  https://github.com/barbatron/fusion-360-glb-export-add-in
2. Click Code, then Download ZIP.
3. Extract the ZIP.
4. Copy the Export As Glb folder (the folder containing Export As Glb.manifest and Export As Glb.py) into your Fusion AddIns directory:
  - Windows: %AppData%\Autodesk\Autodesk Fusion 360\API\AddIns
  - macOS: ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns

### Option 3: Clone from GitHub

1. Clone the repository:

```bash
git clone https://github.com/barbatron/fusion-360-glb-export-add-in.git
```

2. Copy the Export As Glb folder (the folder containing Export As Glb.manifest and Export As Glb.py) into your Fusion AddIns directory:
  - Windows: %AppData%\Autodesk\Autodesk Fusion 360\API\AddIns
  - macOS: ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns

### Name Alignment Requirement

For best Fusion add-in loading reliability, keep names aligned:
1. Add-in folder name
2. Manifest filename base name
3. Python entry filename base name

Example alignment:
- Folder: Export As Glb
- Manifest: Export As Glb.manifest
- Python file: Export As Glb.py

After copying files, open Scripts and Add-Ins in Fusion, go to Add-Ins, then run and optionally enable Run on Startup.

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

Use the "Configure Export Python" command to select a specific Python interpreter:
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
  - Run Configure Export Python and choose a non-Fusion interpreter.
  - Install numpy + cascadio into that interpreter when prompted.

- Button not visible:
  - Reload the add-in and check the Solid workspace Scripts and Add-Ins panel.
