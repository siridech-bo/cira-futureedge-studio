# Quick Start - WebSocket Streaming

## TL;DR

**Build → Deploy → Done!**

The system automatically uses WebSocket (fast) and falls back to SSE (compatible). No configuration needed!

---

## 3-Minute Setup

### 1. Build (30 seconds)
```bash
cd cira-block-runtime/build
cmake ..
cmake --build . --config Release
```

### 2. Deploy (1 minute)
```bash
# Backend
scp bin/cira-block-runtime user@192.168.1.200:/path/to/runtime/

# Frontend
scp -r ../web/* user@192.168.1.200:/path/to/runtime/web/
```

### 3. Test (30 seconds)
Open `http://192.168.1.200:8082` in browser

Look for:
```
📡 Stream Mode panel (bottom-right)
Active: WEBSOCKET ✓
```

**Done!** You're now using high-performance WebSocket streaming.

---

## How to Switch Modes

### Option 1: Use UI (Easiest)
1. Click "📡 Stream Mode" panel (bottom-right)
2. Select mode
3. Click "Apply & Reload"

### Option 2: Edit Config
```javascript
// web/js/oscilloscope-config.js
mode: 'auto'        // Smart (default)
mode: 'websocket'   // Force new
mode: 'sse'         // Force old
```

---

## What Changed?

| Before | After |
|--------|-------|
| SSE only | SSE + WebSocket |
| 300 msg/sec | 30 msg/sec (10× less) |
| JSON text | Binary MessagePack |
| 4-6 oscilloscopes | 10+ oscilloscopes |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Build fails | Fixed include: `block_interface.hpp` |
| No WebSocket | Check console for port 8083 |
| Selector missing | Clear cache (`Ctrl+F5`) |
| Want SSE | Click selector → choose SSE |

---

## Files to Know

**Config:** `web/js/oscilloscope-config.js`
**UI:** Bottom-right floating panel
**Docs:** `STREAM_MODE_SELECTION.md`

---

## Default Behavior

✅ Auto-selects WebSocket if available
✅ Falls back to SSE if not
✅ User can override via UI
✅ Choice persists across sessions

**Zero configuration required!**
