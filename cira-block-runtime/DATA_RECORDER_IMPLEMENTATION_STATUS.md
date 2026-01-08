# Data Recorder Implementation Status

## Overview
Implementing dataset recording functionality for closed-loop model retraining workflow.

## Completed Components ✅

### 1. Data Recorder Block (C++)
**Location:** `blocks/outputs/data_recorder/`

**Files Created:**
- `data_recorder_block.cpp` - Full implementation with:
  - Multiple input pins: record_trigger, data_stream_1, data_stream_2, label
  - Output pins: recording_status, sample_count
  - Format support: CSV, JSON, CBOR (placeholder), NPY (placeholder)
  - Timestamp recording in microseconds
  - Auto-stop on max_samples or duration_ms
  - Save to `/home/user/cira_datasets/` directory
- `CMakeLists.txt` - Build configuration
- Added to main `CMakeLists.txt` at line 177

**Features:**
- Triggered recording via `record_trigger` input pin
- Records multiple data streams simultaneously
- Timestamps with microsecond precision
- Configurable output format, max samples, duration
- Auto-creates save directory

### 2. Web Dashboard Recorder Widget (JavaScript)
**Location:** `web/js/`

**Files Created:**
- `recorder-widget.js` - DataRecorderWidget class with:
  - Start/Stop recording buttons
  - Real-time status display (idle/recording)
  - Elapsed time counter (MM:SS format)
  - Sample count display
  - Dataset list with download/delete buttons
  - WebSocket integration for real-time updates
  - Subscribes to `recording_status` and `sample_count` outputs

**Features:**
- Sends `start_recording`/`stop_recording` commands via WebSocket
- Displays saved datasets with metadata (filename, size, timestamp)
- Download button triggers file download from Jetson to browser
- Delete button with confirmation dialog
- Auto-refreshes dataset list after recording stops

## Remaining Tasks ⚠️

### 3. Fix widgets.js WidgetFactory
**Issue:** Duplicate `case 'oscilloscope':` line at lines 760-761

**Fix Needed:**
```javascript
// Remove duplicate at line 761, should be:
case 'signalplot':
    return new SignalPlotWidget(id, type, config);
case 'oscilloscope':
    return new OscilloscopeWidget(id, type, config);
case 'recorder':
    return new DataRecorderWidget(id, type, config);
default:
    return new Widget(id, type, config);
```

### 4. Web Server API Endpoints (C++)
**Location:** `src/web_server.cpp`

**Endpoints to Add:**

#### GET `/api/datasets`
```cpp
// List all datasets in /home/user/cira_datasets/
// Returns JSON:
{
  "datasets": [
    {
      "filename": "dataset_20260106_143022.cbor",
      "size_kb": 1234,
      "timestamp": "2026-01-06 14:30:22"
    },
    ...
  ]
}
```

#### GET `/api/datasets/download/{filename}`
```cpp
// Stream file download
// Content-Type: application/octet-stream
// Content-Disposition: attachment; filename="{filename}"
```

#### DELETE `/api/datasets/{filename}`
```cpp
// Delete dataset file
// Returns 200 OK or 404 Not Found
```

### 5. WebSocket Command Handlers
**Location:** `src/websocket_server.cpp` or `src/web_server.cpp`

**Commands to Handle:**
```cpp
// Command: start_recording
{
  "command": "start_recording",
  "node_id": 1
}
// Action: Set record_trigger input to true for specified node

// Command: stop_recording
{
  "command": "stop_recording",
  "node_id": 1
}
// Action: Set record_trigger input to false
```

### 6. CSS Styles for Recorder Widget
**Location:** `web/css/dashboard.css`

