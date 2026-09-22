#!/usr/bin/env python3
"""
CyberGhost Linux Switcher - terminal client

Unofficial community tool. Uses the official CyberGhost Linux client only as a
live location/server directory and NetworkManager/OpenVPN for the VPN transport.

The program never reconstructs vpn.data. It changes only the "remote" entry
using nmcli's dictionary-style +/- modification and verifies that all other
vpn.data entries remain unchanged.
"""

from __future__ import annotations

import os
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

APP_NAME = "CyberGhost Linux Switcher"
NM_PROFILE = os.environ.get("CG_SWITCHER_NM_PROFILE", "CyberGhost - Dynamic")
CG_BINARY_ENV = "CYBERGHOST_BIN"
LOW_LOAD_POOL = 5

# CyberGhost regular VPN country catalog.
# Limited to countries currently listed in CyberGhost's public server directory.
# Availability is still checked live through the official Linux client.
CYBERGHOST_COUNTRIES = [
    ("AL", "Albania"),
    ("AD", "Andorra"),
    ("AT", "Austria"),
    ("BY", "Belarus"),
    ("BE", "Belgium"),
    ("BA", "Bosnia and Herzegovina"),
    ("BG", "Bulgaria"),
    ("HR", "Croatia"),
    ("CY", "Cyprus"),
    ("CZ", "Czechia"),
    ("DK", "Denmark"),
    ("EE", "Estonia"),
    ("FI", "Finland"),
    ("FR", "France"),
    ("DE", "Germany"),
    ("GR", "Greece"),
    ("HU", "Hungary"),
    ("IS", "Iceland"),
    ("IE", "Ireland"),
    ("IM", "Isle of Man"),
    ("IT", "Italy"),
    ("LV", "Latvia"),
    ("LI", "Liechtenstein"),
    ("LT", "Lithuania"),
    ("LU", "Luxembourg"),
    ("MT", "Malta"),
    ("MD", "Moldova"),
    ("MC", "Monaco"),
    ("ME", "Montenegro"),
    ("NL", "Netherlands"),
    ("MK", "North Macedonia"),
    ("NO", "Norway"),
    ("PL", "Poland"),
    ("PT", "Portugal"),
    ("RO", "Romania"),
    ("RU", "Russia"),
    ("RS", "Serbia"),
    ("SK", "Slovakia"),
    ("SI", "Slovenia"),
    ("ES", "Spain"),
    ("SE", "Sweden"),
    ("CH", "Switzerland"),
    ("TR", "Türkiye"),
    ("UA", "Ukraine"),
    ("GB", "United Kingdom"),
    ("AR", "Argentina"),
    ("BS", "Bahamas"),
    ("BO", "Bolivia"),
    ("BR", "Brazil"),
    ("CA", "Canada"),
    ("CL", "Chile"),
    ("CO", "Colombia"),
    ("CR", "Costa Rica"),
    ("DO", "Dominican Republic"),
    ("EC", "Ecuador"),
    ("GL", "Greenland"),
    ("GT", "Guatemala"),
    ("MX", "Mexico"),
    ("PA", "Panama"),
    ("PE", "Peru"),
    ("US", "United States"),
    ("UY", "Uruguay"),
    ("VE", "Venezuela"),
    ("AU", "Australia"),
    ("BD", "Bangladesh"),
    ("KH", "Cambodia"),
    ("CN", "China"),
    ("HK", "Hong Kong"),
    ("IN", "India"),
    ("ID", "Indonesia"),
    ("IR", "Iran"),
    ("JP", "Japan"),
    ("KZ", "Kazakhstan"),
    ("LA", "Laos"),
    ("MO", "Macao"),
    ("MY", "Malaysia"),
    ("MN", "Mongolia"),
    ("MM", "Myanmar"),
    ("NP", "Nepal"),
    ("NZ", "New Zealand"),
    ("PK", "Pakistan"),
    ("PH", "Philippines"),
    ("SG", "Singapore"),
    ("KR", "South Korea"),
    ("LK", "Sri Lanka"),
    ("TW", "Taiwan"),
    ("TH", "Thailand"),
    ("VN", "Vietnam"),
    ("DZ", "Algeria"),
    ("AM", "Armenia"),
    ("EG", "Egypt"),
    ("GE", "Georgia"),
    ("IL", "Israel"),
    ("KE", "Kenya"),
    ("MA", "Morocco"),
    ("NG", "Nigeria"),
    ("QA", "Qatar"),
    ("SA", "Saudi Arabia"),
    ("ZA", "South Africa"),
    ("AE", "United Arab Emirates"),
]

def run(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=timeout)

