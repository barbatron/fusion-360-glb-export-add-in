import adsk.core, adsk.fusion
import os
import shutil
import subprocess
import sys
import tempfile
import traceback

ATTR_GROUP = "ExportAsGLTF"
ATTR_LAST_DIR = "lastExportDir"
MIN_PYTHON = (3, 10)


def _safe_file_stem(name):
    if not name:
        return "fusion_model"

    invalid = '<>:"/\\|?*'
    cleaned = "".join("_" if c in invalid else c for c in name).strip()
    return cleaned or "fusion_model"


def _discover_python_executable():
    candidates = []
    for cmd in ("python", "python3"):
        resolved = shutil.which(cmd)
        if resolved and resolved not in candidates:
            candidates.append(resolved)

    if sys.executable and sys.executable not in candidates:
        candidates.append(sys.executable)

    for exe in candidates:
        try:
            probe = subprocess.run(
                [exe, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            continue

        if probe.returncode != 0:
            continue

        version_text = (probe.stdout or "").strip()
        parts = version_text.split(".")
        if len(parts) < 2:
            continue

        try:
            major = int(parts[0])
            minor = int(parts[1])
        except ValueError:
            continue

        if (major, minor) >= MIN_PYTHON:
            return exe, f"{major}.{minor}"

    return None, None

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        exportMgr = design.exportManager

        root_name = design.rootComponent.name if design and design.rootComponent else "fusion_model"
        default_stem = _safe_file_stem(root_name)

        last_dir_attr = app.attributes.itemByName(ATTR_GROUP, ATTR_LAST_DIR)
        default_dir = os.path.expanduser("~")
        if last_dir_attr and os.path.isdir(last_dir_attr.value):
            default_dir = last_dir_attr.value

        file_dialog = ui.createFileDialog()
        file_dialog.title = "Save GLB As"
        file_dialog.filter = "glTF Binary (*.glb)"
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
            app.attributes.add(ATTR_GROUP, ATTR_LAST_DIR, out_dir)
        
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

        # Resolve a system Python executable for running external packages.
        python_executable, python_version = _discover_python_executable()
        if not python_executable:
            ui.messageBox(
                "Could not find a suitable Python interpreter (3.10+). "
                "Install Python 3.10+ and ensure 'python' is on PATH."
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
            
    except Exception as e:
        # Write the error message to the TEXT COMMANDS window.
        app.log(f'Failed:\n{traceback.format_exc()}')
        if ui:
            ui.messageBox(f'Fusion script failed:\n{str(e)}')
