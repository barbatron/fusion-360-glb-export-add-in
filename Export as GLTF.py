import adsk.core, adsk.fusion
import os
import shutil
import subprocess
import sys
import traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        exportMgr = design.exportManager
        
        # Define paths
        temp_dir = os.path.expanduser("~") 
        step_path = os.path.join(temp_dir, "fusion_export.step")
        
        # 1. Export locally to native STEP format
        stepOptions = exportMgr.createSTEPExportOptions(step_path, design.rootComponent)
        exportMgr.execute(stepOptions)
        
        app.log(f"STEP file exported to: {step_path}")

        system_python_code = f"""
import cascadio
import os

step_file = r"{step_path}"
glb_file = os.path.join(r"{temp_dir}", "vr_ready_model.glb")

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
        python_candidates = [
            "F:\\choco-install\\bin\\python3.13.exe",
            shutil.which("python3.13"),
            shutil.which("python"),
            sys.executable,
        ]
        python_executable = next((p for p in python_candidates if p and os.path.exists(p)), None)
        if not python_executable:
            ui.messageBox(
                "Could not find a valid Python executable for subprocess. "
                "Set python_executable to a real path (for example: C:\\Python313\\python.exe)."
            )
            return

        # Validate required modules in the same interpreter before conversion.
        preflight = subprocess.run(
            [python_executable, "-c", "import numpy; import cascadio; print('dependency_check_ok')"],
            capture_output=True,
            text=True
        )
        if preflight.returncode != 0:
            install_cmd = f'"{python_executable}" -m pip install numpy cascadio'
            err = preflight.stderr.strip() if preflight.stderr else "(no stderr)"
            ui.messageBox(
                "Required Python modules are missing for the subprocess interpreter.\n\n"
                f"Interpreter: {python_executable}\n"
                f"Run this command:\n{install_cmd}\n\n"
                f"Preflight stderr:\n{err}"
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
            glb_file = os.path.join(temp_dir, "vr_ready_model.glb")
            details = stdout_text.strip() if stdout_text else "(no stdout)"
            ui.messageBox(f'Process completed - see if {glb_file} exists\n\nstdout:\n{details}')
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
