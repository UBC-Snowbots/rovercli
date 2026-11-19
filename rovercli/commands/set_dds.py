"""Switch the CycloneDDS profile between the rover network and ZeroTier.

Only the <Interfaces> block of the profile is rewritten. Peers, multicast, shared memory
and tuning settings in the existing file are left untouched. Each mode pins exactly one
interface (no autodetermine, no multi-homing).

How the interface is tracked (no state is stored besides the profile itself):
- Setting (`setdds rover|zerotier|auto`): read the live interface list (`ip -j addr`) and
  pick the interface that is up with an IPv4 address in that mode's subnet (NETWORKS below).
  Its *name* (e.g. enp3s0, ztc3qyu2l6) is written into the profile as the single
  <NetworkInterface name="..."/>. Cyclone resolves the address from that name when a node
  starts, so an IP change is harmless. A different interface (new machine, new adapter)
  needs `setdds` to be run again.
- The interface is chosen based on the subnet. See NETWORKS dictionary to see which subnet corresponds to which network. 
- Reading (`setdds show`): take that interface name back out of the profile, look up its
  current IPv4 in the live interface list, and report which subnet (= mode) it is in.
  The profile is the source of truth. Nothing else (markers, cache files) is kept.
"""
from __future__ import annotations

import ipaddress
import json
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

CYCLONE_NS = "https://cdds.io/config"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

# Every rover-side machine lives in these networks. Match on address, not interface
# name: ZeroTier names differ per machine, and a machine may be on several ZT networks.
NETWORKS = {
    "rover": ipaddress.ip_network("192.168.1.0/24"),
    "zerotier": ipaddress.ip_network("172.30.0.0/24"),
}
MODES = ["rover", "zerotier", "auto", "show"]

DEFAULT_PROFILE = """<?xml version="1.0" encoding="utf-8"?>
<CycloneDDS
  xmlns="https://cdds.io/config"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd">
  <Domain Id="101">
    <General>
      <Interfaces>
        <NetworkInterface autodetermine="true" priority="0" multicast="default" />
      </Interfaces>
      <AllowMulticast>true</AllowMulticast>
      <EnableMulticastLoopback>true</EnableMulticastLoopback>
      <MaxMessageSize>65500B</MaxMessageSize>
    </General>
    <Internal>
      <SocketReceiveBufferSize min="10MB"/>
      <Watermarks>
        <WhcHigh>500kB</WhcHigh>
      </Watermarks>
    </Internal>
    <Discovery>
      <ParticipantIndex>auto</ParticipantIndex>
      <MaxAutoParticipantIndex>1000</MaxAutoParticipantIndex>
      <Peers>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
"""


def profile_path() -> Path:
    uri = os.environ.get("CYCLONEDDS_URI", "")
    if uri.startswith("file://"):
        return Path(uri[len("file://"):])
    if uri and not uri.lstrip().startswith("<"):
        return Path(uri)
    root = os.environ.get("ROVERFLAKE_ROOT", str(Path.home() / "RoverFlake2"))
    return Path(root) / "network_stuff" / "dds_profile_cyclone.xml"


def write_default_profile(path: Path) -> None:
    """Write the default (autodetermine) profile if the file is missing or empty."""
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_PROFILE)


