#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


# ============================================================
# Configuration
# ============================================================

APP_NAME = "CyberGhost Linux Switcher"

NM_PROFILE = os.environ.get(
    "CG_SWITCHER_NM_PROFILE",
    "CyberGhost - Dynamic",
)

CG_BINARY_ENV = "CYBERGHOST_BIN"

LOW_LOAD_POOL = 5

CACHE_DIR = Path.home() / ".cache" / "cg-switcher"
COUNTRY_CACHE_FILE = CACHE_DIR / "confirmed-countries.json"


# ============================================================
# ISO 3166-1 country catalog
#
# This is standardized country metadata, NOT a CyberGhost
# server/support list.
#
# Availability is validated live through the official
# CyberGhost Linux client.
# ============================================================

ISO_COUNTRIES = [
    ("AD", "Andorra"),
    ("AE", "United Arab Emirates"),
    ("AF", "Afghanistan"),
    ("AG", "Antigua and Barbuda"),
    ("AI", "Anguilla"),
    ("AL", "Albania"),
    ("AM", "Armenia"),
    ("AO", "Angola"),
    ("AQ", "Antarctica"),
    ("AR", "Argentina"),
    ("AS", "American Samoa"),
    ("AT", "Austria"),
    ("AU", "Australia"),
    ("AW", "Aruba"),
    ("AX", "Åland Islands"),
    ("AZ", "Azerbaijan"),
    ("BA", "Bosnia and Herzegovina"),
    ("BB", "Barbados"),
    ("BD", "Bangladesh"),
    ("BE", "Belgium"),
    ("BF", "Burkina Faso"),
    ("BG", "Bulgaria"),
    ("BH", "Bahrain"),
    ("BI", "Burundi"),
    ("BJ", "Benin"),
    ("BL", "Saint Barthélemy"),
    ("BM", "Bermuda"),
    ("BN", "Brunei"),
    ("BO", "Bolivia"),
    ("BQ", "Bonaire, Sint Eustatius and Saba"),
    ("BR", "Brazil"),
    ("BS", "Bahamas"),
    ("BT", "Bhutan"),
    ("BV", "Bouvet Island"),
    ("BW", "Botswana"),
    ("BY", "Belarus"),
    ("BZ", "Belize"),
    ("CA", "Canada"),
    ("CC", "Cocos (Keeling) Islands"),
    ("CD", "Democratic Republic of the Congo"),
    ("CF", "Central African Republic"),
    ("CG", "Republic of the Congo"),
    ("CH", "Switzerland"),
    ("CI", "Côte d'Ivoire"),
    ("CK", "Cook Islands"),
    ("CL", "Chile"),
    ("CM", "Cameroon"),
    ("CN", "China"),
    ("CO", "Colombia"),
    ("CR", "Costa Rica"),
    ("CU", "Cuba"),
    ("CV", "Cabo Verde"),
    ("CW", "Curaçao"),
    ("CX", "Christmas Island"),
    ("CY", "Cyprus"),
    ("CZ", "Czechia"),
    ("DE", "Germany"),
    ("DJ", "Djibouti"),
    ("DK", "Denmark"),
    ("DM", "Dominica"),
    ("DO", "Dominican Republic"),
    ("DZ", "Algeria"),
    ("EC", "Ecuador"),
    ("EE", "Estonia"),
    ("EG", "Egypt"),
    ("EH", "Western Sahara"),
    ("ER", "Eritrea"),
    ("ES", "Spain"),
    ("ET", "Ethiopia"),
    ("FI", "Finland"),
    ("FJ", "Fiji"),
    ("FK", "Falkland Islands"),
    ("FM", "Micronesia"),
    ("FO", "Faroe Islands"),
    ("FR", "France"),
    ("GA", "Gabon"),
    ("GB", "United Kingdom"),
    ("GD", "Grenada"),
    ("GE", "Georgia"),
    ("GF", "French Guiana"),
    ("GG", "Guernsey"),
    ("GH", "Ghana"),
    ("GI", "Gibraltar"),
    ("GL", "Greenland"),
    ("GM", "Gambia"),
    ("GN", "Guinea"),
    ("GP", "Guadeloupe"),
    ("GQ", "Equatorial Guinea"),
    ("GR", "Greece"),
    ("GS", "South Georgia and the South Sandwich Islands"),
    ("GT", "Guatemala"),
    ("GU", "Guam"),
    ("GW", "Guinea-Bissau"),
    ("GY", "Guyana"),
    ("HK", "Hong Kong"),
    ("HM", "Heard Island and McDonald Islands"),
    ("HN", "Honduras"),
    ("HR", "Croatia"),
    ("HT", "Haiti"),
    ("HU", "Hungary"),
    ("ID", "Indonesia"),
    ("IE", "Ireland"),
    ("IL", "Israel"),
    ("IM", "Isle of Man"),
    ("IN", "India"),
    ("IO", "British Indian Ocean Territory"),
    ("IQ", "Iraq"),
    ("IR", "Iran"),
    ("IS", "Iceland"),
    ("IT", "Italy"),
    ("JE", "Jersey"),
    ("JM", "Jamaica"),
    ("JO", "Jordan"),
    ("JP", "Japan"),
    ("KE", "Kenya"),
    ("KG", "Kyrgyzstan"),
    ("KH", "Cambodia"),
    ("KI", "Kiribati"),
    ("KM", "Comoros"),
    ("KN", "Saint Kitts and Nevis"),
    ("KP", "North Korea"),
    ("KR", "South Korea"),
    ("KW", "Kuwait"),
    ("KY", "Cayman Islands"),
    ("KZ", "Kazakhstan"),
    ("LA", "Laos"),
    ("LB", "Lebanon"),
    ("LC", "Saint Lucia"),
    ("LI", "Liechtenstein"),
    ("LK", "Sri Lanka"),
    ("LR", "Liberia"),
    ("LS", "Lesotho"),
    ("LT", "Lithuania"),
    ("LU", "Luxembourg"),
    ("LV", "Latvia"),
    ("LY", "Libya"),
    ("MA", "Morocco"),
    ("MC", "Monaco"),
    ("MD", "Moldova"),
    ("ME", "Montenegro"),
    ("MF", "Saint Martin"),
    ("MG", "Madagascar"),
    ("MH", "Marshall Islands"),
    ("MK", "North Macedonia"),
    ("ML", "Mali"),
    ("MM", "Myanmar"),
    ("MN", "Mongolia"),
    ("MO", "Macao"),
    ("MP", "Northern Mariana Islands"),
    ("MQ", "Martinique"),
    ("MR", "Mauritania"),
    ("MS", "Montserrat"),
    ("MT", "Malta"),
    ("MU", "Mauritius"),
    ("MV", "Maldives"),
    ("MW", "Malawi"),
    ("MX", "Mexico"),
    ("MY", "Malaysia"),
    ("MZ", "Mozambique"),
    ("NA", "Namibia"),
    ("NC", "New Caledonia"),
    ("NE", "Niger"),
    ("NF", "Norfolk Island"),
    ("NG", "Nigeria"),
    ("NI", "Nicaragua"),
    ("NL", "Netherlands"),
    ("NO", "Norway"),
    ("NP", "Nepal"),
    ("NR", "Nauru"),
    ("NU", "Niue"),
    ("NZ", "New Zealand"),
    ("OM", "Oman"),
    ("PA", "Panama"),
    ("PE", "Peru"),
    ("PF", "French Polynesia"),
    ("PG", "Papua New Guinea"),
    ("PH", "Philippines"),
    ("PK", "Pakistan"),
    ("PL", "Poland"),
    ("PM", "Saint Pierre and Miquelon"),
    ("PN", "Pitcairn"),
    ("PR", "Puerto Rico"),
    ("PS", "Palestine"),
    ("PT", "Portugal"),
    ("PW", "Palau"),
    ("PY", "Paraguay"),
    ("QA", "Qatar"),
    ("RE", "Réunion"),
    ("RO", "Romania"),
    ("RS", "Serbia"),
    ("RU", "Russia"),
    ("RW", "Rwanda"),
    ("SA", "Saudi Arabia"),
    ("SB", "Solomon Islands"),
    ("SC", "Seychelles"),
    ("SD", "Sudan"),
    ("SE", "Sweden"),
    ("SG", "Singapore"),
    ("SH", "Saint Helena, Ascension and Tristan da Cunha"),
    ("SI", "Slovenia"),
    ("SJ", "Svalbard and Jan Mayen"),
    ("SK", "Slovakia"),
    ("SL", "Sierra Leone"),
    ("SM", "San Marino"),
    ("SN", "Senegal"),
    ("SO", "Somalia"),
    ("SR", "Suriname"),
    ("SS", "South Sudan"),
    ("ST", "São Tomé and Príncipe"),
    ("SV", "El Salvador"),
    ("SX", "Sint Maarten"),
    ("SY", "Syria"),
    ("SZ", "Eswatini"),
    ("TC", "Turks and Caicos Islands"),
    ("TD", "Chad"),
    ("TF", "French Southern Territories"),
    ("TG", "Togo"),
    ("TH", "Thailand"),
    ("TJ", "Tajikistan"),
    ("TK", "Tokelau"),
    ("TL", "Timor-Leste"),
    ("TM", "Turkmenistan"),
    ("TN", "Tunisia"),
    ("TO", "Tonga"),
    ("TR", "Türkiye"),
    ("TT", "Trinidad and Tobago"),
    ("TV", "Tuvalu"),
    ("TW", "Taiwan"),
    ("TZ", "Tanzania"),
    ("UA", "Ukraine"),
    ("UG", "Uganda"),
    ("UM", "United States Minor Outlying Islands"),
    ("US", "United States"),
    ("UY", "Uruguay"),
    ("UZ", "Uzbekistan"),
    ("VA", "Vatican City"),
    ("VC", "Saint Vincent and the Grenadines"),
    ("VE", "Venezuela"),
    ("VG", "British Virgin Islands"),
    ("VI", "U.S. Virgin Islands"),
    ("VN", "Vietnam"),
    ("VU", "Vanuatu"),
    ("WF", "Wallis and Futuna"),
    ("WS", "Samoa"),
    ("YE", "Yemen"),
    ("YT", "Mayotte"),
    ("ZA", "South Africa"),
    ("ZM", "Zambia"),
    ("ZW", "Zimbabwe"),
]