def discover_cyberghost_binary() -> Path | None:
    if value := os.environ.get(CG_BINARY_ENV):
        p = Path(value).expanduser()
        if p.is_file() and os.access(p, os.X_OK):
            return p.resolve()

    if found := shutil.which("cyberghostvpn"):
        return Path(found).resolve()

    for p in map(Path, (
        "/usr/bin/cyberghostvpn",
        "/usr/local/bin/cyberghostvpn",
        "/opt/cyberghost/cyberghostvpn",
        "/usr/local/cyberghost/cyberghostvpn",
    )):
        if p.is_file() and os.access(p, os.X_OK):
            return p.resolve()

    for root in (Path.home() / "cg-inspect", Path.home() / "Downloads"):
        if root.exists():
            for p in sorted(root.glob("cyberghostvpn-*/cyberghost/cyberghostvpn"), reverse=True):
                if p.is_file() and os.access(p, os.X_OK):
                    return p.resolve()
    return None

def parse_rows(output: str) -> list[list[str]]:
    rows = []
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        row = [x.strip() for x in line.strip("|").split("|")]
        if row and row[0].isdigit():
            rows.append(row)
    return rows

def valid_instance(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9-]+-s\d+-i\d+", value.lower()))

class Directory:
    def __init__(self, binary: Path, runtime_home: Path):
        self.binary, self.runtime_home = binary, runtime_home

    def call(self, *args: str) -> str:
        cp = run(["env", f"HOME={self.runtime_home}", str(self.binary), *args], 90)
        if cp.returncode:
            detail = "\n".join(x for x in (cp.stdout.strip(), cp.stderr.strip()) if x)
            raise RuntimeError(detail or "CyberGhost directory request failed.")
        return cp.stdout

    def cities(self, code: str) -> list[dict[str, Any]]:
        result = []
        for row in parse_rows(self.call("--country-code", code.lower())):
            if len(row) < 4:
                continue
            try:
                result.append({"name": row[1], "instances": int(row[2]),
                               "load": int(row[3].replace("%", "").strip())})
            except ValueError:
                pass
        if not result:
            raise RuntimeError("No usable cities were returned. The country may have no current "
                               "CyberGhost locations, or the directory API may have failed.")
        return result

    def servers(self, code: str, city: str) -> list[dict[str, Any]]:
        result = []
        for row in parse_rows(self.call("--country-code", code.lower(), "--city", city.lower())):
            if len(row) < 4:
                continue
            instance = row[2].lower()
            try:
                load = int(row[3].replace("%", "").strip())
            except ValueError:
                continue
            if valid_instance(instance) and 0 <= load <= 100:
                result.append({"instance": instance, "load": load})
        result.sort(key=lambda x: (x["load"], x["instance"]))
        if not result:
            raise RuntimeError(f"No usable servers returned for {city}.")
        return result

class NetworkManagerVPN:
    def __init__(self, profile: str):
        self.profile = profile

    def exists(self) -> bool:
        cp = run(["nmcli", "-t", "-f", "NAME", "connection", "show"])
        return self.profile in cp.stdout.splitlines()

    def active(self) -> bool:
        cp = run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"])
        return any(line.split(":", 1)[0] == self.profile for line in cp.stdout.splitlines())

    def disconnect(self) -> None:
        if self.active():
            cp = run(["nmcli", "connection", "down", self.profile], 30)
            if cp.returncode:
                raise RuntimeError(cp.stderr.strip() or cp.stdout.strip() or "Disconnect failed.")

    def snapshot(self) -> dict[str, str]:
        cp = run(["nmcli", "--escape", "no", "-g", "vpn.data",
                  "connection", "show", self.profile])
        if cp.returncode:
            raise RuntimeError(cp.stderr.strip() or "Could not inspect vpn.data.")
        values = {}
        for item in cp.stdout.strip().split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                values[key.strip()] = value.strip()
        return values

    def remote(self) -> str | None:
        value = self.snapshot().get("remote")
        return value.replace(r"\:", ":") if value else None

    def set_remote(self, hostname: str) -> str:
        endpoint = f"{hostname}:443"
        before = self.snapshot()
        if not before:
            raise RuntimeError("NetworkManager returned empty vpn.data.")

        cp = run(["nmcli", "connection", "modify", self.profile, "-vpn.data", "remote"], 30)
        if cp.returncode:
            raise RuntimeError(cp.stderr.strip() or cp.stdout.strip() or
                               "Could not remove old remote.")

        cp = run(["nmcli", "connection", "modify", self.profile,
                  "+vpn.data", f"remote={endpoint}"], 30)
        if cp.returncode:
            old = before.get("remote")
            if old:
                run(["nmcli", "connection", "modify", self.profile,
                     "+vpn.data", f"remote={old.replace(r'\:', ':')}"], 30)
            raise RuntimeError(cp.stderr.strip() or cp.stdout.strip() or
                               "Could not store new remote.")

        after = self.snapshot()
        stored = after.get("remote", "").replace(r"\:", ":")
        if stored != endpoint:
            raise RuntimeError(f"Remote verification failed: requested {endpoint}, stored {stored!r}.")

        protected_before = {k: v for k, v in before.items() if k != "remote"}
        protected_after = {k: v for k, v in after.items() if k != "remote"}
        if protected_before != protected_after:
            changed = sorted(k for k in set(protected_before) | set(protected_after)
                             if protected_before.get(k) != protected_after.get(k))
            raise RuntimeError("Safety check failed; non-remote vpn.data changed: " +
                               ", ".join(changed))
        return endpoint

    def connect(self) -> None:
        cp = run(["nmcli", "connection", "up", self.profile], 90)
        if cp.returncode:
            raise RuntimeError(cp.stderr.strip() or cp.stdout.strip() or
                               "Connection activation failed.")

