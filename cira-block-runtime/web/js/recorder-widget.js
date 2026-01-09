// Data Recorder Widget - Record datasets and download for retraining
class DataRecorderWidget extends Widget {
    constructor(id, type, config) {
        super(id, type, config);
        this.isRecording = false;
        this.recordingStartTime = null;
        this.sampleCount = 0;
        this.elapsedSeconds = 0;
        this.updateInterval = null;
        this.datasets = [];
    }

    getDefaultConfig() {
        return {
            title: 'Dataset Recorder',
            recorderNodeId: 1,
            format: 'cbor',
            autoRefresh: true
        };
    }

    renderBody() {
        return `
            <div class="recorder-widget">
                <div class="recorder-controls">
                    <button class="recorder-btn start-btn" id="recorder-start-${this.id}">
                        <span class="btn-icon">⏺</span> Start Recording
                    </button>
                    <button class="recorder-btn stop-btn" id="recorder-stop-${this.id}" disabled>
                        <span class="btn-icon">⏹</span> Stop
                    </button>
                </div>

                <div class="recorder-status" id="recorder-status-${this.id}">
                    <div class="status-row">
                        <span class="status-label">Status:</span>
                        <span class="status-value" id="status-text-${this.id}">Idle</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Time:</span>
                        <span class="status-value" id="elapsed-time-${this.id}">00:00</span>
                    </div>
                </div>

                <div class="recorder-datasets">
                    <div class="datasets-header">
                        <h4>Saved Datasets</h4>
                        <button class="refresh-btn" id="refresh-datasets-${this.id}">↻</button>
                    </div>
                    <div class="datasets-list" id="datasets-list-${this.id}">
                        <div class="loading">Loading...</div>
                    </div>
                </div>
            </div>
        `;
    }

