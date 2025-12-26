# CiRA Block Runtime - Web Dashboard

## Overview

The CiRA Block Runtime now includes an embedded web server that provides a **customizable dashboard** for monitoring and controlling deployed pipelines.

### Features

✅ **Real-time Monitoring**
- Live metrics from all blocks
- System statistics (CPU, memory, uptime)
- Streaming log viewer

✅ **Customizable Dashboard**
- Drag-and-drop widget layout
- 5 widget types: Status, Gauge, Line Chart, Text Display, Log Viewer
- Save/load custom layouts
- Pre-built templates

✅ **Dual Persistence**
- Dashboard config saved on device
- Backup in browser localStorage
- Survives device reboot

✅ **Secure Access**
- Username/password authentication
- Token-based session management
- Per-device login

✅ **Responsive Design**
- Works on desktop, tablet, mobile
- Modern UI with dark theme

---

## Quick Start

### 1. Build with Web Server

```bash
cd cira-block-runtime
cmake -DWITH_WEB_SERVER=ON -B build
cmake --build build
```

### 2. Run Runtime with Web Dashboard

```bash
./build/cira-block-runtime manifest.json --web-port 8080 --web-user admin --web-pass secret123
```

### 3. Access Dashboard

Open browser to: `http://your-device-ip:8080`

**Login:**
- Username: `admin`
- Password: `secret123`

---

## Dashboard Widgets

### 1. Status Indicator
Shows runtime status with uptime

**Configuration:**
- `showUptime`: Display uptime (default: true)

### 2. Gauge
Circular gauge for single numeric value

**Configuration:**
- `dataSource`: Metric path (e.g., `system.cpu_usage`)
- `min`: Minimum value
- `max`: Maximum value
- `unit`: Display unit (e.g., `%`, `MB`)

### 3. Line Chart
Real-time time-series chart

**Configuration:**
- `dataSource`: Metric path
- `maxPoints`: Number of data points to display (default: 50)

### 4. Text Display
Large text display for values

**Configuration:**
- `dataSource`: Metric path
- `format`: Format string (use `{value}` placeholder)
- `fontSize`: Text size in pixels

### 5. Log Viewer
Scrollable log viewer with filtering

**Configuration:**
- `filterLevel`: `ALL`, `INFO`, `WARNING`, `ERROR`
- `maxLines`: Maximum lines to display
- `autoScroll`: Auto-scroll to latest (default: true)

---

## Data Sources

### System Metrics

- `system.cpu_usage` - CPU usage percentage
- `system.memory_used_mb` - Used memory in MB
- `system.memory_total_mb` - Total memory in MB
- `system.uptime_seconds` - Runtime uptime in seconds

### Block Metrics (Coming Soon)

- `{block_id}.execution_count` - Number of executions
- `{block_id}.avg_latency_ms` - Average execution time
- `{block_id}.{pin_name}` - Block output values

---

## Customizing Dashboard

### Edit Mode

1. Click **"✏️ Edit Layout"** button
2. Widget palette appears on the left
3. **Drag widgets** from palette to canvas
4. **Resize/move** widgets as needed
5. Click **"💾 Save"** to persist changes

### Widget Configuration

- Click **⚙️** icon on widget to configure
- Adjust data source, formatting, colors
- Click **Apply** to save changes

### Reset to Default

Delete `dashboard_config.json` on device and refresh browser.

---

## API Endpoints

### Authentication
```
POST /api/auth/login
Body: {"username": "admin", "password": "secret123"}
Response: {"token": "abc123...", "auth_enabled": true}
```

### Dashboard Config
```
GET  /api/dashboard/config
POST /api/dashboard/config
Body: {dashboard JSON}
```

### Metrics
```
GET /api/metrics
Response: {
  "blocks": [...],
  "system": {...},
  "timestamp": 1234567890
}
```

### Logs
```
GET /api/logs?limit=100&level=ERROR
Response: [
  {"level": "ERROR", "message": "...", "timestamp": 123456}
]
```

