# Export As Glb Add-In

This Fusion 360 add-in exports CAD geometry to GLB files by exporting Fusion geometry to a temporary STEP file. This file is then converted to GLB using the cascadio PyPi package using an external Python interpreter (configurable).

If you are new to Fusion's app ecosystem, this project is an add-in (not a one-off script). Add-ins can stay enabled between sessions and can optionally run on startup.

## Installation

This add-in is currently **not published** to the Autodesk Marketplace. You can still install it in a few clicks using one of the options below.

Fusion loads this add-in from your local AddIns folder:

- Windows: `%AppData%\Autodesk\Autodesk Fusion 360\API\AddIns`
- macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns`

The add-in files need to end up in a subfolder named "Export As Glb" under the AddIns folder - here are some options:

### Option 1: TL;DR command lines

PowerShell (Windows):

```powershell
powershell -ExecutionPolicy Bypass -Command "iwr -UseBasicParsing https://raw.githubusercontent.com/barbatron/fusion-360-glb-export-add-in/main/install-addin.ps1 | iex"
```

Bash (macOS):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/barbatron/fusion-360-glb-export-add-in/main/install-addin.sh)"
```

Fetches and runs the install scripts. Both scripts download the latest ZIP from GitHub and extracts the files where they need to go. Hopefully.

### Option 2: Manually download ZIP from GitHub

1. Open the repository page:
  https://github.com/barbatron/fusion-360-glb-export-add-in
2. Click Code, then Download ZIP.
3. Extract or open the ZIP
4. Rename the extracted "fusion-360-glb-export-add-in-main" folder to exactly "Export As Glb".
5. Copy the "Export As Glb" folder into Fusion's AddIns folder.

### Option 3: Clone from GitHub

1. Clone the repository:

```bash
git clone https://github.com/barbatron/fusion-360-glb-export-add-in.git
```

2. If it doesn't already exist, create an empty "Export As Glb" subfolder in the Fusion 360 add-ins folder.
3. Copy the add-in's Python and manifest files into the "Export As Glb" subfolder.

### Refresh and run add-in

After placing files under AddIns, open the "Scripts and Add-Ins" dialog in Fusion. Optionally filter to add-ins only and find "Export As Glb" in the list. If the "run" switch is on, flip it off. Then flip it on again to run the add-in. You may also enable Run on Startup if desired.

When the add-in starts, it registers toolbar commands in Fusion's "Scripts and Add-Ins panel" in the Solid workspace, plus a right-click command for supported selections.

## What It Can Export

- Full design export (from toolbar command).
- Selection export (from right-click context menu) for:
  - Component occurrences
  - Components
  - Bodies

For body-only export, the add-in creates a temporary component, copies the body into it, exports that, then cleans up.

## Commands

- Export as GLB
  - Added to the Solid workspace Scripts and Add-Ins panel.
  - Exports the full design root component.

- Export Selection as GLB
  - Appears in right-click menu when a supported entity is selected.
  - Exports only the selected item.

- Configure Python for GLB exports
  - Added to the Solid workspace Scripts and Add-Ins panel.
  - Lets you choose and save the Python interpreter used for export.

## Python Interpreter and Dependencies

_**Optional setup:** most of the details below are on "auto pilot" - you are not required to take any steps before using the export command, as you ~will~ should be prompted if input is needed or if anything goes wrong. Otherwise check the text console._

The add-in requires the use of an external Python interpreter, which you may already have installed on your system.

Use the "Configure Python for GLB exports" command to select a specific Python interpreter:

- Auto-detected interpreters from PATH and common install locations.
- Optional manual path entry.
- Fusion embedded Python is labeled in the picker.

The interpreter selection will be remembered for future exports. To change or update the interpreter, re-run the configuration command. If no valid interpreter is configured when invoking the export command, the add-in prompts to configure one.

Before export proceeds, the add-in checks for required modules:

- `numpy`
- `cascadio`

If missing, the add-in will try to install them using `pip`. This may take a while but should only need to happen once.

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

## Contributions

Constructive feedback, PRs and suggestions much appreciated! I know the approach is a bit unorthodox but it works for me.
