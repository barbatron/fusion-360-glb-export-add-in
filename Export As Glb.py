import adsk.core, adsk.fusion
import os
import shutil
import subprocess
import sys
import tempfile
import traceback

ATTR_GROUP = "ExportAsGLTF"
ATTR_LAST_DIR = "lastExportDir"
ATTR_LAST_PYTHON = "lastPythonExecutable"
MIN_PYTHON = (3, 10)

CMD_ID = "ExportAsGLTFCommand"
CMD_NAME = "Export as GLB"
CMD_DESCRIPTION = "Export current design to GLB using cascadio"
WORKSPACE_ID = "FusionSolidEnvironment"
PANEL_ID = "SolidScriptsAddinsPanel"

handlers = []


def _safe_file_stem(name):
    if not name:
        return "fusion_model"

    invalid = '<>:"/\\|?*'
    cleaned = "".join("_" if c in invalid else c for c in name).strip()
    return cleaned or "fusion_model"


def _is_fusion_python(exe_path):
    norm = os.path.normcase(exe_path or "")
    return "autodesk" in norm and "webdeploy" in norm


def _probe_python_version(exe):
    probe_cmd = [exe, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"]
    base = os.path.basename(exe).lower()
    if base == "py.exe" or base == "py":
        probe_cmd = [exe, "-3", "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"]

    probe = subprocess.run(
        probe_cmd,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if probe.returncode != 0:
        return None

    version_text = (probe.stdout or "").strip()
    parts = version_text.split(".")
    if len(parts) < 2:
        return None

    try:
        major = int(parts[0])
        minor = int(parts[1])
    except ValueError:
        return None

    return major, minor


def _find_common_python_paths():
    found = []

    def _add(path):
        if path and os.path.isfile(path) and path not in found:
            found.append(path)

    # Typical per-user and system Python installs.
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        py_root = os.path.join(local_app_data, "Programs", "Python")
        if os.path.isdir(py_root):
            for entry in os.listdir(py_root):
                _add(os.path.join(py_root, entry, "python.exe"))

    for env_var in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env_var)
        if not base:
            continue
        py_root = os.path.join(base, "Python")
        if os.path.isdir(py_root):
            for entry in os.listdir(py_root):
                _add(os.path.join(py_root, entry, "python.exe"))

    # Conda envs (base and named envs).
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        _add(os.path.join(user_profile, "anaconda3", "python.exe"))
        _add(os.path.join(user_profile, "miniconda3", "python.exe"))
        for conda_base in ("anaconda3", "miniconda3"):
            envs_dir = os.path.join(user_profile, conda_base, "envs")
            if os.path.isdir(envs_dir):
                for env_name in os.listdir(envs_dir):
                    _add(os.path.join(envs_dir, env_name, "python.exe"))

    # Parse Python launcher registry view for installed interpreters.
    py_launcher = shutil.which("py")
    if py_launcher:
        try:
            py_list = subprocess.run(
                [py_launcher, "-0p"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if py_list.returncode == 0:
                for raw in (py_list.stdout or "").splitlines():
                    line = raw.strip()
                    if not line:
                        continue
                    # Typical format: -V:3.13 * C:\Path\to\python.exe
                    if " " in line:
                        maybe_path = line.split()[-1].strip()
                        maybe_path = maybe_path.strip('"')
                        _add(maybe_path)
        except Exception:
            pass

    return found


def _discover_python_candidates():
    candidates = []
    for cmd in ("python", "python3", "py"):
        resolved = shutil.which(cmd)
        if resolved and resolved not in candidates:
            candidates.append(resolved)

    for exe in _find_common_python_paths():
        if exe not in candidates:
            candidates.append(exe)

    if sys.executable and sys.executable not in candidates:
        candidates.append(sys.executable)

    discovered = []
    for exe in candidates:
        try:
            version_tuple = _probe_python_version(exe)
        except Exception:
            continue

        if not version_tuple:
            continue

        major, minor = version_tuple

        if (major, minor) >= MIN_PYTHON:
            discovered.append({
                "exe": exe,
                "version": f"{major}.{minor}",
                "is_fusion": _is_fusion_python(exe),
            })

    discovered.sort(key=lambda item: (item["is_fusion"], item["exe"].lower()))
    return discovered


def _select_python_executable(ui, design, candidates):
    if not candidates:
        candidates = []

    last_py_attr = design.attributes.itemByName(ATTR_GROUP, ATTR_LAST_PYTHON)
    last_py = last_py_attr.value if last_py_attr else None

    default_index = 1
    if last_py:
        for idx, item in enumerate(candidates, start=1):
            if os.path.normcase(item["exe"]) == os.path.normcase(last_py):
                default_index = idx
                break

    lines = [
        "Choose Python interpreter for conversion (enter number):",
        "",
    ]
    for idx, item in enumerate(candidates, start=1):
        tag = " [Fusion embedded Python]" if item["is_fusion"] else ""
        lines.append(f"{idx}. {item['exe']} (Python {item['version']}){tag}")

    manual_index = len(candidates) + 1
    lines.append(f"{manual_index}. Specify path manually")
    lines.append("")
    lines.append("Tip: Prefer a non-Fusion interpreter for pip-managed packages.")

    user_input, cancelled = ui.inputBox(
        "\n".join(lines),
        "Select Python Interpreter",
        str(default_index),
    )
    if cancelled:
        return None, None

    try:
        selected_index = int((user_input or "").strip())
    except ValueError:
        ui.messageBox("Invalid selection. Please run again and enter a number from the list.")
        return None, None

    if selected_index == manual_index:
        manual_default = last_py if last_py else "C:\\Python313\\python.exe"
        manual_path, manual_cancelled = ui.inputBox(
            "Enter full path to python executable:",
            "Manual Python Path",
            manual_default,
        )
        if manual_cancelled:
            return None, None

        chosen = (manual_path or "").strip().strip('"')
        if not chosen:
            ui.messageBox("No path entered. Please run again and enter a Python executable path.")
            return None, None
        if not os.path.isfile(chosen):
            ui.messageBox(f"File not found:\n{chosen}")
            return None, None

        try:
            version_tuple = _probe_python_version(chosen)
        except Exception as ex:
            ui.messageBox(f"Failed to probe Python interpreter:\n{str(ex)}")
            return None, None

        if not version_tuple:
            ui.messageBox(
                "The selected file could not be used as a Python interpreter.\n"
                "Please choose a valid python executable."
            )
            return None, None

        if version_tuple < MIN_PYTHON:
            ui.messageBox(
                f"Python {version_tuple[0]}.{version_tuple[1]} is too old. "
                f"Please choose Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer."
            )
            return None, None

        design.attributes.add(ATTR_GROUP, ATTR_LAST_PYTHON, chosen)
        return chosen, f"{version_tuple[0]}.{version_tuple[1]}"

    if selected_index < 1 or selected_index > len(candidates):
        ui.messageBox("Selection out of range. Please run again and choose a listed number.")
        return None, None

    selected = candidates[selected_index - 1]
    design.attributes.add(ATTR_GROUP, ATTR_LAST_PYTHON, selected["exe"])
    return selected["exe"], selected["version"]


def execute_export(ui, app, design):
    exportMgr = design.exportManager

    root_name = design.rootComponent.name if design and design.rootComponent else "fusion_model"
    default_stem = _safe_file_stem(root_name)

    last_dir_attr = design.attributes.itemByName(ATTR_GROUP, ATTR_LAST_DIR)
    default_dir = os.path.expanduser("~")
    if last_dir_attr and os.path.isdir(last_dir_attr.value):
        default_dir = last_dir_attr.value

    file_dialog = ui.createFileDialog()
    file_dialog.title = "Save GLB As"
    file_dialog.filter = "GLB Files (*.glb)"
    file_dialog.initialDirectory = default_dir
    file_dialog.initialFilename = f"{default_stem}.glb"

    dlg_result = file_dialog.showSave()
    if dlg_result != adsk.core.DialogResults.DialogOK:
        return

    glb_path = file_dialog.filename
    if not glb_path.lower().endswith(".glb"):
        glb_path += ".glb"

    out_dir = os.path.dirname(glb_path)
    if out_dir and os.path.isdir(out_dir):
        design.attributes.add(ATTR_GROUP, ATTR_LAST_DIR, out_dir)

    # Define paths
    step_name = f"{os.path.splitext(os.path.basename(glb_path))[0]}.step"
    step_path = os.path.join(tempfile.gettempdir(), step_name)

    # 1. Export locally to native STEP format
    stepOptions = exportMgr.createSTEPExportOptions(step_path, design.rootComponent)
    exportMgr.execute(stepOptions)

    app.log(f"STEP file exported to: {step_path}")

    system_python_code = f"""
import cascadio

step_file = r"{step_path}"
glb_file = r"{glb_path}"

try:
    # Convert STEP -> GLB locally using system environment
    rc = cascadio.step_to_glb(step_file, glb_file)
    if rc != 0:
        raise RuntimeError(f"cascadio.step_to_glb returned non-zero code: {{rc}}")
    print(f"GLB conversion completed: {{glb_file}}")
except Exception as e:
    print(f"System Subprocess Exception: {{str(e)}}")
"""

    # Resolve and select a Python executable for running external packages.
    py_candidates = _discover_python_candidates()
    python_executable, python_version = _select_python_executable(ui, design, py_candidates)
    if not python_executable:
        ui.messageBox(
            "No Python interpreter selected.\n\n"
            "Install Python 3.10+ and ensure it is on PATH if the list was empty."
        )
        return
    app.log(f"Using Python interpreter: {python_executable} (version {python_version})")

    # Validate required modules in the same interpreter before conversion.
    preflight = subprocess.run(
        [python_executable, "-c", "import numpy; import cascadio; print('dependency_check_ok')"],
        capture_output=True,
        text=True
    )
    if preflight.returncode != 0:
        install_cmd = f'"{python_executable}" -m pip install numpy cascadio'
        err = preflight.stderr.strip() if preflight.stderr else "(no stderr)"
        ask = ui.messageBox(
            "Required Python modules are missing for the selected interpreter.\n\n"
            f"Interpreter: {python_executable}\n"
            f"Version: {python_version}\n\n"
            "Install numpy and cascadio into this interpreter now?",
            "Install Python Dependencies",
            adsk.core.MessageBoxButtonTypes.YesNoButtonType,
            adsk.core.MessageBoxIconTypes.QuestionIconType,
        )
        if ask != adsk.core.DialogResults.DialogYes:
            ui.messageBox(
                "Dependency install skipped.\n\n"
                f"Run this command manually:\n{install_cmd}\n\n"
                f"Preflight stderr:\n{err}"
            )
            return

        install = subprocess.run(
            [python_executable, "-m", "pip", "install", "numpy", "cascadio"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if install.returncode != 0:
            install_err = install.stderr.strip() if install.stderr else "(no stderr)"
            ui.messageBox(
                "Automatic dependency install failed.\n\n"
                f"Command:\n{install_cmd}\n\n"
                f"stderr:\n{install_err}"
            )
            return

        verify = subprocess.run(
            [python_executable, "-c", "import numpy; import cascadio; print('dependency_check_ok')"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if verify.returncode != 0:
            verify_err = verify.stderr.strip() if verify.stderr else "(no stderr)"
            ui.messageBox(
                "Dependencies still failed to import after install.\n\n"
                f"Interpreter: {python_executable}\n\n"
                f"stderr:\n{verify_err}"
            )
            return

    # Launch the system background process without blocking Fusion
    process = subprocess.Popen(
        [python_executable, "-c", system_python_code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # We give it a quick status window confirmation
    app.log('Handoff script sent to system Python background process.')

    try:
        stdout_text, stderr_text = process.communicate(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout_text, stderr_text = process.communicate()
        out = stdout_text.strip() if stdout_text else "(no stdout)"
        err = stderr_text.strip() if stderr_text else "(no stderr)"
        ui.messageBox(
            f'Process timed out after 8 seconds.\n\nInterpreter:\n{python_executable}\n\nstdout:\n{out}\n\nstderr:\n{err}'
        )
        return

    proc_result = process.returncode
    if proc_result == 0:
        details = stdout_text.strip() if stdout_text else "(no stdout)"
        ui.messageBox(f'Process completed - see if {glb_path} exists\n\nstdout:\n{details}')
    else:
        out = stdout_text.strip() if stdout_text else "(no stdout)"
        err = stderr_text.strip() if stderr_text else "(no stderr)"
        ui.messageBox(
            f'Process terminated with exit code {proc_result}.\n\nInterpreter:\n{python_executable}\n\nstdout:\n{out}\n\nstderr:\n{err}'
        )


class _CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            design = app.activeProduct
            if not design:
                ui.messageBox("No active design found.")
                return
            execute_export(ui, app, design)
        except Exception:
            if ui:
                ui.messageBox(f'Export as GLB failed:\n{traceback.format_exc()}')


class _CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            on_execute = _CommandExecuteHandler()
            cmd.execute.add(on_execute)
            handlers.append(on_execute)
        except Exception:
            app = adsk.core.Application.get()
            if app:
                app.log(f'Command creation failed:\n{traceback.format_exc()}')


def start(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_DESCRIPTION)

        on_created = _CommandCreatedHandler()
        cmd_def.commandCreated.add(on_created)
        handlers.append(on_created)

        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID) if workspace else None
        if not panel:
            panel = ui.allToolbarPanels.itemById(PANEL_ID)

        if panel:
            control = panel.controls.itemById(CMD_ID)
            if not control:
                control = panel.controls.addCommand(cmd_def)
                control.isPromoted = True
        else:
            ui.messageBox("Could not find target toolbar panel for Export as GLB add-in.")
    except Exception:
        if ui:
            ui.messageBox(f'Add-in start failed:\n{traceback.format_exc()}')


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID) if workspace else None
        if not panel:
            panel = ui.allToolbarPanels.itemById(PANEL_ID)

        if panel:
            control = panel.controls.itemById(CMD_ID)
            if control:
                control.deleteMe()

        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()

        handlers.clear()
    except Exception:
        if ui:
            ui.messageBox(f'Add-in stop failed:\n{traceback.format_exc()}')


def run(context):
    # For add-ins, enabling should register commands/UI only.
    start(context)
