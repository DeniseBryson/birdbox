class CameraStream {
    constructor() {
        this.ws = null;
        this.streamImage = document.getElementById('stream-image');
        this.placeholder = document.getElementById('stream-placeholder');
        this.errorDisplay = document.getElementById('stream-error');
        this.startButton = document.getElementById('start-stream');
        this.stopButton = document.getElementById('stop-stream');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        this.startButton.addEventListener('click', () => this.startStream());
        this.stopButton.addEventListener('click', () => this.stopStream());
    }
    
    startStream() {
        if (this.ws || this.isConnecting) {
            return;
        }
        
        this.isConnecting = true;
        this.startButton.disabled = true;
        this.ws = new WebSocket(`ws://${window.location.host}/api/v1/camera/stream`);
        
        this.ws.onopen = () => {
            console.log('Stream connection opened');
            this.isConnecting = false;
            this.reconnectAttempts = 0;
            this.errorDisplay.style.display = 'none';
            this.startButton.style.display = 'none';
            this.stopButton.style.display = 'inline-block';
            this.stopButton.disabled = false;
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            switch (message.type) {
                case 'frame':
                    this.updateFrame(message.data);
                    break;
                case 'status':
                    console.log('Stream status:', message.status);
                    if (message.status === 'streaming') {
                        this.placeholder.style.display = 'none';
                        this.streamImage.style.display = 'block';
                    }
                    break;
                case 'error':
                    this.showError(message.message);
                    break;
            }
        };
        
        this.ws.onclose = () => {
            console.log('Stream connection closed');
            this.resetUI();
            this.ws = null;
            this.isConnecting = false;
            
            // Attempt to reconnect if not manually stopped
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                console.log(`Reconnecting... Attempt ${this.reconnectAttempts + 1}`);
                this.reconnectAttempts++;
                setTimeout(() => this.startStream(), 2000);
            } else {
                this.showError('Connection lost. Please refresh the page to try again.');
                this.startButton.disabled = false;
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('Stream error:', error);
            this.showError('Connection error');
            this.resetUI();
            this.startButton.disabled = false;
        };
    }
    
    stopStream() {
        if (this.ws) {
            this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
            this.ws.close();
            this.ws = null;
            this.stopButton.disabled = true;
        }
    }
    
    updateFrame(frameData) {
        // Convert Latin1 string back to binary data
        const binaryString = frameData;
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Create blob and update image
        const blob = new Blob([bytes], { type: 'image/jpeg' });
        this.streamImage.src = URL.createObjectURL(blob);
    }
    
    showError(message) {
        this.errorDisplay.textContent = message;
        this.errorDisplay.style.display = 'block';
        this.placeholder.style.display = 'none';
        this.streamImage.style.display = 'none';
    }
    
    resetUI() {
        this.startButton.style.display = 'inline-block';
        this.stopButton.style.display = 'none';
        this.streamImage.style.display = 'none';
        this.placeholder.style.display = 'block';
        this.placeholder.textContent = 'Stream disconnected';
    }
}
