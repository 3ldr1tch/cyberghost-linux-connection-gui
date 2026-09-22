# CyberGhost Linux Switcher

An **unofficial community frontend** for selecting CyberGhost countries, cities, and individual VPN servers on Linux.

The project uses the official CyberGhost Linux client as a **live server-directory source** and uses **NetworkManager/OpenVPN** for the actual VPN connection. It is intended for Linux users who want convenient city/server selection without relying on CyberGhost's graphical client.

> This project is not affiliated with, endorsed by, or maintained by CyberGhost. CyberGhost is a trademark of its respective owner.

## Features

- Country and city selection
- Live CyberGhost server enumeration
- Individual server selection with current load
- Automatic selection from the five lowest-load valid servers
- Exact `*.cg-dialup.net` server targeting
- NetworkManager/OpenVPN transport
- Terminal client and PySide6 GUI
- Public IP, tunnel IP, hostname, and endpoint information
- Defensive validation of CyberGhost instance names and load values
- Safe NetworkManager mutation that changes **only** `vpn.data["remote"]`

## Requirements

You need:

- Linux
- Python 3
- NetworkManager and `nmcli`
- NetworkManager OpenVPN support
- OpenVPN
- `curl` for public-IP display
- A valid CyberGhost account
- The official CyberGhost Linux client, authenticated/setup
- An existing working CyberGhost NetworkManager OpenVPN profile
- PySide6 only if using the GUI

The project does **not** include or redistribute CyberGhost's client, credentials, certificates, private keys, or OpenVPN configuration.

### Arch / Garuda

A typical package set is:

```text
networkmanager
networkmanager-openvpn
openvpn
curl
python
pyside6
```

Install these using your normal Arch package-management workflow.

Other distributions use different package names; look for NetworkManager's OpenVPN plugin, OpenVPN, Python 3, curl, and PySide6.

## Setup

### 1. Install and set up CyberGhost's official Linux client

Download the official Linux client directly from CyberGhost and complete its normal account/device setup.

This project intentionally does not implement CyberGhost authentication.

### 2. Create a working NetworkManager CyberGhost profile

Import or create a CyberGhost OpenVPN connection in NetworkManager and verify that it connects normally before using this project.

The default profile name expected by the switcher is:

```text
CyberGhost - Dynamic
```

You can use a different profile without editing the program:

```text
CG_SWITCHER_NM_PROFILE="My CyberGhost VPN" ./cg-switcher.py
```

The same environment variable works with the GUI.

### 3. Make the scripts executable

```text
chmod +x cg-switcher.py
chmod +x cg-switcher-gui.py
```

### 4. CyberGhost binary discovery

The switcher looks for `cyberghostvpn` in:

1. `CYBERGHOST_BIN`
2. `$PATH`
3. `/usr/bin`
4. `/usr/local/bin`
5. `/opt/cyberghost`
6. `/usr/local/cyberghost`
7. CyberGhost extraction directories under `~/cg-inspect`
8. Matching downloads under `~/Downloads`

For a nonstandard location:

```text
CYBERGHOST_BIN="/path/to/cyberghostvpn" ./cg-switcher.py
```

## Terminal usage

Run:

```text
./cg-switcher.py
```

The terminal workflow is:

```text
Country
   ↓
live CyberGhost city query
   ↓
City
   ↓
live CyberGhost server query
   ↓
Automatic or exact server
   ↓
NetworkManager remote change
   ↓
OpenVPN connection
```

Automatic mode randomly selects one server from the five currently lowest-load valid servers. Loads outside `0–100%` and malformed instance names are ignored.

## GUI usage

Run:

```text
./cg-switcher-gui.py
```

Select a country, city, and either **Automatic** or an exact server, then press **Connect**.

Closing the GUI does not intentionally disconnect an already active NetworkManager VPN connection.

## Architecture

CyberGhost Linux Switcher deliberately separates server discovery from VPN transport.

### Server directory

The official CyberGhost Linux executable is invoked to obtain live location/server information. The switcher parses its country/city/server tables.

Directory queries run unprivileged as the current user. The switcher supplies its temporary runtime `HOME` to the official client but does not use `sudo` for country, city, or server discovery.

The application does not reimplement CyberGhost account authentication or directly maintain CyberGhost account tokens.

### VPN transport

NetworkManager and its OpenVPN plugin own the actual VPN connection.

The switcher reuses an already configured NetworkManager profile and changes only its `remote` VPN-data dictionary entry.

An instance such as:

```text
dallas-s409-i10
```

maps to:

```text
dallas-s409-i10.cg-dialup.net:443
```

### Why `vpn.data` is not reconstructed

`nmcli` serializes and escapes NetworkManager dictionary properties. Reading the entire serialized `vpn.data` value and writing it back can compound escaping. Values such as:

```text
AES-256-GCM\:AES-128-GCM\:AES-256-CBC
```

