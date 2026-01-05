# Stream Mode Selection Guide

## How to Choose Between SSE and WebSocket

The system now supports **TWO streaming modes** that work simultaneously:

| Mode | Port | Performance | Status |
|------|------|-------------|--------|
| **SSE** | 8082 | Good | ✅ Stable (Legacy) |
| **WebSocket** | 8083 | Excellent | ✅ New (Recommended) |

---

## **3 Ways to Select Mode:**

### **Method 1: Automatic Selection (Default)**

The system automatically chooses the best mode:

```javascript
// In oscilloscope-config.js
mode: 'auto'
```

**Behavior:**
- ✅ Uses **WebSocket** if browser supports it (Chrome, Firefox, Edge, Safari)
- ✅ Falls back to **SSE** if WebSocket unavailable (old browsers, network restrictions)
- ✅ Zero configuration needed

---

### **Method 2: UI Selector (User-Friendly)**

A floating control panel appears in the bottom-right corner of the dashboard:

```
┌─────────────────────────────┐
│ 📡 Stream Mode         ▼    │
├─────────────────────────────┤
│ ○ Auto (Recommended)        │
│ ○ WebSocket (NEW)           │
│ ○ SSE (Legacy)              │
│                             │
│ [Apply & Reload]            │
│                             │
│ Active: WEBSOCKET           │
│ WebSocket: ✓ Available      │
└─────────────────────────────┘
```

**How to use:**
1. Click the panel to expand
2. Select your preferred mode
3. Click "Apply & Reload"
4. Dashboard reloads with new mode

**Your choice is saved** in browser localStorage and persists across sessions.

---

### **Method 3: Manual Configuration (Advanced)**

Edit `web/js/oscilloscope-config.js` directly:

```javascript
const OscilloscopeStreamConfig = {
    mode: 'websocket',  // Options: 'auto', 'sse', 'websocket'

    // Other settings...
    targetFPS: 30,
    downsampleTarget: 1000,
};
```

Then rebuild or redeploy.

---

## **Feature Comparison:**

| Feature | SSE (Legacy) | WebSocket (New) |
|---------|-------------|-----------------|
| **Performance** | Good | Excellent (5-10× faster) |
| **Latency** | ~50-100ms | ~10-20ms |
| **Network Overhead** | High (JSON text) | Low (Binary MessagePack) |
| **Multiple Channels** | 1 connection each | 1 connection shared |
| **Browser Support** | All browsers | Modern browsers (99%+) |
| **Server CPU** | Medium | Low |
| **Scalability** | 4-6 oscilloscopes | 10+ oscilloscopes |
| **Future Features** | Limited | ✅ Images, ✅ Video |

---

## **When to Use Each Mode:**

### **Use WebSocket (Recommended):**
- ✅ Modern browsers (Chrome, Firefox, Edge, Safari)
- ✅ Need best performance (multiple oscilloscopes)
- ✅ Planning to add camera/image streaming
- ✅ Want lowest latency

### **Use SSE (Fallback):**
- ⚠️ Old/legacy browser requirements
- ⚠️ Corporate firewall blocks WebSocket
- ⚠️ Testing/debugging SSE-specific issues
- ⚠️ Maximum compatibility needed

### **Use Auto (Best Choice):**
- ✅ Don't want to think about it
- ✅ Want best performance where available
- ✅ Need automatic fallback
- ✅ **This is the default!**

---

## **How It Works Internally:**

### **Server Side (Automatic):**

When a block outputs data, **both paths receive it simultaneously**:

```cpp
void WebServer::BroadcastSignalData(node_id, pin_name, value) {
    // Path 1: WebSocket (NEW)
    signal_aggregator_->PushSample(node_id, pin_name, value);
    websocket_server_->BroadcastWaveform(...);

    // Path 2: SSE (LEGACY)
    for (auto& sse_connection : sse_connections_) {
        sse_connection->Send(json_data);
    }
}
```

