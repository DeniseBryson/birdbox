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
            const message = JSON.parse(event.data);
            console.log('WebSocket message received:', message);
            if (message.type === 'gpio_init') {
                console.log('got init:', message);
                // Update our cache
                if (message.data.pins) {
                    this.pins = message.data.pins;
                    console.log('initializing pins with:', this.pins);
                    if (!this.dropdownPopulated) {
                        this.populatePinDropdown(this.pins);
                        this.dropdownPopulated = true;
                    }
                    this.updateOverviewTable(this.pins);
                }
                if (message.data.states) {
                    // Update specific pin states
                    Object.entries(message.data.states).forEach(([pin, state]) => {
                        const pinObj = this.pins.find(p => p.number === parseInt(pin));
                        if (pinObj) {
                            pinObj.state = state;
                            this.updatePinStates([pinObj]);
                        }
                    });
                }
            }
            if (message.type === 'gpio_update') {
                console.log('got update:', message);
                // Update specific pin states
                Object.entries(message.data).forEach(([pin, state]) => {
                    const pinObj = this.pins.find(p => p.number === parseInt(pin));
                    if (pinObj) {
                        pinObj.state = state;
                        this.updatePinStates([pinObj]);
                    }
                });
            }
            if (message.type === 'gpio_pin_update') {
                console.log('got pin update:', message);
                // Update specific pin states
                const pinObj = this.pins.find(p => p.number === parseInt(message.data.pin));
                console.log('updating pin from pin update:', pinObj);
                if (pinObj) {
                    pinObj.state = message.data.state;
                    this.updatePinStates([pinObj]);
                    this.updateTableRow(pinObj);
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
            option.textContent = `GPIO ${pin.number} (${pin.configured ? pin.mode === 'IN' ? 'Input' : 'Output' : 'Unconfigured'})`;
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
            tr.setAttribute('data-pin', pin.number);
            tr.innerHTML = `
                <td class="pin-number">GPIO ${pin.number}</td>
                <td class="pin-mode">${pin.configured ? pin.mode === 'IN' ? 'Input' : 'Output' : 'Unconfigured'}</td>
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

        
        try {
            const response = await fetch('/gpio/api/configure', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    pin: this.selectedPin,
                    mode: mode  // Should be exactly 'IN' or 'OUT'
                })
            });
            
            const data = await response.json();
            if (!response.ok) {
                alert(`Failed to configure pin: ${data.error || 'Unknown error'}`);
                console.log('Failed to configure pin:', mode, data);
                return;
            }
            console.log('Successfully configured pin:', this.selectedPin, 'to mode:', mode);
            console.log('Pin configuration response:', data);  // Add this debug log

            // Update our cached pin data with the new configuration
            const pin = this.pins.find(p => p.number === this.selectedPin);
            if (pin) {
                pin.configured = true;
                pin.mode = data.mode;  // Make sure we use the mode from the server response
                pin.state = data.state;
                console.log('Updated pin data:', pin);  // Add this debug log
                this.updatePinStates([pin]);
                this.updateTableRow(pin);
                this.populatePinDropdown(this.pins);
            }
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
                console.log('Selected pin:', this.selectedPin);  // Add this debug log
            });
        }
        
        if (setInput) {
            setInput.addEventListener('click', () => {
                console.log('Setting pin as input');  // Add this debug log
                this.configurePin('IN');
            });
        }
        
        if (setOutput) {
            setOutput.addEventListener('click', () => {
                console.log('Setting pin as output');  // Add this debug log
                this.configurePin('OUT');
            });
        }
    }

    updateTableRow(pin) {
        console.log('Updating table row:', pin);
        const tbody = document.querySelector('#gpio-overview tbody');
        if (!tbody) {
            console.log('No tbody found');
            return;  // Guard clause
        }

        // Find existing row for this pin
        const existingRow = tbody.querySelector(`tr[data-pin="${pin.number}"]`);
        if (existingRow) {
            // Update the mode cell
            const modeCell = existingRow.querySelector('.pin-mode');
            if (modeCell) {
                modeCell.textContent = pin.configured ? 
                    (pin.mode === 'IN' ? 'Input' : 'Output') : 'Unconfigured';
            }

            // Update the state cell
            const stateCell = existingRow.querySelector('.pin-state');
            if (stateCell) {
                console.log(`Updating state cell to ${pin.state ? 'high' : 'low'} :`, stateCell);
                stateCell.innerHTML = `
                    <span class="state-indicator ${pin.state ? 'high' : 'low'}"></span>
                    <span class="state-text">${pin.state ? 'HIGH' : 'LOW'}</span>
                `;
            }
            
            // Update the actions cell
            const actionsCell = existingRow.querySelector('.pin-actions');
            if (actionsCell) {
                console.log(`Updating actions cell for mode ${pin.mode}:`, actionsCell);
                if (pin.configured && pin.mode === 'OUT') {
                    actionsCell.innerHTML = `
                        <button class="btn btn-sm btn-${pin.state ? 'success' : 'danger'} toggle-btn"
                                onclick="gpioController.togglePinState(${pin.number}, ${pin.state ? 0 : 1})">
                            Toggle
                        </button>
                    `;
                } else if (pin.mode === 'IN') {
                    actionsCell.innerHTML = 'Input Pin';
                } else {
                    actionsCell.innerHTML = '-';
                }
            }
        }
    }
} 