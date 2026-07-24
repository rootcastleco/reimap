# reimap for Android

A lightweight Android host for reimap. It ships two experiences:

1. **Offline demo (default)** — a fully self-contained, animated world map bundled
   in `app/src/main/assets/demo/`. No server, no network, no permissions beyond
   `INTERNET` are needed to enjoy it; it runs the instant you install the app.
2. **Live view** — from the overflow menu choose **Connect to server** and enter
   the URL of a running reimap desktop instance (for example
   `http://192.168.1.10:8050`) to stream the real connections your machine makes.

The privileged socket scanning is done by the desktop/server engine (Python); the
phone renders. This keeps the APK tiny, permission-light and store-friendly.

## Architecture

```
┌───────────────────────────┐        http         ┌────────────────────────┐
│  reimap desktop (Python)  │  ◀───────────────▶  │  reimap Android (Kotlin) │
│  scans sockets, GeoIP,    │   live view mode    │  WebView shell           │
│  serves the Dash UI       │                     │  + bundled offline demo  │
└───────────────────────────┘                     └────────────────────────┘
```

## Building

The project uses the Android Gradle Plugin 8.2 and Kotlin 1.9. You need JDK 17 and
the Android SDK (`compileSdk 34`).

```bash
cd android
# one-time: generate the Gradle wrapper if you don't have gradle installed
gradle wrapper

# debug APK  ->  app/build/outputs/apk/debug/app-debug.apk
./gradlew assembleDebug

# release APK (unsigned) -> app/build/outputs/apk/release/app-release-unsigned.apk
./gradlew assembleRelease
```

CI builds the debug APK on every push and attaches a signed-on-request APK to
tagged releases — see `.github/workflows/`.

## The offline demo

The demo map (`assets/demo/`) is original, dependency-free JavaScript:

- `land.json` — a compact land outline decoded at build time from the same
  MaxMind-free Natural Earth topology the desktop map uses.
- `demo-data.js` — the demo endpoint set, mirroring `reimap.demo` so the phone and
  the desktop tell the same story.
- `map.js` — a canvas renderer: filled continents, great-circle arcs radiating from
  the home origin, packets travelling along each arc, and pulsing hemisphere-aware
  markers (circles north, diamonds south — the same visual language as the desktop
  `geo_enricher` plugin).

Built by [Batuhan Ayrıbaş](https://batuhanayribas.com), a
[Rootcastle](https://rootcastle.com) project. MIT licensed.
