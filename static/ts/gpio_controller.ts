/**
 * GPIO Controller for BirdsOS
 * Handles all GPIO-related frontend functionality
 */

type PinMode = 'IN' | 'OUT' | 'UNDEFINED';
// TODO: FIX THIS
type PinState = 'LOW' | 'HIGH' | 0 | 1 | undefined;
enum GPIOMessageType {
    GPIO_UPDATE = 'gpio_update',
    GPIO_PIN_UPDATE = 'gpio_pin_update',
    PING = 'ping'
}

interface Pin {
    number: number;
    mode: PinMode;
    state: PinState;
}

interface GPIOMessage {
    type: GPIOMessageType;
    data: any;
}

interface GPIUpdateMessage extends GPIOMessage {
    type: GPIOMessageType.GPIO_UPDATE;
    data: {
        pins: Pin[];
    };
}

interface GPIPingMessage extends GPIOMessage {
    type: GPIOMessageType.PING;
    data: {};
}

interface GPIPinUpdateMessage extends GPIOMessage {
    type: GPIOMessageType.GPIO_PIN_UPDATE;
    data: {
        pin: number;
        state: PinState;
    };
}

interface ConfigureResponse extends Pin {
    status: 'success' | 'error';
    errorMsg?: string;
}
class GPIOController {
    private selectedPin: Pin | null;
    private availablePins: Pin[];

    constructor() {
        this.selectedPin = null;
        this.availablePins = [];  // Cache of pin states
        this.setupEventListeners();
        this.setupWebSocket();
    }

    private onUpdateMessage(message: GPIUpdateMessage): void {
        console.log('Handling update message:', message);
        if (message.data.pins) {
            this.availablePins = message.data.pins;
            console.log('initializing pins with:', this.availablePins);
            this.populatePinDropdown(this.availablePins);
            this.updateOverviewTable(this.availablePins);
        }           
    }

    private onPinUpdateMessage(message: GPIPinUpdateMessage): void {
        console.log('Handling pin update message:', message);
        if (message.data.pin === undefined || message.data.state === undefined){
            console.error('Invalid pin update message:', message);
            return;
        }
        
        const pinObj = this.availablePins.find(p => p.number === message.data.pin);
        if (!pinObj) {
            console.error('Pin not found:', message);
            return;
        }
        
        if (pinObj.state === message.data.state && pinObj.mode !== 'UNDEFINED') {
            console.log(`pin ${pinObj.number} is already in the desired state. Skipping change of UI`);
            return;
        }

        console.log(`updating pin ${pinObj.number} from ${pinObj.state} to ${message.data.state}`);
        pinObj.state = message.data.state;
        this.updatePinStates([pinObj]);
        this.updateTableRow(pinObj);
    }
    
    private isValidMessage(message: Object): boolean {
        const isValid = message.hasOwnProperty('type') && message.hasOwnProperty('data');
        if(!isValid){
            console.error('Invalid message received:', message);
        }
        return isValid;
    }

    private setupWebSocket(): void {
        const ws = new WebSocket(`ws://${window.location.host}/ws/gpio-updates`);
        console.log('WebSocket opened');
        
        ws.onmessage = (event: MessageEvent) => {
            const message: Object = JSON.parse(event.data);            
            if (!this.isValidMessage(message)) {
                console.error('Invalid message received:', message);
                return;
            }
            const gpioMessage: GPIOMessage = message as GPIOMessage;            
            switch (gpioMessage.type) {
                case GPIOMessageType.GPIO_UPDATE:
                    const updateMessage: GPIUpdateMessage = gpioMessage as GPIUpdateMessage;
                    this.onUpdateMessage(updateMessage);
                    break;
                case GPIOMessageType.GPIO_PIN_UPDATE:
                    const pinUpdateMessage: GPIPinUpdateMessage = gpioMessage as GPIPinUpdateMessage;
                    this.onPinUpdateMessage(pinUpdateMessage);
                    break;
            }      
          
        };

        ws.onclose = () => {
            console.log('WebSocket closed, attempting to reconnect...');
            setTimeout(() => this.setupWebSocket(), 2000);
        };
        
        ws.onerror = (error: Event) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onopen = () => {
            console.log('WebSocket connected');
        };
    }

