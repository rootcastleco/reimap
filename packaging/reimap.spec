# PyInstaller spec for reimap desktop binaries (Windows / macOS / Linux).
#
# Build:  pyinstaller packaging/reimap.spec
# Output: dist/reimap  (single-folder app; see COLLECT below)
#
# Dash and Plotly ship data files and many lazily-imported submodules, so we use
# collect_all to gather them, and we bundle reimap's own assets (the offline world
# map topology and any static files).

import os

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# Bundle Dash, Plotly and friends completely (they ship data files + lazy imports).
for pkg in ("dash", "plotly", "dash_core_components", "dash_html_components", "dash_table"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# reimap's own package data (assets/world_110m.json, world_50m.json, etc.).
# We locate the package by importing only its lightweight top-level module — we do
# NOT walk its submodules here, to avoid importing optional native deps (geoip2 →
# cryptography) during analysis on constrained build hosts.
import reimap  # noqa: E402

_pkg_dir = os.path.dirname(reimap.__file__)
datas += [(os.path.join(_pkg_dir, "assets"), "reimap/assets")]

# Explicit hidden imports: reimap submodules + optional native deps that are only
# imported lazily at runtime, listed as strings so analysis never executes them.
hiddenimports += [
    "reimap.app",
    "reimap.runtime",
    "reimap.demo",
    "reimap.geoip.database",
    "reimap.geoip.resolver",
    "reimap.scanner.psutil_scanner",
    "reimap.scanner.lsof_scanner",
    "reimap.plugins.manager",
    "reimap.plugins.builtin.connection_logger",
    "reimap.plugins.builtin.new_endpoint_alerts",
    "reimap.plugins.builtin.private_ip_filter",
    "reimap.plugins.builtin.geo_enricher",
    "reimap.plugins.builtin.jsonl_exporter",
    "reimap.ui.animation",
    "reimap.ui.callbacks",
    "reimap.ui.layout",
    "reimap.ui.shortcuts",
    "psutil",
    "geoip2",
    "geoip2.database",
    "geoip2.errors",
    "maxminddb",
    "requests",
    "engineio.async_drivers.threading",
]

block_cipher = None

a = Analysis(
    ["entry.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="reimap",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="reimap",
)
