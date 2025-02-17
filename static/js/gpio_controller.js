/**
 * GPIO Controller for BirdsOS
 * Handles all GPIO-related frontend functionality
 */
class GPIOController {
    constructor() {
        this.selectedPin = null;
        this.pins = [];  // Cache of pin states
        this.setupEventListeners();
        this.setupWebSocket();
        this.dropdownPopulated = false;
    }
    
    setupWebSocket() {
        const ws = new WebSocket(`ws://${window.location.host}/ws/gpio-updates`);
        console.log('WebSocket opened');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            if (data.type === 'gpio_update') {
                // Update our cache
                if (data.data.pins) {
                    console.log('got pins:', data.data.pins);
                    this.pins = data.data.pins;
                    if (!this.dropdownPopulated) {
                        this.populatePinDropdown(this.pins);
                        this.dropdownPopulated = true;
                    }
                    this.updateOverviewTable(this.pins);
                }
                if (data.data.states) {
                    // Update specific pin states
                    Object.entries(data.data.states).forEach(([pin, state]) => {
                        const pinObj = this.pins.find(p => p.number === parseInt(pin));
                        if (pinObj) {
                            pinObj.state = state;
                            this.updatePinStates([pinObj]);
                        }
                    });
                }
            }
        };

        ws.onclose = () => {
            // Attempt to reconnect after a delay
            console.log('WebSocket closed, attempting to reconnect...');
            setTimeout(() => this.setupWebSocket(), 2000);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onopen = () => {
            console.log('WebSocket connected');
        };
    }
    
    populatePinDropdown(pins) {
        const select = document.getElementById('gpio-pin-select');
        if (!select) return;  // Guard clause if element doesn't exist
        
        // Store current selection
        const currentValue = this.selectedPin ? this.selectedPin.toString() : '';
        
        // Clear existing options
        select.innerHTML = '<option value="">Choose a pin...</option>';
        
        // Sort pins by number for better display
        pins.sort((a, b) => a.number - b.number).forEach(pin => {
            const option = document.createElement('option');
            option.value = pin.number;
            option.textContent = `GPIO ${pin.number} (${pin.configured ? pin.mode === 1 ? 'Input' : 'Output' : 'Unconfigured'})`;
            if (pin.number.toString() === currentValue) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }
    
    updatePinStates(pins) {
        console.log('Updating pin states:', pins);
        if (this.selectedPin) {
            const pin = pins.find(p => p.number === this.selectedPin);
            if (pin) {
                this.updatePinStatus(pin);
            }
        }
    }
    
    updatePinStatus(pin) {
        console.log('Updating pin status:', pin);
        const indicator = document.querySelector('.state-indicator');
        const text = document.querySelector('.state-text');
        if (!indicator || !text) return;  // Guard clause
        
        indicator.className = 'state-indicator';
        indicator.classList.add(pin.state ? 'high' : 'low');
        
        text.textContent = `Mode: ${pin.mode}, State: ${pin.state ? 'HIGH' : 'LOW'}`;
    }
    
    updateOverviewTable(pins) {
        const tbody = document.querySelector('#gpio-overview tbody');
        if (!tbody) return;  // Guard clause

        console.log('Updating overview table:', pins);
        tbody.innerHTML = '';
        
        // Sort pins by number for consistent display
        pins.sort((a, b) => a.number - b.number).forEach(pin => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="pin-number">GPIO ${pin.number}</td>
                <td class="pin-mode">${pin.configured ? pin.mode === 1 ? 'Input' : 'Output' : 'Unconfigured'}</td>
                <td class="pin-state">
                    <span class="state-indicator ${pin.state ? 'high' : 'low'}"></span>
                    <span class="state-text">${pin.state ? 'HIGH' : 'LOW'}</span>
                </td>
                <td class="pin-actions">
                    ${pin.configured && pin.mode === 'OUT' ? `
                        <button class="btn btn-sm btn-${pin.state ? 'success' : 'danger'} toggle-btn"
                                onclick="gpioController.togglePinState(${pin.number}, ${pin.state ? 0 : 1})">
                            Toggle
                        </button>
                    ` : pin.mode === 'IN' ? 'Input Pin' : '-'}
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    async configurePin(mode) {
        if (!this.selectedPin) {
            alert('Please select a GPIO pin first');
            return;
        }

        console.log('Configuring pin:', mode);
        try {
            const response = await fetch('/gpio/api/configure', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    pin: this.selectedPin,
                    mode: mode
                })
            });
            
            const data = await response.json();
            if (!response.ok) {
                alert(`Failed to configure pin: ${data.error || 'Unknown error'}`);
            }
            // No need to refresh - WebSocket will send updates
        } catch (error) {
            console.error('Failed to configure pin:', error);
            alert('Failed to configure pin. Check console for details.');
        }
    }
    
    async togglePinState(pin, newState) {
        console.log('Toggling pin state:', pin, newState);
        try {
            // Use cached pin info instead of making a request
            const pinInfo = this.pins.find(p => p.number === pin);
            
            if (!pinInfo || !pinInfo.configured || pinInfo.mode !== 'OUT') {
                alert('This pin is not configured as an output pin');
                return;
            }
            
            const response = await fetch('/gpio/api/state', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    pin: pin,
                    state: newState
                })
            });
            
            const data = await response.json();
            if (!response.ok) {
                alert(`Failed to set pin state: ${data.error || 'Unknown error'}`);
            }
            // No need to refresh - WebSocket will send updates
        } catch (error) {
            console.error('Failed to set pin state:', error);
            alert('Failed to set pin state. Check console for details.');
        }
    }
    
    setupEventListeners() {
        const pinSelect = document.getElementById('gpio-pin-select');
        const setInput = document.getElementById('set-input');
        const setOutput = document.getElementById('set-output');
        
        if (pinSelect) {
            pinSelect.addEventListener('change', (e) => {
                this.selectedPin = parseInt(e.target.value);
            });
        }
        
        if (setInput) {
            setInput.addEventListener('click', () => {
                this.configurePin('IN');
            });
        }
        
        if (setOutput) {
            setOutput.addEventListener('click', () => {
                this.configurePin('OUT');
            });
        }
    }
} 