    private populatePinDropdown(pins: Pin[]): void {
        const select = document.getElementById('gpio-pin-select') as HTMLSelectElement | null;
        if (!select) return;
        
        const currentValue = this.selectedPin?.number.toString() || '';
        
        select.innerHTML = '<option value="">Choose a pin...</option>';
        
        pins.sort((a, b) => a.number - b.number).forEach(pin => {
            const option = document.createElement('option');
            option.value = pin.number.toString();
            const pinState = pin.state === 'HIGH' ? 'HIGH' : 'LOW';
            const pinMode = pin.mode;
            option.textContent = `GPIO ${pin.number} (${pinMode}, ${pinState})`;
            if (pin.number.toString() === currentValue) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }
    
    private updatePinStates(pins: Pin[]): void {
        for (const pin of pins) {
            this.updatePinStatus(pin);
        }
    }
    
    private updatePinStatus(pin: Pin): void {
        console.log('Updating pin status:', pin);
        const indicator = document.querySelector('.state-indicator') as HTMLElement | null;
        const text = document.querySelector('.state-text') as HTMLElement | null;
        if (!indicator || !text) {
            console.log('No indicator or text found in HTML Document');
            return;
        }
        
        indicator.className = 'state-indicator';
        indicator.classList.add(pin.state===1?'HIGH': pin.state===0?'LOW':pin.state);
        const state = pin.state==='HIGH'?' [HIGH]':' [LOW]';
        const stateText = pin.mode === 'UNDEFINED' ? '' : state;
        text.textContent = `${pin.mode}${stateText}`;
    }
    
    private updateTableRow(pin: Pin): void {
        console.log('Updating table row:', pin);
        const tbody = document.querySelector('#gpio-overview tbody');
        if (!tbody) {
            console.log('No tbody found');
            return;
        }

        const existingRow = tbody.querySelector(`tr[data-pin="${pin.number}"]`);
        if (existingRow) {
            const modeCell = existingRow.querySelector('.pin-mode');
            if (modeCell) {
                modeCell.textContent = pin.mode;
            }

            const stateCell = existingRow.querySelector('.pin-state');
            if (stateCell) {
                stateCell.innerHTML = `
                    <span class="state-indicator ${pin.state ? 'HIGH' : 'LOW'}"></span>
                    <span class="state-text">${pin.state ? 'HIGH' : 'LOW'}</span>
                `;
            }
            
            const actionsCell = existingRow.querySelector('.pin-actions');
            if (actionsCell) {
                if (pin.mode === 'OUT') {
                    actionsCell.innerHTML = `
                        <button class="btn btn-sm btn-${pin.state === 'HIGH' ? 'success' : 'danger'} toggle-btn"
                                onclick="gpioController.togglePinState(${pin.number})">
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
    
    private updateOverviewTable(pins: Pin[]): void {
        const tbody = document.querySelector('#gpio-overview tbody');
        if (!tbody) return;

        console.log('Updating overview table:', pins);
        tbody.innerHTML = '';
        
        pins.sort((a, b) => a.number - b.number).forEach(pin => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-pin', pin.number.toString());
            tr.innerHTML = `
                <td class="pin-number">GPIO ${pin.number}</td>
                <td class="pin-mode">${pin.mode}</td>
                <td class="pin-state">
                    <span class="state-indicator ${pin.state ? 'HIGH' : 'LOW'} "></span>
                    <span class="state-text">${pin.state ? 'HIGH' : 'LOW'}</span>
                </td>
                <td class="pin-actions">
                    ${pin.mode === 'OUT' ? `
                        <button class="btn btn-sm btn-${pin.state === 'HIGH' ? 'success' : 'danger'} toggle-btn"
                                onclick="gpioController.togglePinState(${pin.number})">
                            Toggle
                        </button>
                    ` : pin.mode === 'IN' ? 'Input Pin' : '-'}
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    public async configurePin(mode: PinMode): Promise<void> {
        /**
         * Configure a pin to be an input or output
         * @param mode - The mode to configure the pin to (IN or OUT)
         * @returns void
         * @description This function configures the currentlyselected pin to be an input or output
         */

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
                    pin: this.selectedPin.number,
                    mode: mode
                })
            });
            
            const data: ConfigureResponse = await response.json();
            if (!response.ok || data.status === 'error') {
                alert(`Failed to configure pin: ${data.errorMsg || 'Unknown error'}`);
                console.log('Failed to configure pin:', mode, data);
                return;
            }

            const pin = this.availablePins.find(p => p.number === data.number);

            if(!pin){
                console.error('Pin not found in available pins:', this.availablePins);
                return;
            }

            pin.mode = data.mode;
            pin.state = data.state;
            this.selectedPin = pin;          

            this.updatePinStates([this.selectedPin]);
            this.updateTableRow(this.selectedPin);
            this.populatePinDropdown(this.availablePins);
                
        } catch (error) {
            console.error('Failed to configure pin:', error);
            alert('Failed to configure pin. Check console for details.');
        }
    }
    
    public async togglePinState(pin: number): Promise<void> {
        console.log('Toggling pin state:', pin);
        try {
            const pinInfo = this.availablePins.find(p => p.number === pin);
            
            if (!pinInfo || pinInfo.mode !== 'OUT') {
                if(!pinInfo){
                    alert(`Pin ${pin} not found in available pins: ${this.availablePins.map(p => p.number).join(', ')}`);
                }
                else if(pinInfo.mode !== 'OUT'){
                    alert(`Pin ${pin} is configured as ${pinInfo.mode} and not an output pin`);
                }
                return;
            }
            console.error('Pin current State', pinInfo.state);
            const newState = pinInfo.state === 1 ? 0 : 1;
            console.error('Pin new State', newState);
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
            
            console.log(`Successfully changed pin ${pin} state to ${newState}`);
            
            const data = await response.json();
            if (!response.ok) {
                alert(`Failed to set pin state: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Failed to set pin state:', error);
            alert('Failed to set pin state. Check console for details.');
        }
    }
    
    private setupEventListeners(): void {
        /**
         * Setup event listeners for the GPIO controller
         * @returns void
         * @description This function sets up event listeners for changing the selected pin and setting this pin to input or output
         */
        const pinSelect = document.getElementById('gpio-pin-select') as HTMLSelectElement | null;
        const setInput = document.getElementById('set-input') as HTMLButtonElement | null;
        const setOutput = document.getElementById('set-output') as HTMLButtonElement | null;
        
        if (pinSelect) {
            pinSelect.addEventListener('change', (e: Event) => {
                const target = e.target as HTMLSelectElement;
                const pinObj = this.availablePins.find(p => p.number === parseInt(target.value));
                if (!pinObj) {
                    console.error(`Selected pin ${target.value} not found in available pins: ${this.availablePins.map(p => p.number).join(', ')}`);
                    return;
                }
                this.selectedPin = pinObj;
                console.log('Selected pin in dropdown:', this.selectedPin);
            });
        }
        
        if (setInput) {
            setInput.addEventListener('click', () => {
                console.log('Setting pin as input');
                this.configurePin('IN');
            });
        }
        
        if (setOutput) {
            setOutput.addEventListener('click', () => {
                console.log('Setting pin as output');
                this.configurePin('OUT');
            });
        }
    }
}

// Make controller available globally
declare global {
    interface Window {
        gpioController: GPIOController;
    }
}

// Expose the class globally
window.gpioController = new GPIOController();