# ============================================================
# Generic helpers
# ============================================================

def run_command(
    args: list[str],
    *,
    timeout: int = 60,
    check: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=check,
    )


def discover_cyberghost_binary() -> tuple[Path | None, str]:
    env_value = os.environ.get(CG_BINARY_ENV)

    if env_value:
        candidate = Path(env_value).expanduser()

        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve(), f"${CG_BINARY_ENV}"

    path_binary = shutil.which("cyberghostvpn")

    if path_binary:
        return Path(path_binary).resolve(), "PATH"

    fixed_candidates = [
        Path("/usr/bin/cyberghostvpn"),
        Path("/usr/local/bin/cyberghostvpn"),
        Path("/opt/cyberghost/cyberghostvpn"),
        Path("/usr/local/cyberghost/cyberghostvpn"),
    ]

    for candidate in fixed_candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve(), str(candidate.parent)

    search_roots = [
        Path.home() / "cg-inspect",
        Path.home() / "Downloads",
    ]

    for base in search_roots:
        if not base.exists():
            continue

        matches = sorted(
            base.glob("cyberghostvpn-*/cyberghost/cyberghostvpn"),
            reverse=True,
        )

        for candidate in matches:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate.resolve(), str(base)

    return None, "not found"


def shorten_path(path: str, max_length: int = 72) -> str:
    home = str(Path.home())

    if path.startswith(home):
        path = "~" + path[len(home):]

    if len(path) <= max_length:
        return path

    keep = max_length - 3
    left = keep // 2
    right = keep - left

    return f"{path[:left]}...{path[-right:]}"


def parse_table_rows(output: str) -> list[list[str]]:
    rows: list[list[str]] = []

    for line in output.splitlines():
        line = line.strip()

        if not line.startswith("|"):
            continue

        columns = [
            item.strip()
            for item in line.strip("|").split("|")
        ]

        if not columns:
            continue

        if columns[0].lower() in {"no.", "no", "#"}:
            continue

        if not columns[0].isdigit():
            continue

        rows.append(columns)

    return rows


def is_valid_instance_name(instance: str) -> bool:
    return bool(
        re.fullmatch(
            r"[a-z0-9-]+-s\d+-i\d+",
            instance.lower(),
        )
    )


