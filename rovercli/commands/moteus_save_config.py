import subprocess
from pathlib import Path
import re


CONFIG_FOLDER = Path(__file__).resolve().parent.parent.parent / "motor_config"

def save_config(name: str = "unnamed"):
    CONFIG_FOLDER.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["moteus_tool", "--dump-config"],
        check=True,
        capture_output=True,
        text=True,
    )

    output = result.stdout

    target_pattern = re.compile(
        r"(?ms)^Target:.*?\bcan_id=(?P<can_id>\d+)\b.*?(?=^Target:|\Z)"
    )
    targets = list(target_pattern.finditer(output))
    if not targets:
        raise ValueError("No target blocks with can_id values found in moteus config output")

    for target in targets:
        can_id = target.group("can_id")
        target_path = CONFIG_FOLDER / f"config_{can_id}_{name}.txt"
        target_path.write_text(target.group().rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    save_config()
