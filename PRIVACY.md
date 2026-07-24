# Privacy

reimap is **local-first** and **telemetry-free** by design.

## What reimap does

- Enumerates the network sockets your own machine has open, using the operating
  system's standard facilities (`psutil`, or `lsof` on macOS as a fallback).
- Resolves the geographic location of remote IP addresses **locally**, against a
  MaxMind database file stored on your disk.
- Renders the results in a web UI served on `127.0.0.1` (localhost) only.

## What reimap does not do

- It does **not** send your connection data, IP addresses, or any usage
  information to any server.
- It does **not** require an account or an internet connection to run (only the
  optional GeoIP database download reaches out, and only when you ask it to).
- It does **not** perform any active scanning of remote hosts. reimap only
  observes sockets your own processes have already opened.

## What is stored on your machine

reimap keeps a small amount of state under your platform's standard directories:

| File | Location | Contents |
| --- | --- | --- |
| `config.json` | config dir | Your settings (theme, intervals, plugin list). |
| `history.json` | data dir | Rolling window of remote endpoints and hit counts. |
| `insights_latest.json` | data dir | The most recent insights snapshot. |
| `daily_reports.json` | data dir | Archived daily reports. |
| `scans.jsonl` | data dir | Only if the `jsonl_exporter` plugin is enabled. |
| `reimap.log` | log dir | Rotating application logs. |
| `geoip/*.mmdb` | cache dir | Your GeoIP database, if installed. |

All of these live only on your machine and can be deleted at any time. The exact
paths are shown in the **GeoIP** panel inside the app.

## The GeoIP download

The only outbound network request reimap can make is downloading the GeoLite2-City
database from MaxMind, and only when you explicitly press **Update GeoIP** with a
licence key you provide. GeoLite2 data is © MaxMind and governed by MaxMind's own
licensing terms.

## Plugins

Plugins run arbitrary Python you have installed. A plugin *could* send data
elsewhere — that is the nature of an extensibility system. Only enable plugins you
trust. The five built-in plugins never make network requests.

---

Questions? Reach the author at [batuhanayribas.com](https://batuhanayribas.com)
or the organisation at [rootcastle.com](https://rootcastle.com).
