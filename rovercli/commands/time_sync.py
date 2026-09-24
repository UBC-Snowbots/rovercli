import getpass
import subprocess
from typing import Optional


def time_sync(remote_host: str = "rover", password: Optional[str] = None):
    print(f"Synchronizing time with remote host: {remote_host}")
    try:
        password = password if password is not None else getpass.getpass("Enter password for sudo: ")
        date_output = str(int(subprocess.check_output(["date", "-u", "+%s"]).decode().strip()) + 1)
        subprocess.run(
            ["ssh", remote_host, "sudo", "-S", "date", f"--set='@{date_output}'"],
            check=True,
            input=password.encode(),
            capture_output=True,
        )
        print("Time synchronization successful.")
    except subprocess.CalledProcessError as error:
        print(f"Time synchronization failed: {error}")