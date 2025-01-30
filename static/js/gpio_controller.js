/**
 * GPIO Controller for BirdsOS
 * Handles all GPIO-related frontend functionality
 */
class GPIOController {
    constructor() {
        this.selectedPin = null;
        this.setupEventListeners();
        this.updatePinList();
        this.startStatusUpdates();
    }
    
    async updatePinList() {
        try {
            const response = await fetch('/gpio/api/pins');
            const data = await response.json();
            
            if (data.pins) {  // Check for pins array instead of status
                this.populatePinDropdown(data.pins);
                this.updatePinStates(data.pins);
                this.updateOverviewTable(data.pins);
            } else if (data.error) {
                console.error('Error fetching GPIO pins:', data.error);
            }
        } catch (error) {
            console.error('Failed to fetch GPIO pins:', error);
        }
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
            option.textContent = `GPIO ${pin.number} (${pin.configured ? pin.mode : 'Unconfigured'})`;
            if (pin.number.toString() === currentValue) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }
    
    updatePinStates(pins) {
        if (this.selectedPin) {
            const pin = pins.find(p => p.number === this.selectedPin);
            if (pin) {
                this.updatePinStatus(pin);
            }
        }
    }
    
    updatePinStatus(pin) {
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
        
        tbody.innerHTML = '';
        
        // Sort pins by number for consistent display
        pins.sort((a, b) => a.number - b.number).forEach(pin => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="pin-number">GPIO ${pin.number}</td>
                <td class="pin-mode">${pin.configured ? pin.mode : 'Unconfigured'}</td>
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
                    ` : '<span class="no-action">-</span>'}
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
                    mode: mode
                })
            });
            
            const data = await response.json();
            if (response.ok) {  // Check HTTP status instead of response data
                await this.updatePinList();  // Refresh all pins
            } else {
                alert(`Failed to configure pin: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Failed to configure pin:', error);
            alert('Failed to configure pin. Check console for details.');
        }
    }
    
    async togglePinState(pin, newState) {
        try {
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
            if (response.ok) {  // Check HTTP status instead of response data
                await this.updatePinList();  // Refresh all pins
            } else {
                alert(`Failed to set pin state: ${data.error || 'Unknown error'}`);
            }
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
                if (this.selectedPin) {
                    this.updatePinList();
                }
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
    
    startStatusUpdates() {
        // Update every 2 seconds
        setInterval(() => this.updatePinList(), 2000);
    }
} 