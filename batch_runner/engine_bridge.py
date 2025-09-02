import importlib
import os
import subprocess
from typing import Optional

def run_engine_on_batch(
    batch_dir: str,
    output_dir: str,
    engine_command: Optional[str],
    engine_callable: Optional[str],
) -> int:
    """
    Run your engine on a batch directory either via a subprocess command
    or a Python callable. Returns 0 on success.
    """
    os.makedirs(output_dir, exist_ok=True)

    if engine_command:
        cmd = engine_command.format(batch=batch_dir, output=output_dir)
        print(f"[engine_bridge] Running command: {cmd}")
        return subprocess.run(cmd, shell=True).returncode

    if engine_callable:
        print(f"[engine_bridge] Importing callable: {engine_callable}")
        module_path, func_name = engine_callable.split(":")
        mod = importlib.import_module(module_path)
        fn = getattr(mod, func_name)
        ret = fn(batch_dir=batch_dir, output_dir=output_dir)
        return 0 if (ret is None or ret == 0) else int(ret)

    raise ValueError("Neither engine_command nor engine_callable is configured.")
