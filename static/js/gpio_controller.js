var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var GPIOMessageType;
(function (GPIOMessageType) {
    GPIOMessageType["GPIO_UPDATE"] = "gpio_update";
    GPIOMessageType["GPIO_PIN_UPDATE"] = "gpio_pin_update";
    GPIOMessageType["PING"] = "ping";
})(GPIOMessageType || (GPIOMessageType = {}));
class GPIOController {
    constructor() {
        this.selectedPin = null;
        this.availablePins = [];
        this.setupEventListeners();
        this.setupWebSocket();
    }
    onUpdateMessage(message) {
        console.log('Handling update message:', message);
        if (message.data.pins) {
            this.availablePins = message.data.pins;
            console.log('initializing pins with:', this.availablePins);
            this.populatePinDropdown(this.availablePins);
            this.updateOverviewTable(this.availablePins);
        }
    }
    onPinUpdateMessage(message) {
        console.log('Handling pin update message:', message);
        if (message.data.pin === undefined || message.data.state === undefined) {
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
    isValidMessage(message) {
        const isValid = message.hasOwnProperty('type') && message.hasOwnProperty('data');
        if (!isValid) {
            console.error('Invalid message received:', message);
        }
        return isValid;
    }
    setupWebSocket() {
        const ws = new WebSocket(`ws://${window.location.host}/ws/gpio-updates`);
        console.log('WebSocket opened');
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (!this.isValidMessage(message)) {
                console.error('Invalid message received:', message);
                return;
            }
            const gpioMessage = message;
            switch (gpioMessage.type) {
                case GPIOMessageType.GPIO_UPDATE:
                    const updateMessage = gpioMessage;
                    this.onUpdateMessage(updateMessage);
                    break;
                case GPIOMessageType.GPIO_PIN_UPDATE:
                    const pinUpdateMessage = gpioMessage;
                    this.onPinUpdateMessage(pinUpdateMessage);
                    break;
            }
        };
        ws.onclose = () => {
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
        var _a;
        const select = document.getElementById('gpio-pin-select');
        if (!select)
            return;
        const currentValue = ((_a = this.selectedPin) === null || _a === void 0 ? void 0 : _a.number.toString()) || '';
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
    updatePinStates(pins) {
        for (const pin of pins) {
            this.updatePinStatus(pin);
        }
    }
    updatePinStatus(pin) {
        console.log('Updating pin status:', pin);
        const indicator = document.querySelector('.state-indicator');
        const text = document.querySelector('.state-text');
        if (!indicator || !text) {
            console.log('No indicator or text found in HTML Document');
            return;
        }
        indicator.className = 'state-indicator';
        indicator.classList.add(pin.state);
        const state = pin.state === 'HIGH' ? ' [HIGH]' : ' [LOW]';
        const stateText = pin.mode === 'UNDEFINED' ? '' : state;
        text.textContent = `${pin.mode}${stateText}`;
    }
    updateTableRow(pin) {
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
                }
                else if (pin.mode === 'IN') {
                    actionsCell.innerHTML = 'Input Pin';
                }
                else {
                    actionsCell.innerHTML = '-';
                }
            }
        }
    }
    updateOverviewTable(pins) {
        const tbody = document.querySelector('#gpio-overview tbody');
        if (!tbody)
            return;
        console.log('Updating overview table:', pins);
        tbody.innerHTML = '';
        pins.sort((a, b) => a.number - b.number).forEach(pin => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-pin', pin.number.toString());
            tr.innerHTML = `
                <td class="pin-number">GPIO ${pin.number}</td>
                <td class="pin-mode">${pin.mode}</td>
                <td class="pin-state">
                    <span class="state-indicator ${pin.state ? 'HIGH' : 'LOW'}"></span>
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
    configurePin(mode) {
        return __awaiter(this, void 0, void 0, function* () {
            if (!this.selectedPin) {
                alert('Please select a GPIO pin first');
                return;
            }
            console.log('Configuring pin:', mode);
            try {
                const response = yield fetch('/gpio/api/configure', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        pin: this.selectedPin.number,
                        mode: mode
                    })
                });
                const data = yield response.json();
                if (!response.ok || data.status === 'error') {
                    alert(`Failed to configure pin: ${data.errorMsg || 'Unknown error'}`);
                    console.log('Failed to configure pin:', mode, data);
                    return;
                }
                const pin = this.availablePins.find(p => p.number === data.number);
                if (!pin) {
                    console.error('Pin not found in available pins:', this.availablePins);
                    return;
                }
                pin.mode = data.mode;
                pin.state = data.state;
                this.selectedPin = pin;
                this.updatePinStates([this.selectedPin]);
                this.updateTableRow(this.selectedPin);
                this.populatePinDropdown(this.availablePins);
            }
            catch (error) {
                console.error('Failed to configure pin:', error);
                alert('Failed to configure pin. Check console for details.');
            }
        });
    }
    togglePinState(pin) {
        return __awaiter(this, void 0, void 0, function* () {
            console.log('Toggling pin state:', pin);
            try {
                const pinInfo = this.availablePins.find(p => p.number === pin);
                if (!pinInfo || pinInfo.mode !== 'OUT') {
                    if (!pinInfo) {
                        alert(`Pin ${pin} not found in available pins: ${this.availablePins.map(p => p.number).join(', ')}`);
                    }
                    else if (pinInfo.mode !== 'OUT') {
                        alert(`Pin ${pin} is configured as ${pinInfo.mode} and not an output pin`);
                    }
                    return;
                }
                console.error('Pin current State', pinInfo.state);
                const newState = pinInfo.state === 1 ? 0 : 1;
                console.error('Pin new State', newState);
                const response = yield fetch('/gpio/api/state', {
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
                const data = yield response.json();
                if (!response.ok) {
                    alert(`Failed to set pin state: ${data.error || 'Unknown error'}`);
                }
            }
            catch (error) {
                console.error('Failed to set pin state:', error);
                alert('Failed to set pin state. Check console for details.');
            }
        });
    }
    setupEventListeners() {
        const pinSelect = document.getElementById('gpio-pin-select');
        const setInput = document.getElementById('set-input');
        const setOutput = document.getElementById('set-output');
        if (pinSelect) {
            pinSelect.addEventListener('change', (e) => {
                const target = e.target;
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
window.gpioController = new GPIOController();
