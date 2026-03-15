# MiniDLNA (ReadyMedia) - Home Assistant Add-on

DLNA/UPnP media server for streaming audio, video and photos to network devices (Smart TVs, media players, game consoles, etc.).

## About

[MiniDLNA](https://sourceforge.net/projects/minidlna/) (ReadyMedia) is a lightweight DLNA/UPnP-AV media server. It serves media files to DLNA-compatible devices on your local network.

This add-on provides a modern, configurable MiniDLNA server for Home Assistant with Ingress support.

## Installation

1. Add the repository to your Home Assistant add-on store
2. Install the "MiniDLNA" add-on
3. Configure media directories
4. Start the add-on

## Configuration

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `media_dirs` | `["AV,/media"]` | Media directories with type prefix |
| `friendly_name` | `Home Assistant DLNA` | Server name visible to DLNA clients |
| `inotify` | `true` | Auto-detect new files using inotify |
| `notify_interval` | `900` | SSDP notify interval in seconds (60-86400) |
| `strict_dlna` | `false` | Strict DLNA compliance |
| `enable_subtitles` | `true` | Enable subtitle support |
| `log_level` | `warn` | Log level (off/fatal/error/warn/info/debug) |
| `wide_links` | `false` | Allow symlinks outside media directories |
| `root_container` | `.` | Root container: `.` (directory), `B` (music), `M` (music), `V` (video), `P` (pictures) |
| `force_rescan` | `false` | Delete database and rescan all media on next start |

### Media Directory Format

Each entry in `media_dirs` uses the format: `[TYPE,]PATH`

Type prefixes:
- `A` - Audio
- `V` - Video
- `P` - Pictures
- `AV` - Audio and Video
- `AP` - Audio and Pictures
- `VP` - Video and Pictures
- `AVP` or no prefix - All types

### Examples

```yaml
media_dirs:
  - "AV,/media"
  - "V,/media/movies"
  - "A,/media/music"
  - "P,/share/photos"
```

## Ports

- **8200** - MiniDLNA web interface and streaming port (accessible via Ingress and direct port)

## Web Interface

The MiniDLNA status page is accessible through:
- Home Assistant Ingress (sidebar)
- Direct access at `http://your-ha-ip:8200`

## Network

This add-on uses host networking for DLNA/UPnP discovery (SSDP multicast). DLNA clients on your local network will automatically discover the server.

## Data Persistence

The media database is stored in `/data/db` and persists across add-on restarts. Use the `force_rescan` option to rebuild the database if needed.

## License

This add-on is licensed under GPL v2, matching the MiniDLNA license.