# ============================================================
# Cache
# ============================================================

def load_country_cache() -> dict[str, Any]:
    try:
        data = json.loads(
            COUNTRY_CACHE_FILE.read_text(encoding="utf-8")
        )

        if not isinstance(data, dict):
            raise ValueError

        if not isinstance(data.get("confirmed"), dict):
            data["confirmed"] = {}

        return data

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        ValueError,
    ):
        return {
            "version": 1,
            "confirmed": {},
        }


def save_country_cache(cache: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    try:
        CACHE_DIR.chmod(0o700)
    except OSError:
        pass

    temporary = COUNTRY_CACHE_FILE.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(
            cache,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    try:
        temporary.chmod(0o600)
    except OSError:
        pass

    temporary.replace(COUNTRY_CACHE_FILE)

    try:
        COUNTRY_CACHE_FILE.chmod(0o600)
    except OSError:
        pass


def cache_confirmed_country(
    code: str,
    name: str,
    cities: list[dict[str, Any]],
) -> None:
    cache = load_country_cache()

    confirmed = cache.setdefault("confirmed", {})

    confirmed[code.upper()] = {
        "name": name,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "city_count": len(cities),
        "cities": [city["name"] for city in cities],
    }

    cache["version"] = 1

    save_country_cache(cache)


def cached_country_entry(code: str) -> dict[str, Any] | None:
    cache = load_country_cache()

    entry = cache.get(
        "confirmed",
        {},
    ).get(code.upper())

    if isinstance(entry, dict):
        return entry

    return None


# ============================================================
# CyberGhost directory
# ============================================================

class CyberGhostDirectory:
    def __init__(self, binary: Path, runtime_home: Path):
        self.binary = binary
        self.runtime_home = runtime_home

    def _command(
        self,
        *arguments: str,
        timeout: int = 90,
    ) -> subprocess.CompletedProcess:
        return run_command(
            [
                "sudo",
                "env",
                f"HOME={self.runtime_home}",
                str(self.binary),
                *arguments,
            ],
            timeout=timeout,
        )

    def get_cities(
        self,
        country_code: str,
    ) -> list[dict[str, Any]]:
        result = self._command(
            "--country-code",
            country_code.lower(),
        )

        if result.returncode != 0:
            combined = "\n".join(
                value
                for value in (
                    result.stdout.strip(),
                    result.stderr.strip(),
                )
                if value
            )

            if "JSONDecodeError" in combined:
                raise RuntimeError(
                    "CyberGhost did not return usable location "
                    "data for this country.\n\n"
                    "This may mean the country currently has no "
                    "CyberGhost traffic locations, or the "
                    "CyberGhost directory API returned an "
                    "invalid/transient response."
                )

            raise RuntimeError(
                combined
                or "CyberGhost could not validate this country."
            )

        rows = parse_table_rows(result.stdout)

        cities: list[dict[str, Any]] = []

        for row in rows:
            if len(row) < 4:
                continue

            city_name = row[1].strip()

            try:
                instance_count = int(row[2])

                load = int(
                    row[3].replace("%", "").strip()
                )

            except ValueError:
                continue

            if not city_name:
                continue

            cities.append(
                {
                    "name": city_name,
                    "instances": instance_count,
                    "load": load,
                }
            )

        if not cities:
            raise RuntimeError(
                "CyberGhost returned successfully, but no "
                "valid city rows were found."
            )

        return cities

    def get_servers(
        self,
        country_code: str,
        city: str,
    ) -> list[dict[str, Any]]:
        result = self._command(
            "--country-code",
            country_code.lower(),
            "--city",
            city.lower(),
        )

        if result.returncode != 0:
            combined = "\n".join(
                value
                for value in (
                    result.stdout.strip(),
                    result.stderr.strip(),
                )
                if value
            )

            raise RuntimeError(
                combined
                or "CyberGhost could not retrieve servers."
            )

        rows = parse_table_rows(result.stdout)

        servers: list[dict[str, Any]] = []

        # Official client output:
        #
        # | No. | City | Instance | Load |
        #
        # row[1] = City
        # row[2] = Instance
        # row[3] = Load

        for row in rows:
            if len(row) < 4:
                continue

            instance = row[2].strip().lower()

            try:
                load = int(
                    row[3].replace("%", "").strip()
                )

            except ValueError:
                continue

            if not is_valid_instance_name(instance):
                continue

            if not 0 <= load <= 100:
                continue

            servers.append(
                {
                    "instance": instance,
                    "load": load,
                }
            )

        servers.sort(
            key=lambda item: (
                item["load"],
                item["instance"],
            )
        )

        if not servers:
            raise RuntimeError(
                f"No usable server instances were returned "
                f"for {city}."
            )

        return servers


# ============================================================
# NetworkManager
# ============================================================

class NetworkManagerVPN:
    """
    NetworkManager interface.

    IMPORTANT DESIGN RULE:

    vpn.data is NEVER read, parsed, reconstructed, and written
    back as one serialized value.

    NetworkManager's vpn.data is dictionary-like and nmcli
    escapes values when serializing it. Round-tripping the
    serialized representation can corrupt values such as
    data-ciphers.

    Server changes therefore operate only on the "remote"
    dictionary entry using nmcli's +/- property modification.
    """

    def __init__(self, profile: str):
        self.profile = profile

    def profile_exists(self) -> bool:
        result = run_command(
            [
                "nmcli",
                "-t",
                "-f",
                "NAME",
                "connection",
                "show",
            ]
        )

        return self.profile in result.stdout.splitlines()

    def is_connected(self) -> bool:
        result = run_command(
            [
                "nmcli",
                "-t",
                "-f",
                "NAME,TYPE",
                "connection",
                "show",
                "--active",
            ]
        )

        for line in result.stdout.splitlines():
            if not line:
                continue

            name = line.split(":", 1)[0]

            if name == self.profile:
                return True

        return False

    def disconnect(self) -> None:
        if not self.is_connected():
            return

        result = run_command(
            [
                "nmcli",
                "connection",
                "down",
                self.profile,
            ],
            timeout=30,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or result.stdout.strip()
                or "Could not disconnect the VPN."
            )

    def _read_vpn_data_unescaped(self) -> str:
        """
        Read vpn.data for verification only.

        --escape no prevents nmcli from adding output escaping.

        The returned data is NEVER fed back to NetworkManager.
        """

        result = run_command(
            [
                "nmcli",
                "--escape",
                "no",
                "-g",
                "vpn.data",
                "connection",
                "show",
                self.profile,
            ]
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or "Could not inspect NetworkManager VPN data."
            )

        return result.stdout.strip()

    @staticmethod
    def _extract_vpn_dictionary(
        vpn_data: str,
    ) -> dict[str, str]:
        """
        Parse vpn.data for comparison only.

        Nothing returned by this function is ever serialized
        back into NetworkManager.
        """

        values: dict[str, str] = {}

        for item in vpn_data.split(","):
            item = item.strip()

            if not item or "=" not in item:
                continue

            key, value = item.split("=", 1)

            key = key.strip()
            value = value.strip()

            if key:
                values[key] = value

        return values

    def snapshot(self) -> dict[str, str]:
        return self._extract_vpn_dictionary(
            self._read_vpn_data_unescaped()
        )

    def get_current_remote(self) -> str | None:
        values = self.snapshot()

        remote = values.get("remote")

        if not remote:
            return None

        # With --escape no this should normally already be
        # host:port. Keep this tiny normalization only for
        # compatibility with differing nmcli output behavior.
        return remote.replace("\\:", ":").strip()

    def set_remote(self, hostname: str) -> str:
        """
        Change ONLY vpn.data["remote"].

        All other VPN dictionary entries remain owned by
        NetworkManager and are never rewritten by this app.
        """

        endpoint = f"{hostname}:443"

        before = self.snapshot()

        if not before:
            raise RuntimeError(
                "NetworkManager returned no VPN data for "
                f'"{self.profile}".'
            )

        # Remove only the dictionary entry named "remote".
        #
        # nmcli documents '-' on multi-valued properties as
        # removing selected items. For dictionary properties,
        # the key identifies the item.

        remove_result = run_command(
            [
                "nmcli",
                "connection",
                "modify",
                self.profile,
                "-vpn.data",
                "remote",
            ],
            timeout=30,
        )

        if remove_result.returncode != 0:
            raise RuntimeError(
                "Could not remove the old NetworkManager "
                "remote entry.\n\n"
                + (
                    remove_result.stderr.strip()
                    or remove_result.stdout.strip()
                    or "Unknown nmcli error."
                )
            )

        # Add ONLY the replacement remote entry.
        #
        # Because subprocess receives arguments directly,
        # endpoint does not pass through a shell and does not
        # require shell quoting/escaping here.

        add_result = run_command(
            [
                "nmcli",
                "connection",
                "modify",
                self.profile,
                "+vpn.data",
                f"remote={endpoint}",
            ],
            timeout=30,
        )

        if add_result.returncode != 0:
            # Attempt to restore the previous remote if the
            # add operation unexpectedly fails.

            old_remote = before.get("remote")

            if old_remote:
                old_remote = old_remote.replace("\\:", ":")

                run_command(
                    [
                        "nmcli",
                        "connection",
                        "modify",
                        self.profile,
                        "+vpn.data",
                        f"remote={old_remote}",
                    ],
                    timeout=30,
                )

            raise RuntimeError(
                "Could not store the new NetworkManager "
                "remote entry.\n\n"
                + (
                    add_result.stderr.strip()
                    or add_result.stdout.strip()
                    or "Unknown nmcli error."
                )
            )

        after = self.snapshot()

        stored_remote = after.get("remote")

        if stored_remote:
            stored_remote = stored_remote.replace("\\:", ":")

        # ----------------------------------------------------
        # Guardrail 1:
        # Requested remote must match.
        # ----------------------------------------------------

        if stored_remote != endpoint:
            raise RuntimeError(
                "NetworkManager did not store the requested "
                "remote.\n\n"
                f"Requested: {endpoint}\n"
                f"Stored: {stored_remote or '(none)'}\n\n"
                "VPN activation was not attempted."
            )

        # ----------------------------------------------------
        # Guardrail 2:
        # Every pre-existing VPN dictionary value other than
        # "remote" must be identical before and after.
        # ----------------------------------------------------

        protected_before = {
            key: value
            for key, value in before.items()
            if key != "remote"
        }

        protected_after = {
            key: value
            for key, value in after.items()
            if key != "remote"
        }

        if protected_before != protected_after:
            changed_keys = sorted(
                set(protected_before)
                | set(protected_after)
            )

            differences: list[str] = []

            for key in changed_keys:
                old_value = protected_before.get(key)
                new_value = protected_after.get(key)

                if old_value != new_value:
                    differences.append(key)

            raise RuntimeError(
                "Safety check failed: changing the VPN remote "
                "also changed other NetworkManager VPN data.\n\n"
                "Changed keys: "
                + ", ".join(differences)
                + "\n\nVPN activation was not attempted."
            )

        return endpoint

    def connect(self) -> None:
        result = run_command(
            [
                "nmcli",
                "connection",
                "up",
                self.profile,
            ],
            timeout=90,
        )

        if result.returncode != 0:
            detail = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Unknown NetworkManager error."
            )

            raise RuntimeError(
                "NetworkManager could not activate the VPN.\n\n"
                f"{detail}"
            )


# ============================================================
# Network information
# ============================================================

def resolve_hostname(hostname: str) -> str:
    try:
        return socket.gethostbyname(hostname)

    except OSError:
        return "DNS lookup failed"


def get_public_ip() -> str:
    curl = shutil.which("curl")

    if not curl:
        return "curl not installed"

    try:
        result = run_command(
            [
                curl,
                "-4",
                "--silent",
                "--show-error",
                "--max-time",
                "10",
                "https://ifconfig.me",
            ],
            timeout=15,
        )

        if result.returncode == 0:
            value = result.stdout.strip()

            if value:
                return value

    except Exception:
        pass

    return "Unavailable"


def get_tunnel_info() -> tuple[str, str]:
    try:
        addr_output = run_command(
            [
                "ip",
                "-4",
                "-o",
                "addr",
                "show",
            ]
        ).stdout

        tunnel_device = ""

        for line in addr_output.splitlines():
            match = re.match(
                r"\d+:\s+(tun\S+)",
                line,
            )

            if match:
                tunnel_device = match.group(1)
                break

        if not tunnel_device:
            return "None", "None"

        addr_output = run_command(
            [
                "ip",
                "-4",
                "-o",
                "addr",
                "show",
                "dev",
                tunnel_device,
            ]
        ).stdout

        match = re.search(
            r"\binet\s+([0-9.]+)/",
            addr_output,
        )

        tunnel_ip = (
            match.group(1)
            if match
            else "Unknown"
        )

        return tunnel_device, tunnel_ip

    except Exception:
        return "Unknown", "Unknown"


# ============================================================
# Worker
# ============================================================

class Worker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, function: Callable[[], Any]):
        super().__init__()
        self.function = function

    def run(self) -> None:
        try:
            result = self.function()
            self.finished.emit(result)

        except Exception as exc:
            self.failed.emit(str(exc))


