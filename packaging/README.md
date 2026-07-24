# Packaging reimap desktop binaries

reimap ships as reproducible, single-folder desktop applications for Windows,
macOS and Linux, built with [PyInstaller](https://pyinstaller.org/) from
[`reimap.spec`](reimap.spec).

## Building locally

```bash
pip install -e .
pip install pyinstaller
cd packaging
pyinstaller reimap.spec --noconfirm
# result: packaging/dist/reimap/reimap  (plus its bundled runtime)
```

Run the result:

```bash
./dist/reimap/reimap            # Linux/macOS
dist\reimap\reimap.exe          # Windows
./dist/reimap/reimap --demo     # offline demo, no GeoIP needed
```

## Continuous delivery

The [`release`](../.github/workflows/release.yml) workflow builds all three desktop
binaries in parallel on native runners (`ubuntu-latest`, `windows-latest`,
`macos-latest`) and the Android APK, then attaches every artifact to the GitHub
Release for the pushed tag. This CI build is the canonical source of official
binaries.

## Notes

- The spec bundles Dash and Plotly completely (they ship data files and lazily
  imported submodules) and includes reimap's own `assets/` (the offline world map
  topology), so the binary needs no network to draw the map.
- `geoip2` is bundled so GeoIP works once the user installs a database. On some
  sandboxed build hosts, PyInstaller's isolated analysis of `cryptography` (an
  indirect `geoip2` dependency) can panic in the host's native crypto binding;
  this does not occur on the standard GitHub-hosted runners the release workflow
  uses. Build official binaries via CI.
