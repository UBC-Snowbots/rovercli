import re
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from .moteus_calibrate import get_available_moteus_ids
from .moteus_save_config import CONFIG_FOLDER


def load_config(name: str = "unnamed"):
    file_pattern = re.compile(rf"config_(?P<can_id>\d+)_{re.escape(name)}\.txt")
    config_files = {
        match.group("can_id"): path
        for path in sorted(CONFIG_FOLDER.glob(f"config_*_{name}.txt"))
        if (match := file_pattern.fullmatch(path.name))
    }
    if not config_files:
        raise FileNotFoundError(
            f"No configuration files matching config_<can_id>_{name}.txt found in {CONFIG_FOLDER}"
        )

    available_ids = get_available_moteus_ids()
    for can_id, config_file in config_files.items():
        if int(can_id) not in available_ids:
            print(f"Skipping unavailable moteus target {can_id}.")
            continue

        # Strip the "Target:" header that save_config keeps, since
        # moteus_tool --restore-config cannot parse it.
        config_lines = [
            line
            for line in config_file.read_text(encoding="utf-8").splitlines()
            if not line.startswith("Target:")
        ]
        with NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        ) as temporary_file:
            temporary_file.write("\n".join(config_lines) + "\n")
            temporary_path = Path(temporary_file.name)
        try:
            print(f"Restoring {config_file.name} to moteus target {can_id}")
            subprocess.run(
                ["moteus_tool", "--target", can_id, "--restore-config", str(temporary_path), "--can-disable-brs"],
                check=True,
            )
        finally:
            temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    load_config()