# ============================================================
# Main GUI
# ============================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(APP_NAME)

        self.resize(760, 680)
        self.setMinimumSize(560, 520)

        self.runtime_home = Path(
            tempfile.mkdtemp(
                prefix=f"cg-switcher-{os.getuid()}-"
            )
        )

        (
            self.cg_binary,
            self.cg_binary_source,
        ) = discover_cyberghost_binary()

        self.directory: CyberGhostDirectory | None = None

        if self.cg_binary:
            self.directory = CyberGhostDirectory(
                self.cg_binary,
                self.runtime_home,
            )

        self.network = NetworkManagerVPN(NM_PROFILE)

        self.current_servers: list[dict[str, Any]] = []

        self.current_country_code: str | None = None
        self.current_country_name: str | None = None

        self.worker_thread: QThread | None = None
        self.worker: Worker | None = None

        self._build_ui()
        self._populate_countries()
        self._startup_diagnostics()
        self._refresh_connection_info()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        root = QWidget()
        scroll.setWidget(root)

        self.setCentralWidget(scroll)

        layout = QVBoxLayout(root)

        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel(APP_NAME)

        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 6)
        title_font.setBold(True)

        title.setFont(title_font)

        subtitle = QLabel(
            "Unofficial NetworkManager frontend using the "
            "official CyberGhost Linux client for live "
            "location and server data."
        )

        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Location panel

        location_frame = QFrame()
        location_frame.setFrameShape(QFrame.Shape.StyledPanel)

        location_layout = QGridLayout(location_frame)

        location_layout.setColumnStretch(1, 1)
        location_layout.setHorizontalSpacing(12)
        location_layout.setVerticalSpacing(10)

        self.country_combo = QComboBox()
        self.city_combo = QComboBox()
        self.server_combo = QComboBox()

        for combo in (
            self.country_combo,
            self.city_combo,
            self.server_combo,
        ):
            combo.setMinimumHeight(38)

            combo.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )

        self.city_combo.setEnabled(False)
        self.server_combo.setEnabled(False)

        location_layout.addWidget(QLabel("Country"), 0, 0)
        location_layout.addWidget(self.country_combo, 0, 1)

        location_layout.addWidget(QLabel("City"), 1, 0)
        location_layout.addWidget(self.city_combo, 1, 1)

        location_layout.addWidget(QLabel("Server"), 2, 0)
        location_layout.addWidget(self.server_combo, 2, 1)

        self.country_state_label = QLabel(
            "Select a country to validate it against CyberGhost."
        )

        self.country_state_label.setWordWrap(True)

        location_layout.addWidget(
            self.country_state_label,
            3,
            0,
            1,
            2,
        )

        layout.addWidget(location_frame)

        # Selected-server panel

        selected_frame = QFrame()
        selected_frame.setFrameShape(QFrame.Shape.StyledPanel)

        selected_layout = QGridLayout(selected_frame)
        selected_layout.setColumnStretch(1, 1)

        self.selected_server_value = QLabel("—")
        self.selected_load_value = QLabel("—")
        self.hostname_value = QLabel("—")
        self.endpoint_ip_value = QLabel("—")

        for label in (
            self.hostname_value,
            self.endpoint_ip_value,
        ):
            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

        selected_layout.addWidget(QLabel("Selected server"), 0, 0)
        selected_layout.addWidget(self.selected_server_value, 0, 1)

        selected_layout.addWidget(QLabel("Load"), 1, 0)
        selected_layout.addWidget(self.selected_load_value, 1, 1)

        selected_layout.addWidget(QLabel("Hostname"), 2, 0)
        selected_layout.addWidget(self.hostname_value, 2, 1)

        selected_layout.addWidget(QLabel("Endpoint IP"), 3, 0)
        selected_layout.addWidget(self.endpoint_ip_value, 3, 1)

        layout.addWidget(selected_frame)

        # Buttons

        button_layout = QHBoxLayout()

        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.refresh_button = QPushButton("Refresh")

        for button in (
            self.connect_button,
            self.disconnect_button,
            self.refresh_button,
        ):
            button.setMinimumHeight(40)

        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)
        button_layout.addWidget(self.refresh_button)

        layout.addLayout(button_layout)

        # Status panel

        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)

        status_layout = QGridLayout(status_frame)
        status_layout.setColumnStretch(1, 1)

        self.status_value = QLabel("Ready")
        self.public_ip_value = QLabel("—")
        self.tunnel_device_value = QLabel("—")
        self.tunnel_ip_value = QLabel("—")
        self.remote_value = QLabel("—")

        for label in (
            self.status_value,
            self.public_ip_value,
            self.tunnel_device_value,
            self.tunnel_ip_value,
            self.remote_value,
        ):
            label.setWordWrap(True)

            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

        status_layout.addWidget(QLabel("Status"), 0, 0)
        status_layout.addWidget(self.status_value, 0, 1)

        status_layout.addWidget(QLabel("Public IP"), 1, 0)
        status_layout.addWidget(self.public_ip_value, 1, 1)

        status_layout.addWidget(QLabel("Tunnel"), 2, 0)
        status_layout.addWidget(self.tunnel_device_value, 2, 1)

        status_layout.addWidget(QLabel("Tunnel IP"), 3, 0)
        status_layout.addWidget(self.tunnel_ip_value, 3, 1)

        status_layout.addWidget(QLabel("NM remote"), 4, 0)
        status_layout.addWidget(self.remote_value, 4, 1)

        layout.addWidget(status_frame)

        # Diagnostics

        self.diagnostics_toggle = QToolButton()

        self.diagnostics_toggle.setText(
            "Startup Diagnostics ▼"
        )

        self.diagnostics_toggle.setCheckable(True)
        self.diagnostics_toggle.setChecked(False)

        layout.addWidget(self.diagnostics_toggle)

        self.diagnostics_frame = QFrame()

        self.diagnostics_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        self.diagnostics_frame.setVisible(False)

        diagnostics_layout = QVBoxLayout(
            self.diagnostics_frame
        )

        self.diagnostics_label = QLabel()
        self.diagnostics_label.setWordWrap(True)

        self.diagnostics_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        diagnostics_layout.addWidget(self.diagnostics_label)

        layout.addWidget(self.diagnostics_frame)

        # Footer

        self.footer_label = QLabel(
            "CyberGhost Linux Switcher is an unofficial "
            "community application and is not affiliated "
            "with CyberGhost."
        )

        self.footer_label.setWordWrap(True)

        footer_font = self.footer_label.font()

        footer_font.setPointSize(
            max(
                footer_font.pointSize() - 1,
                8,
            )
        )

        self.footer_label.setFont(footer_font)

        layout.addWidget(self.footer_label)
        layout.addStretch(1)

        # Signals

        self.country_combo.currentIndexChanged.connect(
            self._country_changed
        )

        self.city_combo.currentIndexChanged.connect(
            self._city_changed
        )

        self.server_combo.currentIndexChanged.connect(
            self._server_changed
        )

        self.connect_button.clicked.connect(
            self._connect_clicked
        )

        self.disconnect_button.clicked.connect(
            self._disconnect_clicked
        )

        self.refresh_button.clicked.connect(
            self._refresh_clicked
        )

        self.diagnostics_toggle.toggled.connect(
            self._toggle_diagnostics
        )

    # --------------------------------------------------------
    # Countries
    # --------------------------------------------------------

    def _populate_countries(self) -> None:
        self.country_combo.blockSignals(True)

        self.country_combo.clear()

        self.country_combo.addItem(
            "Select a country…",
            None,
        )

        confirmed_codes = set(
            load_country_cache()
            .get("confirmed", {})
            .keys()
        )

        for code, name in sorted(
            ISO_COUNTRIES,
            key=lambda item: item[1],
        ):
            display = f"{name} ({code})"

            if code in confirmed_codes:
                display += "  ✓"

            self.country_combo.addItem(
                display,
                {
                    "code": code.lower(),
                    "name": name,
                },
            )

        self.country_combo.blockSignals(False)

    def _country_changed(self) -> None:
        data = self.country_combo.currentData()

        self.city_combo.blockSignals(True)
        self.city_combo.clear()
        self.city_combo.blockSignals(False)

        self.server_combo.blockSignals(True)
        self.server_combo.clear()
        self.server_combo.blockSignals(False)

        self.city_combo.setEnabled(False)
        self.server_combo.setEnabled(False)

        self.current_servers = []
        self.current_country_code = None
        self.current_country_name = None

        self._clear_selected_server()

        if not data:
            self.country_state_label.setText(
                "Select a country to validate it against "
                "CyberGhost."
            )
            return

        if not self.directory:
            self.country_state_label.setText(
                "CyberGhost client not available."
            )
            return

        code = data["code"]
        name = data["name"]

        self.current_country_code = code
        self.current_country_name = name

        cached = cached_country_entry(code)

        if cached:
            validated = cached.get(
                "validated_at",
                "unknown",
            )

            self.country_state_label.setText(
                f"{name} was previously confirmed as a "
                "CyberGhost location.\n"
                f"Last successful validation: {validated}\n"
                "Checking current availability…"
            )

        else:
            self.country_state_label.setText(
                f"Checking CyberGhost availability for {name}…"
            )

        self._set_busy(
            True,
            f"Validating {name}…",
        )

        self._start_worker(
            lambda: self.directory.get_cities(code),
            self._cities_loaded,
            self._country_validation_failed,
        )

    def _cities_loaded(
        self,
        cities: list[dict[str, Any]],
    ) -> None:
        self._set_busy(False)

        if (
            not self.current_country_code
            or not self.current_country_name
        ):
            return

        cache_confirmed_country(
            self.current_country_code,
            self.current_country_name,
            cities,
        )

        self.country_state_label.setText(
            f"✓ {self.current_country_name} is currently "
            f"available through CyberGhost "
            f"({len(cities)} cities)."
        )

        self.city_combo.blockSignals(True)

        self.city_combo.clear()

        self.city_combo.addItem(
            "Select a city…",
            None,
        )

        for city in cities:
            display = (
                f"{city['name']} — "
                f"{city['instances']} instances, "
                f"{city['load']}% avg load"
            )

            self.city_combo.addItem(
                display,
                city,
            )

        self.city_combo.blockSignals(False)

        self.city_combo.setEnabled(True)

        self.status_value.setText(
            "Country validated"
        )

        current_code = self.current_country_code.upper()

        for index in range(self.country_combo.count()):
            item = self.country_combo.itemData(index)

            if not isinstance(item, dict):
                continue

            if item.get("code", "").upper() != current_code:
                continue

            self.country_combo.setItemText(
                index,
                f"{item['name']} ({current_code})  ✓",
            )

            break

    def _country_validation_failed(
        self,
        message: str,
    ) -> None:
        self._set_busy(False)

        name = self.current_country_name or "This country"

        cached = None

        if self.current_country_code:
            cached = cached_country_entry(
                self.current_country_code
            )

        if cached:
            self.country_state_label.setText(
                f"⚠ Current validation failed for {name}.\n"
                "A previous successful validation remains "
                "cached, but it is not being treated as "
                "current availability."
            )

        else:
            self.country_state_label.setText(
                f"⚠ CyberGhost could not validate {name}.\n"
                "This may mean there are currently no "
                "CyberGhost traffic locations for this "
                "country, or the directory API returned "
                "an error."
            )

        self.status_value.setText(
            "Country validation failed"
        )

        QMessageBox.warning(
            self,
            "Country unavailable",
            (
                f"{name} could not be validated.\n\n"
                f"{message}\n\n"
                "The application will not permanently mark "
                "this country as unsupported."
            ),
        )

    # --------------------------------------------------------
    # City/server loading
    # --------------------------------------------------------

    def _city_changed(self) -> None:
        city = self.city_combo.currentData()

        self.server_combo.blockSignals(True)
        self.server_combo.clear()
        self.server_combo.blockSignals(False)

        self.server_combo.setEnabled(False)

        self.current_servers = []

        self._clear_selected_server()

        if (
            not city
            or not self.current_country_code
            or not self.directory
        ):
            return

        city_name = city["name"]
        code = self.current_country_code

        self._set_busy(
            True,
            f"Loading servers for {city_name}…",
        )

        self._start_worker(
            lambda: self.directory.get_servers(
                code,
                city_name,
            ),
            self._servers_loaded,
            self._operation_failed,
        )

    def _servers_loaded(
        self,
        servers: list[dict[str, Any]],
    ) -> None:
        self._set_busy(False)

        self.current_servers = servers

        self.server_combo.blockSignals(True)

        self.server_combo.clear()

        pool_size = min(
            LOW_LOAD_POOL,
            len(servers),
        )

        self.server_combo.addItem(
            (
                "Automatic — random from "
                f"{pool_size} lowest-load servers"
            ),
            {
                "automatic": True,
            },
        )

        for server in servers:
            self.server_combo.addItem(
                (
                    f"{server['instance']} — "
                    f"{server['load']}%"
                ),
                {
                    "automatic": False,
                    **server,
                },
            )

        self.server_combo.blockSignals(False)

        self.server_combo.setEnabled(True)

        self.status_value.setText(
            f"Loaded {len(servers)} servers"
        )

        self._server_changed()

    # --------------------------------------------------------
    # Server selection
    # --------------------------------------------------------

    def _selected_server(
        self,
    ) -> dict[str, Any] | None:
        data = self.server_combo.currentData()

        if not data:
            return None

        if data.get("automatic"):
            if not self.current_servers:
                return None

            pool = self.current_servers[
                :min(
                    LOW_LOAD_POOL,
                    len(self.current_servers),
                )
            ]

            return random.choice(pool)

        return data

    def _server_changed(self) -> None:
        data = self.server_combo.currentData()

        if not data:
            self._clear_selected_server()
            return

        if data.get("automatic"):
            if not self.current_servers:
                self._clear_selected_server()
                return

            pool = self.current_servers[
                :min(
                    LOW_LOAD_POOL,
                    len(self.current_servers),
                )
            ]

            best_load = pool[0]["load"]

            self.selected_server_value.setText(
                "Automatic — random from "
                f"{len(pool)} lowest-load servers"
            )

            self.selected_load_value.setText(
                f"Best current load: {best_load}%"
            )

            self.hostname_value.setText(
                "Chosen when Connect is pressed"
            )

            self.endpoint_ip_value.setText("—")

            return

        instance = data["instance"]
        load = data["load"]

        hostname = f"{instance}.cg-dialup.net"

        self.selected_server_value.setText(instance)
        self.selected_load_value.setText(f"{load}%")
        self.hostname_value.setText(hostname)

        self.endpoint_ip_value.setText(
            resolve_hostname(hostname)
        )

    def _clear_selected_server(self) -> None:
        self.selected_server_value.setText("—")
        self.selected_load_value.setText("—")
        self.hostname_value.setText("—")
        self.endpoint_ip_value.setText("—")

    # --------------------------------------------------------
    # Connect
    # --------------------------------------------------------

    def _connect_clicked(self) -> None:
        server = self._selected_server()

        if not server:
            QMessageBox.warning(
                self,
                "No server selected",
                (
                    "Select a valid country, city, "
                    "and server before connecting."
                ),
            )
            return

        instance = server["instance"]
        load = server["load"]

        if not is_valid_instance_name(instance):
            QMessageBox.critical(
                self,
                APP_NAME,
                (
                    "CyberGhost returned an invalid server "
                    "instance name:\n\n"
                    f"{instance}\n\n"
                    "The NetworkManager profile was not "
                    "modified."
                ),
            )
            return

        hostname = f"{instance}.cg-dialup.net"

        endpoint_ip = resolve_hostname(hostname)

        self.selected_server_value.setText(instance)
        self.selected_load_value.setText(f"{load}%")
        self.hostname_value.setText(hostname)
        self.endpoint_ip_value.setText(endpoint_ip)

        self._set_busy(
            True,
            f"Connecting to {instance}…",
        )

        def operation() -> dict[str, str]:
            if not self.network.profile_exists():
                raise RuntimeError(
                    f'NetworkManager profile "{NM_PROFILE}" '
                    "does not exist."
                )

            self.network.disconnect()

            endpoint = self.network.set_remote(hostname)

            self.network.connect()

            tunnel_device, tunnel_ip = get_tunnel_info()

            public_ip = get_public_ip()

            return {
                "instance": instance,
                "endpoint": endpoint,
                "public_ip": public_ip,
                "tunnel_device": tunnel_device,
                "tunnel_ip": tunnel_ip,
            }

        self._start_worker(
            operation,
            self._connection_complete,
            self._operation_failed,
        )

    def _connection_complete(
        self,
        info: dict[str, str],
    ) -> None:
        self._set_busy(False)

        self.status_value.setText(
            f"Connected — {info['instance']}"
        )

        self.public_ip_value.setText(
            info["public_ip"]
        )

        self.tunnel_device_value.setText(
            info["tunnel_device"]
        )

        self.tunnel_ip_value.setText(
            info["tunnel_ip"]
        )

        self.remote_value.setText(
            info["endpoint"]
        )

    # --------------------------------------------------------
    # Disconnect
    # --------------------------------------------------------

    def _disconnect_clicked(self) -> None:
        self._set_busy(
            True,
            "Disconnecting…",
        )

        self._start_worker(
            self.network.disconnect,
            self._disconnect_complete,
            self._operation_failed,
        )

    def _disconnect_complete(
        self,
        _result: Any,
    ) -> None:
        self._set_busy(False)

        self.status_value.setText(
            "Disconnected"
        )

        self._refresh_connection_info()

    # --------------------------------------------------------
    # Refresh
    # --------------------------------------------------------

    def _refresh_clicked(self) -> None:
        city_data = self.city_combo.currentData()

        if (
            city_data
            and self.current_country_code
            and self.directory
        ):
            city_name = city_data["name"]
            code = self.current_country_code

            self._set_busy(
                True,
                f"Refreshing servers for {city_name}…",
            )

            self._start_worker(
                lambda: self.directory.get_servers(
                    code,
                    city_name,
                ),
                self._servers_loaded,
                self._operation_failed,
            )

            return

        country_data = self.country_combo.currentData()

        if country_data and self.directory:
            code = country_data["code"]

            self._set_busy(
                True,
                f"Revalidating {country_data['name']}…",
            )

            self._start_worker(
                lambda: self.directory.get_cities(code),
                self._cities_loaded,
                self._country_validation_failed,
            )

            return

        self._refresh_connection_info()

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    def _refresh_connection_info(self) -> None:
        try:
            connected = self.network.is_connected()

            self.status_value.setText(
                "Connected"
                if connected
                else "Disconnected"
            )

            remote = None

            if self.network.profile_exists():
                remote = self.network.get_current_remote()

            self.remote_value.setText(
                remote or "—"
            )

            tunnel_device, tunnel_ip = get_tunnel_info()

            self.tunnel_device_value.setText(
                tunnel_device
            )

            self.tunnel_ip_value.setText(
                tunnel_ip
            )

            self.public_ip_value.setText(
                get_public_ip()
            )

        except Exception as exc:
            self.status_value.setText(
                f"Status error: {exc}"
            )

    # --------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------

    def _startup_diagnostics(self) -> None:
        lines: list[str] = []
        failed = False

        if self.cg_binary:
            lines.append(
                "✓ CyberGhost client: "
                f"{shorten_path(str(self.cg_binary))}"
            )

            lines.append(
                "  Discovery source: "
                f"{self.cg_binary_source}"
            )

        else:
            failed = True

            lines.append(
                "✗ CyberGhost client: not found"
            )

            lines.append(
                f"  Set {CG_BINARY_ENV} if the official "
                "client is installed in a non-standard "
                "location."
            )

        if shutil.which("nmcli"):
            lines.append(
                "✓ NetworkManager/nmcli: available"
            )
        else:
            failed = True
            lines.append(
                "✗ NetworkManager/nmcli: not found"
            )

        try:
            if self.network.profile_exists():
                lines.append(
                    f"✓ VPN profile: {NM_PROFILE}"
                )

                try:
                    remote = self.network.get_current_remote()

                    lines.append(
                        "✓ Current remote: "
                        f"{remote or '(none)'}"
                    )

                except Exception as exc:
                    lines.append(
                        "⚠ Could not read current remote: "
                        f"{exc}"
                    )

            else:
                failed = True

                lines.append(
                    f"✗ VPN profile not found: {NM_PROFILE}"
                )

        except Exception as exc:
            failed = True

            lines.append(
                "✗ VPN profile check failed: "
                f"{exc}"
            )

        if shutil.which("curl"):
            lines.append(
                "✓ curl: available"
            )
        else:
            lines.append(
                "⚠ curl: not found; public-IP display "
                "will be unavailable"
            )

        lines.append(
            "✓ Country catalog: ISO 3166-1"
        )

        confirmed_count = len(
            load_country_cache()
            .get("confirmed", {})
        )

        lines.append(
            "✓ Confirmed-country cache: "
            f"{confirmed_count} successful validation(s)"
        )

        lines.append(
            "  Cache: "
            f"{shorten_path(str(COUNTRY_CACHE_FILE))}"
        )

        lines.append(
            "✓ Safe NM mutation: remote entry only"
        )

        lines.append(
            "✓ VPN-data guardrail: non-remote keys verified"
        )

        lines.append(
            "✓ Runtime HOME: "
            f"{shorten_path(str(self.runtime_home))}"
        )

        self.diagnostics_label.setText(
            "\n".join(lines)
        )

        if failed:
            self.diagnostics_toggle.setChecked(True)

    def _toggle_diagnostics(
        self,
        checked: bool,
    ) -> None:
        self.diagnostics_frame.setVisible(checked)

        self.diagnostics_toggle.setText(
            "Startup Diagnostics ▲"
            if checked
            else "Startup Diagnostics ▼"
        )

    # --------------------------------------------------------
    # Workers
    # --------------------------------------------------------

    def _start_worker(
        self,
        function: Callable[[], Any],
        success_callback: Callable[[Any], None],
        error_callback: Callable[[str], None],
    ) -> None:
        if (
            self.worker_thread
            and self.worker_thread.isRunning()
        ):
            return

        thread = QThread(self)
        worker = Worker(function)

        worker.moveToThread(thread)

        thread.started.connect(worker.run)

        worker.finished.connect(success_callback)
        worker.failed.connect(error_callback)

        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)

        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)

        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._worker_finished)

        self.worker_thread = thread
        self.worker = worker

        thread.start()

    def _worker_finished(self) -> None:
        self.worker_thread = None
        self.worker = None

    def _operation_failed(
        self,
        message: str,
    ) -> None:
        self._set_busy(False)

        self.status_value.setText(
            "Operation failed"
        )

        QMessageBox.critical(
            self,
            APP_NAME,
            message,
        )

        self._refresh_connection_info()

    # --------------------------------------------------------
    # Busy state
    # --------------------------------------------------------

    def _set_busy(
        self,
        busy: bool,
        message: str | None = None,
    ) -> None:
        self.country_combo.setEnabled(not busy)

        self.city_combo.setEnabled(
            not busy
            and self.city_combo.count() > 0
        )

        self.server_combo.setEnabled(
            not busy
            and self.server_combo.count() > 0
        )

        self.connect_button.setEnabled(not busy)
        self.disconnect_button.setEnabled(not busy)
        self.refresh_button.setEnabled(not busy)

        if busy and message:
            self.status_value.setText(message)

    # --------------------------------------------------------
    # Shutdown
    # --------------------------------------------------------

    def closeEvent(self, event) -> None:
        # Intentionally leave an active VPN connected.
        # NetworkManager owns the connection independently
        # from the GUI.

        try:
            shutil.rmtree(
                self.runtime_home,
                ignore_errors=True,
            )
        except Exception:
            pass

        event.accept()


# ============================================================
# Entry point
# ============================================================

def main() -> int:
    app = QApplication(sys.argv)

    app.setApplicationName(APP_NAME)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