### Runtime Control
```
POST /api/runtime/start
POST /api/runtime/stop
POST /api/runtime/restart
```

---

## Deployment from Pipeline Builder

When deploying from Pipeline Builder:

1. Select **Block Runtime (Development)** mode
2. Check **✅ Enable Web Dashboard**
3. Set port (default: 8080)
4. Set username and password
5. Deploy

After deployment completes:
```
Deployment complete! Runtime is executing on target.

Web Dashboard: http://192.168.1.200:8080
Username: admin
Password: ********
```

---

## Security Notes

### Production Deployment

For production use, consider:

1. **Use strong passwords** - Minimum 12 characters
2. **Enable HTTPS** - Use reverse proxy (nginx, Apache)
3. **Firewall rules** - Only allow trusted IPs
4. **Change default port** - Don't use 8080

### Example: nginx Reverse Proxy with HTTPS

```nginx
server {
    listen 443 ssl;
    server_name jetson.local;

    ssl_certificate /etc/ssl/certs/jetson.crt;
    ssl_certificate_key /etc/ssl/private/jetson.key;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }
}
```

---

## Troubleshooting

### Dashboard Not Loading

**Check if web server is running:**
```bash
# On device
netstat -tuln | grep 8080
```

**Check firewall:**
```bash
# Ubuntu/Debian
sudo ufw allow 8080

# Jetson Nano
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

### Can't Login

**Reset credentials:**
```bash
# Restart runtime with new credentials
./cira-block-runtime manifest.json --web-user newuser --web-pass newpass
```

**Disable authentication (not recommended):**
```bash
./cira-block-runtime manifest.json --web-port 8080 --no-auth
```

### Metrics Not Updating

**Check browser console:**
- Press F12
- Look for errors in Console tab
- Verify `/api/metrics` returns data

**Check runtime logs:**
```bash
# Runtime should log web requests
tail -f logs/runtime.log
```

---

## Development

### Adding Custom Widgets

1. Create widget class in `web/js/widgets.js`:

```javascript
class MyCustomWidget extends Widget {
    getDefaultConfig() {
        return {
            title: 'My Widget',
            customSetting: 'value'
        };
    }

    renderBody() {
        return `<div>Custom widget content</div>`;
    }

    update(data) {
        // Update widget with new data
    }
}
```

2. Register in WidgetFactory:

```javascript
class WidgetFactory {
    static create(type, id, config) {
        switch (type) {
            case 'my-custom':
                return new MyCustomWidget(id, type, config);
            // ... other widgets
        }
    }
}
```

3. Add to palette in `index.html`:

```html
<div class="palette-item" data-widget="my-custom" draggable="true">
    <span class="widget-icon">🎨</span>
    <span>My Widget</span>
</div>
```

---

## Performance

### Resource Usage

- **Memory**: ~10 MB (web server + dashboard)
- **CPU**: <1% idle, ~2-5% during active monitoring
- **Network**: ~1-5 KB/s (metrics polling)

### Optimization Tips

1. **Reduce poll rate** - Edit `dashboard.js`, change interval from 1000ms to 2000ms
2. **Limit log buffer** - Reduce `MAX_LOG_BUFFER_SIZE` in `web_server.cpp`
3. **Fewer widgets** - Remove unused widgets to reduce rendering overhead

---

## Future Enhancements (Phase 6)

- [ ] WebSocket for real-time streaming (instead of polling)
- [ ] Video stream widget for camera feeds
- [ ] Block configuration editor
- [ ] Pipeline rewiring from web UI
- [ ] Multi-dashboard support (different views for different users)
- [ ] Export/import dashboard templates
- [ ] Dark/light theme toggle
- [ ] Custom widget builder (no code required)

---

## License

Part of CiRA FES - Copyright 2025

---

## Support

For issues or questions:
- Check logs: `logs/runtime.log`
- GitHub Issues: https://github.com/your-repo/cira-fes/issues
- Documentation: See `BUILD_AND_TEST.md`
