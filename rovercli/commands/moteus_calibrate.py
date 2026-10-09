import json
import os
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import yaml


DEFAULT_CALIBRATION_FILE = (
    Path(__file__).resolve().parent.parent.parent / "motor_config" / "calibration.yaml"
)
CALIBRATION_LOG_FILE = DEFAULT_CALIBRATION_FILE.with_name("calibration_log.yaml")
TARGET_ID_PATTERN = re.compile(r"Target:\s*DeviceAddress\(can_id=(\d+)\b")
REPORT_PATTERN = re.compile(r"^REPORT:\s*(moteus-cal-[^/\\]+\.log)\s*$")


def _write_calibration_log(log: dict) -> None:
    CALIBRATION_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=CALIBRATION_LOG_FILE.parent,
        delete=False,
    )
    temporary_path = Path(temporary_file.name)
    try:
        with temporary_file:
            yaml.safe_dump(log, temporary_file, sort_keys=False)
        temporary_path.replace(CALIBRATION_LOG_FILE)
    finally:
        temporary_path.unlink(missing_ok=True)


def _run_calibration(target_id: int, command: list[str], log: dict) -> None:
    record: dict[str, object] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "parameters": command[4:],
        "output": None,
    }
    log[target_id] = record
    _write_calibration_log(log)
    report_path: Optional[Path] = None
    report_directory = Path.cwd()
    try:
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env={**os.environ, "MOTEUS_CAL_DIR": str(report_directory)},
        ) as process:
            assert process.stdout is not None
            try:
                for line in process.stdout:
                    match = REPORT_PATTERN.fullmatch(line.strip())
                    if match:
                        report_path = report_directory / match.group(1)
                    print(line, end="", flush=True)
                return_code = process.wait()
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
                raise
        record["return_code"] = return_code
        record["status"] = "success" if return_code == 0 else "failed"
        if return_code == 0 and report_path is None:
            raise RuntimeError(f"No calibration REPORT filename found for target {target_id}")
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)
    except (OSError, RuntimeError) as error:
        record["status"] = "failed"
        record["error"] = str(error)
        raise
    except KeyboardInterrupt:
        record["status"] = "interrupted"
        raise
    finally:
        try:
            if report_path is not None:
                with report_path.open(encoding="utf-8") as report_file:
                    report = json.load(report_file)
                if not isinstance(report, dict):
                    raise ValueError(f"Expected a JSON object in calibration report {report_path}")
                record["output"] = report
        except (OSError, ValueError) as error:
            record["status"] = "failed"
            record["error"] = str(error)
            raise
        finally:
            record["finished_at"] = datetime.now(timezone.utc).isoformat()
            _write_calibration_log(log)
        if report_path is not None:
            report_path.unlink()


def get_available_moteus_ids() -> set[int]:
    result = subprocess.run(
        ["moteus_tool", "--info"],
        check=True,
        capture_output=True,
        text=True,
    )
    return {int(match.group(1)) for match in TARGET_ID_PATTERN.finditer(result.stdout)}


def calibrate(calibration_path: Optional[Path] = None) -> None:
    calibration_path = calibration_path or DEFAULT_CALIBRATION_FILE
    with calibration_path.open(encoding="utf-8") as calibration_file:
        calibrations = yaml.safe_load(calibration_file)

    if not isinstance(calibrations, dict) or not calibrations:
        raise ValueError(f"Expected a non-empty target mapping in {calibration_path}")

    available_ids = get_available_moteus_ids()
    if not available_ids:
        print("No moteus controllers found by moteus_tool --info.")
        return

    log = {}
    if CALIBRATION_LOG_FILE.exists():
        with CALIBRATION_LOG_FILE.open(encoding="utf-8") as log_file:
            log = yaml.safe_load(log_file)
        if not isinstance(log, dict):
            raise ValueError(f"Expected a target mapping in {CALIBRATION_LOG_FILE}")

    for target, parameters in calibrations.items():
        if isinstance(target, bool) or not isinstance(target, (str, int)):
            raise ValueError(f"Invalid moteus target in {calibration_path}: {target!r}")
        if not isinstance(parameters, list) or not all(
            isinstance(parameter, str) for parameter in parameters
        ):
            raise ValueError(
                f"Expected a list of parameter strings for target {target!r} "
                f"in {calibration_path}"
            )

        try:
            target_id = int(target)
        except ValueError as error:
            raise ValueError(
                f"Moteus target must be a CAN ID in {calibration_path}: {target!r}"
            ) from error

        if target_id not in available_ids:
            print(f"Skipping unavailable moteus target {target_id}.")
            continue

        _run_calibration(
            target_id,
            [
                "moteus_tool",
                "--calibrate",
                "--target",
                str(target_id),
                *(argument for parameter in parameters for argument in shlex.split(parameter)),
            ],
            log,
        )