can consequently become corrupted.

The current implementation therefore uses NetworkManager's multi-value property operations:

```text
-vpn.data remote
+vpn.data remote=<hostname>:443
```

It then takes before/after snapshots and verifies that every non-`remote` VPN-data entry remains unchanged. If that safety check fails, VPN activation is not attempted.

## Security model

The switcher follows several intentional boundaries:

- It does not ask for or store your CyberGhost password.
- It does not implement CyberGhost authentication.
- It does not package CyberGhost's executable.
- It does not package certificates, private keys, `.ovpn` files, JWTs, or account/device secrets.
- It does not need to read your private-key contents.
- NetworkManager remains responsible for VPN credentials and activation.
- The official CyberGhost client remains responsible for CyberGhost account/device access.
- A temporary runtime `HOME` is used when querying the official client and is removed when the process exits.
- Server instance names must match the expected CyberGhost instance format.
- Reported server loads outside `0–100` are rejected.
- The application changes only the NetworkManager `remote` dictionary entry and verifies that other VPN-data keys were not changed.

CyberGhost location/server discovery runs as the current user and does not invoke the official CyberGhost executable with `sudo`. NetworkManager remains responsible for VPN activation and for any authorization required by the system's NetworkManager/Polkit configuration.

## Country availability

The country selector uses a local ISO 3166-1 catalog. It is **not** a hardcoded list of CyberGhost-supported countries.

Selecting a country causes the official CyberGhost client to query current availability. A failed query is not permanently interpreted as proof that a country is unsupported because API/transient failures can produce similar errors.

The GUI may cache previous successful country validations for convenience, but cached validation is not treated as proof of current availability.

## Troubleshooting

### `CyberGhost client not found`

Set its path explicitly:

```text
CYBERGHOST_BIN="/full/path/to/cyberghostvpn" ./cg-switcher.py
```

Make sure the executable has execute permission.

### NetworkManager profile not found

List profiles:

```text
nmcli connection show
```

Either name the working profile `CyberGhost - Dynamic` or set:

```text
CG_SWITCHER_NM_PROFILE="Your Profile Name"
```

### `Connection activation failed: Unknown reason`

NetworkManager often puts the useful OpenVPN error in its journal:

```text
sudo journalctl -u NetworkManager --since '-2 minutes' --no-pager | tail -100
```

You can also manually test the profile:

```text
nmcli connection up 'CyberGhost - Dynamic'
```

### `Unsupported cipher in --data-ciphers`

Inspect the current VPN data:

```text
nmcli --escape no -g vpn.data connection show 'CyberGhost - Dynamic'
```

A valid cipher list may look like:

```text
data-ciphers = AES-256-GCM\:AES-128-GCM\:AES-256-CBC
```

If it contains a large number of repeated backslashes, the profile may have been damaged by a tool that round-tripped serialized `vpn.data`. Restore the profile from a known-good configuration before using the switcher.

Current versions of this project do not reconstruct `vpn.data`.

### Country query fails or returns JSON errors

CyberGhost's directory/API may fail transiently, and some ISO countries may not have current CyberGhost locations.

Retry later or select another country. The switcher intentionally does not permanently classify a failed country query as unsupported.

### Server list contains strange load values

The switcher rejects loads below `0%` or above `100%`.

### Check the active endpoint

```text
nmcli --escape no -g vpn.data connection show 'CyberGhost - Dynamic'
```

### Check your public IPv4 address

```text
curl -4 https://ifconfig.me
```

### Inspect tunnel interfaces

```text
ip -4 addr
```

## Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `CYBERGHOST_BIN` | Explicit path to the official CyberGhost executable | Auto-discovered |
| `CG_SWITCHER_NM_PROFILE` | NetworkManager VPN profile to reuse | `CyberGhost - Dynamic` |

## Project files

```text
cg-switcher.py       Terminal client
cg-switcher-gui.py   PySide6 GUI
README.md            Documentation
LICENSE              MIT license
.gitignore           Private/generated-file exclusions
```

## Publishing / contribution safety

Do not commit or redistribute:

- CyberGhost passwords
- JWTs or authentication tokens
- account/device secrets
- private keys
- client certificates from your account
- `.ovpn` files containing private configuration
- `/usr/local/cyberghost/openvpn/`
- downloaded or extracted proprietary CyberGhost client files
- personal NetworkManager connection files

Before committing changes, inspect the staged diff and run a secret scan appropriate for your development workflow.

## Disclaimer

CyberGhost Linux Switcher is an unofficial community project and is not affiliated with, endorsed by, sponsored by, or maintained by CyberGhost.

A valid CyberGhost account and the official CyberGhost Linux client are required. CyberGhost and related marks belong to their respective owner.

This software is provided without warranty. You are responsible for reviewing the software, protecting your credentials and private key material, complying with CyberGhost's applicable terms, and verifying that your VPN connection behaves as expected.