    afterRender() {
        const startBtn = document.getElementById(`recorder-start-${this.id}`);
        const stopBtn = document.getElementById(`recorder-stop-${this.id}`);
        const refreshBtn = document.getElementById(`refresh-datasets-${this.id}`);

        if (startBtn) {
            startBtn.addEventListener('click', () => this.startRecording());
        }

        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopRecording());
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDatasets());
        }

        // Load datasets on init
        this.loadDatasets();

        // Subscribe to recorder status updates
        this.subscribeToRecorderStatus();
    }

    subscribeToRecorderStatus() {
        // Subscribe to recording_status output
        const nodeId = this.config.recorderNodeId || 1;

        if (typeof wsManager !== 'undefined' && wsManager.isConnected()) {
            wsManager.subscribe(`${nodeId}:recording_status`, (value) => {
                this.updateRecordingStatus(value > 0);
            });
        }
    }

    startRecording() {
        console.log('[DataRecorder] Starting recording...');

        const startBtn = document.getElementById(`recorder-start-${this.id}`);
        const stopBtn = document.getElementById(`recorder-stop-${this.id}`);

        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;

        // Send start command via WebSocket
        if (typeof wsManager !== 'undefined' && wsManager.isConnected()) {
            const command = {
                command: 'start_recording',
                node_id: this.config.recorderNodeId || 1
            };
            wsManager.ws.send(JSON.stringify(command));
        }

        this.isRecording = true;
        this.recordingStartTime = Date.now();
        this.sampleCount = 0;

        // Start update interval
        this.updateInterval = setInterval(() => {
            this.updateElapsedTime();
        }, 1000);

        this.updateStatusText('Recording...');
    }

    stopRecording() {
        console.log('[DataRecorder] Stopping recording...');

        const startBtn = document.getElementById(`recorder-start-${this.id}`);
        const stopBtn = document.getElementById(`recorder-stop-${this.id}`);

        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;

        // Send stop command via WebSocket
        if (typeof wsManager !== 'undefined' && wsManager.isConnected()) {
            const command = {
                command: 'stop_recording',
                node_id: this.config.recorderNodeId || 1
            };
            wsManager.ws.send(JSON.stringify(command));
        }

        this.isRecording = false;

        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        this.updateStatusText('Idle');

        // Refresh datasets list after a short delay
        setTimeout(() => this.loadDatasets(), 1000);
    }

    updateRecordingStatus(isRecording) {
        if (isRecording && !this.isRecording) {
            // Backend started recording
            this.isRecording = true;
            this.recordingStartTime = Date.now();

            const startBtn = document.getElementById(`recorder-start-${this.id}`);
            const stopBtn = document.getElementById(`recorder-stop-${this.id}`);
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;

            this.updateStatusText('Recording...');
        } else if (!isRecording && this.isRecording) {
            // Backend stopped recording
            this.stopRecording();
        }
    }

    updateStatusText(text) {
        const statusText = document.getElementById(`status-text-${this.id}`);
        if (statusText) {
            statusText.textContent = text;
            statusText.className = 'status-value';
            if (text === 'Recording...') {
                statusText.classList.add('recording');
            }
        }
    }

    updateElapsedTime() {
        if (!this.isRecording || !this.recordingStartTime) return;

        const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;

        const timeText = document.getElementById(`elapsed-time-${this.id}`);
        if (timeText) {
            timeText.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }
    }

    async loadDatasets() {
        const listContainer = document.getElementById(`datasets-list-${this.id}`);
        if (!listContainer) return;

        listContainer.innerHTML = '<div class="loading">Loading...</div>';

        try {
            const response = await fetch('/api/datasets');
            const data = await response.json();

            this.datasets = data.datasets || [];

            if (this.datasets.length === 0) {
                listContainer.innerHTML = '<div class="no-datasets">No datasets recorded yet</div>';
                return;
            }

            let html = '';
            for (const dataset of this.datasets) {
                html += `
                    <div class="dataset-item">
                        <div class="dataset-info">
                            <div class="dataset-name">${dataset.filename}</div>
                            <div class="dataset-meta">
                                ${dataset.size_kb} KB • ${dataset.timestamp}
                            </div>
                        </div>
                        <div class="dataset-actions">
                            <button class="download-btn" onclick="window.downloadDataset('${dataset.filename}')">
                                ⬇ Download
                            </button>
                            <button class="delete-btn" onclick="window.deleteDataset('${dataset.filename}', '${this.id}')">
                                🗑
                            </button>
                        </div>
                    </div>
                `;
            }

            listContainer.innerHTML = html;
        } catch (error) {
            console.error('[DataRecorder] Error loading datasets:', error);
            listContainer.innerHTML = '<div class="error">Failed to load datasets</div>';
        }
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Global functions for dataset management
window.downloadDataset = async function(filename) {
    try {
        const response = await fetch(`/api/datasets/download/${filename}`);
        const blob = await response.blob();

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        console.log(`[DataRecorder] Downloaded: ${filename}`);
    } catch (error) {
        console.error('[DataRecorder] Download failed:', error);
        alert('Failed to download dataset');
    }
};

window.deleteDataset = async function(filename, widgetId) {
    if (!confirm(`Delete dataset "${filename}"?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/datasets/${filename}`, {
            method: 'DELETE',
            credentials: 'include',
            headers: {
                'Authorization': 'Bearer ' + (localStorage.getItem('auth_token') || '')
            }
        });

        if (response.ok) {
            console.log(`[DataRecorder] Deleted: ${filename}`);
            // Refresh the dataset list by finding the widget instance
            if (widgetManager && widgetManager.widgets) {
                const widget = widgetManager.widgets.find(w => w.id === widgetId);
                if (widget && widget.loadDatasets) {
                    widget.loadDatasets();
                }
            }
        } else {
            alert('Failed to delete dataset');
        }
    } catch (error) {
        console.error('[DataRecorder] Delete failed:', error);
        alert('Failed to delete dataset');
    }
};