**Styles Needed:**
```css
/* Recorder Widget Styles */
.recorder-widget {
    display: flex;
    flex-direction: column;
    gap: 15px;
    padding: 15px;
}

.recorder-controls {
    display: flex;
    gap: 10px;
}

.recorder-btn {
    flex: 1;
    padding: 12px;
    font-size: 16px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: all 0.3s;
}

.start-btn {
    background: #27ae60;
    color: white;
}

.start-btn:hover:not(:disabled) {
    background: #229954;
}

.stop-btn {
    background: #e74c3c;
    color: white;
}

.stop-btn:disabled {
    background: #95a5a6;
    cursor: not-allowed;
}

.btn-icon {
    font-size: 18px;
}

.recorder-status {
    background: #34495e;
    border-radius: 5px;
    padding: 15px;
}

.status-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.status-label {
    color: #95a5a6;
    font-weight: bold;
}

.status-value {
    color: #ecf0f1;
}

.status-value.recording {
    color: #e74c3c;
    font-weight: bold;
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.recorder-datasets {
    border-top: 1px solid #34495e;
    padding-top: 15px;
}

.datasets-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.datasets-header h4 {
    margin: 0;
    color: #ecf0f1;
}

.refresh-btn {
    background: transparent;
    border: 1px solid #3498db;
    color: #3498db;
    padding: 5px 10px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 18px;
}

.refresh-btn:hover {
    background: #3498db;
    color: white;
}

.datasets-list {
    max-height: 300px;
    overflow-y: auto;
}

.dataset-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #2c3e50;
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 5px;
}

.dataset-info {
    flex: 1;
}

.dataset-name {
    font-weight: bold;
    color: #ecf0f1;
    margin-bottom: 4px;
}

.dataset-meta {
    font-size: 12px;
    color: #95a5a6;
}

.dataset-actions {
    display: flex;
    gap: 8px;
}

.download-btn, .delete-btn {
    padding: 6px 12px;
    border: none;
    border-radius: 3px;
    cursor: pointer;
    font-size: 14px;
}

.download-btn {
    background: #3498db;
    color: white;
}

.download-btn:hover {
    background: #2980b9;
}

.delete-btn {
    background: #e74c3c;
    color: white;
}

.delete-btn:hover {
    background: #c0392b;
}

.loading, .no-datasets, .error {
    text-align: center;
    padding: 20px;
    color: #95a5a6;
    font-style: italic;
}

.error {
    color: #e74c3c;
}
```

### 7. Include recorder-widget.js in index.html
**Location:** `web/index.html`

**Add before closing `</body>` tag:**
```html
<script src="js/recorder-widget.js?v=20260106a"></script>
```

### 8. Add Data Recorder to Pipeline Builder
**Location:** `pipeline_builder/` (node registry)

**Node Definition:**
```json
{
  "id": "data-recorder",
  "name": "Data Recorder",
  "category": "Output",
  "description": "Record datasets for model retraining",
  "inputs": [
    {"name": "record_trigger", "type": "bool"},
    {"name": "data_stream_1", "type": "float"},
    {"name": "data_stream_2", "type": "float_vector"},
    {"name": "label", "type": "int"}
  ],
  "outputs": [
    {"name": "recording_status", "type": "bool"},
    {"name": "sample_count", "type": "int"}
  ],
  "config": [
    {"name": "format", "type": "string", "default": "cbor"},
    {"name": "save_directory", "type": "string", "default": "/home/user/cira_datasets"},
    {"name": "max_samples", "type": "int", "default": 0},
    {"name": "duration_ms", "type": "int", "default": 0}
  ]
}
```

## Testing Workflow

1. **Build cira-block-runtime:**
   ```bash
   cd cira-block-runtime/build
   cmake ..
   make
   ```

2. **Create Test Pipeline:**
   - Synthetic Signal Generator → data_stream_1
   - Sliding Window → data_stream_2
   - Web Button (button_1) → record_trigger
   - TimesNet prediction → label
   - Data Recorder outputs → Web Dashboard widget

3. **Deploy to Jetson:**
   - Use Pipeline Builder deployment
   - Check `/home/user/cira_datasets/` directory exists

4. **Test Recording:**
   - Open web dashboard
   - Add Recorder widget
   - Press Start Recording button
   - Wait for samples
   - Press Stop Recording
   - Verify dataset appears in list

5. **Test Download:**
   - Click Download button on dataset
   - Verify file downloads to browser
   - Open file and verify data format

6. **Test Retraining Loop:**
   - Download dataset from Jetson
   - Use dataset to retrain TimesNet model
   - Deploy updated model
   - Test predictions

## Implementation Priority

1. Fix widgets.js (5 min)
2. Add CSS styles (10 min)
3. Include recorder-widget.js in index.html (2 min)
4. Implement web server API endpoints (30 min)
5. Add WebSocket command handlers (15 min)
6. Add node to Pipeline Builder registry (10 min)
7. Build and test (30 min)

**Total Estimated Time:** ~2 hours

## Notes

- CBOR and NPY format support is placeholders (saves as JSON/CSV)
- True CBOR encoding would require msgpack-c library
- True NPY format would require implementing NumPy .npy binary format
- For MVP, JSON and CSV formats are sufficient for retraining