def choose(title: str, entries: list[tuple[str, Any]]) -> Any:
    print(f"\n{title}")
    for n, (label, _) in enumerate(entries, 1):
        print(f"  {n:>3}. {label}")
    while True:
        try:
            raw = input("\nSelection (q to quit): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit(0)
        if raw.lower() in {"q", "quit", "exit"}:
            raise SystemExit(0)
        try:
            n = int(raw)
            if 1 <= n <= len(entries):
                return entries[n - 1][1]
        except ValueError:
            pass
        print("Invalid selection.")

def resolve(hostname: str) -> str:
    try:
        return socket.gethostbyname(hostname)
    except OSError:
        return "DNS lookup failed"

def public_ip() -> str:
    curl = shutil.which("curl")
    if not curl:
        return "Unavailable (curl not installed)"
    cp = run([curl, "-4", "--silent", "--show-error", "--max-time", "10",
              "https://ifconfig.me"], 15)
    return cp.stdout.strip() if cp.returncode == 0 and cp.stdout.strip() else "Unavailable"

def tunnel_info() -> tuple[str, str]:
    cp = run(["ip", "-4", "-o", "addr", "show"])
    for line in cp.stdout.splitlines():
        m = re.match(r"\d+:\s+(tun\S+).*?\binet\s+([0-9.]+)/", line)
        if m:
            return m.group(1), m.group(2)
    return "None", "None"

def main() -> int:
    print(f"\n{APP_NAME}")
    print("=" * len(APP_NAME))
    print(f"NetworkManager profile: {NM_PROFILE}")

    if not shutil.which("nmcli"):
        print("ERROR: nmcli is not installed.", file=sys.stderr)
        return 1

    binary = discover_cyberghost_binary()
    if not binary:
        print(f"ERROR: official CyberGhost client not found. Set {CG_BINARY_ENV} "
              "to its executable path.", file=sys.stderr)
        return 1

    vpn = NetworkManagerVPN(NM_PROFILE)
    if not vpn.exists():
        print(f'ERROR: NetworkManager profile "{NM_PROFILE}" does not exist.',
              file=sys.stderr)
        return 1

    runtime_home = Path(tempfile.mkdtemp(prefix=f"cg-switcher-{os.getuid()}-"))
    directory = Directory(binary, runtime_home)

    try:
        countries = [(f"{name} ({code})", (code.lower(), name))
                     for code, name in sorted(CYBERGHOST_COUNTRIES, key=lambda x: x[1])]
        code, country = choose("Country", countries)

        print(f"\nChecking current CyberGhost locations for {country}...")
        cities = directory.cities(code)
        city = choose("City", [
            (f"{c['name']} — {c['instances']} instances, {c['load']}% avg load", c)
            for c in cities
        ])

        print(f"\nLoading live servers for {city['name']}...")
        servers = directory.servers(code, city["name"])
        pool_size = min(LOW_LOAD_POOL, len(servers))
        selection = choose("Server", [
            (f"Automatic — random from {pool_size} lowest-load servers",
             {"automatic": True})
        ] + [
            (f"{s['instance']} — {s['load']}%", s) for s in servers
        ])

        server = random.choice(servers[:pool_size]) if selection.get("automatic") else selection
        instance, load = server["instance"], server["load"]
        hostname = f"{instance}.cg-dialup.net"

        print("\nSelected")
        print(f"  Instance:    {instance}")
        print(f"  Load:        {load}%")
        print(f"  Hostname:    {hostname}")
        print(f"  Endpoint IP: {resolve(hostname)}")

        answer = input("\nConnect? [Y/n]: ").strip().lower()
        if answer not in {"", "y", "yes"}:
            print("No changes made.")
            return 0

        print("\nPreparing NetworkManager profile...")
        vpn.disconnect()
        endpoint = vpn.set_remote(hostname)
        print(f"  Remote safely changed to: {endpoint}")
        print("  Non-remote vpn.data verification: OK")

        print("Connecting...")
        vpn.connect()

        dev, ip = tunnel_info()
        print("\nConnected")
        print(f"  Instance:  {instance}")
        print(f"  Remote:    {vpn.remote()}")
        print(f"  Tunnel:    {dev}")
        print(f"  Tunnel IP: {ip}")
        print(f"  Public IP: {public_ip()}")
        return 0

    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(runtime_home, ignore_errors=True)

if __name__ == "__main__":
    raise SystemExit(main())