def _interfaces() -> list[dict]:
    out = subprocess.run(["ip", "-j", "addr"], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def find_interface(network: str, ifaces: list[dict] | None = None) -> tuple[str, str] | None:
    """Return (name, ipv4) of the up interface with an address in NETWORKS[network].

    Prefers wired over wireless if several match (e.g. a home router also on 192.168.1.x).
    """
    net = NETWORKS[network]
    matches = []
    for iface in ifaces if ifaces is not None else _interfaces():
        if "UP" not in iface.get("flags", []) or "LOWER_UP" not in iface.get("flags", []):
            continue
        for addr in iface.get("addr_info", []):
            if addr.get("family") == "inet" and ipaddress.ip_address(addr["local"]) in net:
                matches.append((iface["ifname"], addr["local"]))
    if not matches:
        return None
    wired = [m for m in matches if not m[0].startswith("wl")]
    candidates = wired or matches
    if len(candidates) > 1:
        names = ", ".join(f"{n} ({a})" for n, a in candidates)
        raise RuntimeError(f"Several interfaces are on the {network} network: {names}. Pass --iface to pick one.")
    return candidates[0]


def _load(path: Path) -> ET.ElementTree:
    ET.register_namespace("", CYCLONE_NS)
    ET.register_namespace("xsi", XSI_NS)
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    return ET.parse(path, parser=parser)


def _interfaces_elem(tree: ET.ElementTree) -> ET.Element:
    elem = tree.getroot().find(f".//{{{CYCLONE_NS}}}General/{{{CYCLONE_NS}}}Interfaces")
    if elem is None:
        raise RuntimeError("Profile has no <General><Interfaces> block; fix it or delete the file and rerun.")
    return elem


def current_mode(path: Path) -> str:
    """Derive the mode from the pinned interface's current address (see module docstring)."""
    if not path.exists() or path.stat().st_size == 0:
        return "missing/empty (Cyclone defaults)"
    nics = [c for c in _interfaces_elem(_load(path)) if c.tag == f"{{{CYCLONE_NS}}}NetworkInterface"]
    if len(nics) != 1 or "name" not in nics[0].attrib:
        described = "; ".join(" ".join(f'{k}="{v}"' for k, v in n.attrib.items()) for n in nics)
        return "not pinned by setdds: " + (described or "no interfaces")

    name = nics[0].attrib["name"]
    iface = next((i for i in _interfaces() if i["ifname"] == name), None)
    if iface is None:
        return f"{name} (interface does not exist)"
    if "LOWER_UP" not in iface.get("flags", []):
        return f"{name} (not up)"
    for addr in iface.get("addr_info", []):
        if addr.get("family") != "inet":
            continue
        ip = ipaddress.ip_address(addr["local"])
        for mode, net in NETWORKS.items():
            if ip in net:
                return f"{mode} ({name} {ip})"
    return f"{name} (no address on the rover or zerotier network)"


def write_interface(path: Path, name: str) -> None:
    write_default_profile(path)
    tree = _load(path)
    interfaces = _interfaces_elem(tree)
    for child in list(interfaces):
        interfaces.remove(child)
    nic = ET.Element(f"{{{CYCLONE_NS}}}NetworkInterface", {"name": name, "priority": "0", "multicast": "default"})
    interfaces.text = "\n" + " " * 8
    nic.tail = "\n" + " " * 6
    interfaces.append(nic)
    tmp = path.with_suffix(".xml.tmp")
    tree.write(tmp, encoding="utf-8", xml_declaration=True)
    with open(tmp, "a") as f:
        f.write("\n")
    os.replace(tmp, path)


def _stop_ros2_daemon() -> None:
    if shutil.which("ros2") is None:
        return
    subprocess.run(["ros2", "daemon", "stop"], capture_output=True)


def set_dds(mode: str, iface: str | None = None) -> None:
    path = profile_path()
    if mode == "show":
        print(f"Profile: {path}")
        print(f"Mode:    {current_mode(path)}")
        return

    ifaces = _interfaces()
    if mode == "auto":
        mode = "rover" if find_interface("rover", ifaces) else "zerotier"
        print(f"auto: picked {mode}")

    if iface:
        found = next((i for i in ifaces if i["ifname"] == iface), None)
        if found is None:
            raise SystemExit(f"Interface {iface} does not exist.")
        addrs = [a["local"] for a in found.get("addr_info", []) if a.get("family") == "inet"]
        if not addrs:
            raise SystemExit(f"Interface {iface} has no IPv4 address.")
        match = (iface, addrs[0])
    else:
        try:
            match = find_interface(mode, ifaces)
        except RuntimeError as e:
            raise SystemExit(str(e))
        if match is None:
            raise SystemExit(f"No interface is up with an address in {NETWORKS[mode]} ({mode}). Is the cable/ZeroTier connected?")

    name, address = match
    write_interface(path, name)
    _stop_ros2_daemon()
    print(f"DDS set to {mode}: {name} ({address})")
    print(f"Wrote {path}")
    print("Restart running ROS nodes for this to take effect (ros2 daemon was stopped).")