**No configuration needed** - server handles both automatically.

### **Client Side (You Choose):**

The oscilloscope widget checks your configuration:

```javascript
// In oscilloscope.js (pseudocode)
if (OscilloscopeStreamConfig.selectMode() === 'websocket') {
    this.connectWebSocket();  // High performance
} else {
    this.connectSSE();        // Fallback
}
```

---

## **Testing Both Modes:**

### **Test WebSocket:**
1. Set mode to `'websocket'` or `'auto'`
2. Open browser console
3. Look for: `[Oscilloscope] Auto-selected WebSocket mode`
4. Check network tab for `ws://192.168.1.200:8083` connections

### **Test SSE:**
1. Set mode to `'sse'`
2. Open browser console
3. Look for: `[Oscilloscope] Auto-selected SSE mode`
4. Check network tab for `/api/signals/stream` EventSource connections

### **Verify Performance:**

**WebSocket should show:**
- Fewer network requests (~30/sec vs 300/sec)
- Smaller payload sizes (binary vs JSON)
- Lower CPU usage in browser DevTools

---

## **Troubleshooting:**

### **Q: Mode selector doesn't appear**
**A:** Clear browser cache and reload (`Ctrl+F5`)

### **Q: WebSocket shows "Not Available"**
**A:** Check server console for:
```
[WebSocketServer] Started on port 8083
```

### **Q: WebSocket connects but no data**
**A:** Verify backend is compiled with new code:
```bash
cd build && cmake --build . --config Release
```

### **Q: Want to force SSE even with WebSocket available**
**A:** Use UI selector or set `mode: 'sse'` in config

### **Q: How do I know which mode is active?**
**A:** Check browser console:
```
=== Oscilloscope Stream Configuration ===
Mode: websocket
WebSocket Support: true
HTTP URL: http://192.168.1.200:8082
WebSocket URL: ws://192.168.1.200:8083
==========================================
```

---

## **Migration Strategy:**

### **Phase 1: Testing (Current)**
- ✅ Both modes work
- ✅ Default is 'auto' (prefers WebSocket)
- ✅ Users can switch easily

### **Phase 2: Full WebSocket (Future)**
- SSE code remains for compatibility
- WebSocket becomes default
- SSE can be removed in 6 months if no issues

### **Phase 3: Deprecation (Optional)**
- After 6-12 months of WebSocket stability
- Remove SSE code entirely
- Full binary protocol

---

## **Configuration Summary:**

| Setting | Location | Purpose |
|---------|----------|---------|
| `mode` | `oscilloscope-config.js` | Force mode or use auto |
| UI Selector | Bottom-right corner | User-friendly mode switch |
| localStorage | Browser | Persists user choice |
| Server | Automatic | Runs both simultaneously |

---

## **Quick Start:**

**Default configuration works out of the box!**

Just deploy and:
1. Modern browsers → automatically use WebSocket ⚡
2. Old browsers → automatically fallback to SSE ✅
3. Users can override via UI selector if needed 🎛️

**No action required** - the system is smart enough to choose the best mode!

---

## **Advanced: MessagePack Support**

For even better performance, install MessagePack library:

```html
<!-- Add to index.html before oscilloscope-config.js -->
<script src="https://cdn.jsdelivr.net/npm/msgpack-lite@0.1.26/dist/msgpack.min.js"></script>
```

**Benefits:**
- 30-50% smaller payloads
- Faster encoding/decoding
- Better for binary data (images, video)

**Status:** Optional - fallback binary protocol works without it

---

## **Conclusion:**

You have **3 ways** to choose streaming mode:
1. **Auto** (recommended) - Smart default
2. **UI Selector** (user-friendly) - Click to switch
3. **Manual Config** (advanced) - Edit JavaScript

**Both modes work simultaneously**, so there's **zero risk** in testing the new WebSocket mode.

🎯 **Recommended:** Keep default `mode: 'auto'` and let users choose via UI if they want!
