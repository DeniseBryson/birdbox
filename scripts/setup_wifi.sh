#!/bin/bash

# Set up logging
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="wifi_setup_${TIMESTAMP}.log"
exec 1> >(tee -a "${LOG_FILE}") 2>&1

echo "WiFi Setup Script for Raspberry Pi"
echo "================================="
echo "Setup started at: $(date)"
echo "Log file: ${LOG_FILE}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Error: This script must be run on a Raspberry Pi"
    exit 1
fi

# Install NetworkManager if not present
echo "Checking NetworkManager installation..."
if ! command -v nmcli &> /dev/null; then
    echo "NetworkManager not found. Installing..."
    apt-get update
    apt-get install -y network-manager
    
    # Enable NetworkManager
    systemctl enable NetworkManager
    systemctl start NetworkManager
    
    # Wait for NetworkManager to start
    echo "Waiting for NetworkManager to start..."
    sleep 5
else
    echo "NetworkManager is already installed"
fi

# Function to add WiFi connection
add_wifi_connection() {
    local name="$1"
    local ssid="$2"
    local password="$3"
    local priority="$4"

    echo "Setting up WiFi connection: $name (SSID: $ssid, Priority: $priority)"
    
    # Check if connection already exists
    if nmcli connection show "$name" &> /dev/null; then
        echo "Connection '$name' already exists. Removing..."
        nmcli connection delete "$name"
    fi
    
    # Add new connection
    if nmcli connection add \
        type wifi \
        con-name "$name" \
        ifname wlan0 \
        ssid "$ssid" \
        wifi-sec.key-mgmt wpa-psk \
        wifi-sec.psk "$password" \
        connection.autoconnect yes \
        connection.autoconnect-priority "$priority"; then
        echo "Successfully added connection: $name"
        return 0
    else
        echo "Failed to add connection: $name"
        return 1
    fi
}

# Function to verify connection
verify_connection() {
    local name="$1"
    echo "Verifying connection: $name"
    
    if nmcli connection show --active | grep -q "$name"; then
        echo "✓ Connection '$name' is active"
        return 0
    else
        echo "! Connection '$name' is not active"
        return 1
    fi
}

# Function to read networks from config file
read_networks_from_config() {
    local config_file="$1"
    local networks=()
    
    # Read non-empty, non-comment lines
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^[[:space:]]*# && -n "$line" ]]; then
            networks+=("$line")
        fi
    done < "$config_file"
    
    echo "${networks[@]}"
}

# Main setup
echo "Starting WiFi setup..."

# Store current connection info
CURRENT_SSID=$(iwgetid -r)
echo "Current WiFi SSID: $CURRENT_SSID"

# Initialize counter for network naming
NETWORK_COUNT=1

# Check for configuration file
CONFIG_FILE="wifi_networks.conf"
if [ -f "$CONFIG_FILE" ]; then
    echo "Found configuration file: $CONFIG_FILE"
    echo "Would you like to:"
    echo "1. Use networks from configuration file"
    echo "2. Enter networks manually"
    echo "3. Use both (config file + manual entry)"
    read -p "Enter your choice (1-3): " SETUP_CHOICE
    
    case $SETUP_CHOICE in
        1)
            # Read from config file only
            while IFS=, read -r SSID PASSWORD PRIORITY || [ -n "$SSID" ]; do
                # Skip comments and empty lines
                [[ "$SSID" =~ ^[[:space:]]*# || -z "$SSID" ]] && continue
                
                # Remove any whitespace
                SSID=$(echo "$SSID" | xargs)
                PASSWORD=$(echo "$PASSWORD" | xargs)
                PRIORITY=$(echo "$PRIORITY" | xargs)
                
                if add_wifi_connection "WiFi${NETWORK_COUNT}" "$SSID" "$PASSWORD" "$PRIORITY"; then
                    echo "WiFi${NETWORK_COUNT} configured successfully"
                    ((NETWORK_COUNT++))
                fi
            done < "$CONFIG_FILE"
            ;;
            
        2)
            # Manual entry only
            echo "Please enter WiFi network details."
            echo "Press Enter for SSID or Ctrl+C to finish adding networks."
            
            while true; do
                echo ""
                echo "WiFi Network $NETWORK_COUNT"
                echo "-------------"
                read -p "Enter network name (SSID or Enter to finish): " SSID
                
                [ -z "$SSID" ] && break
                
                read -s -p "Enter password: " PASSWORD
                echo ""
                read -p "Enter priority (lower number = higher priority): " PRIORITY
                
                if add_wifi_connection "WiFi${NETWORK_COUNT}" "$SSID" "$PASSWORD" "$PRIORITY"; then
                    echo "WiFi${NETWORK_COUNT} configured successfully"
                    ((NETWORK_COUNT++))
                fi
            done
            ;;
            
        3)
            # First read from config file
            while IFS=, read -r SSID PASSWORD PRIORITY || [ -n "$SSID" ]; do
                # Skip comments and empty lines
                [[ "$SSID" =~ ^[[:space:]]*# || -z "$SSID" ]] && continue
                
                # Remove any whitespace
                SSID=$(echo "$SSID" | xargs)
                PASSWORD=$(echo "$PASSWORD" | xargs)
                PRIORITY=$(echo "$PRIORITY" | xargs)
                
                if add_wifi_connection "WiFi${NETWORK_COUNT}" "$SSID" "$PASSWORD" "$PRIORITY"; then
                    echo "WiFi${NETWORK_COUNT} configured successfully"
                    ((NETWORK_COUNT++))
                fi
            done < "$CONFIG_FILE"
            
            # Then allow manual entry for additional networks
            echo ""
            echo "Add additional networks"
            echo "Press Enter for SSID or Ctrl+C to finish adding networks."
            
            while true; do
                echo ""
                echo "Additional WiFi Network $NETWORK_COUNT"
                echo "-------------"
                read -p "Enter network name (SSID or Enter to finish): " SSID
                
                [ -z "$SSID" ] && break
                
                read -s -p "Enter password: " PASSWORD
                echo ""
                read -p "Enter priority (lower number = higher priority): " PRIORITY
                
                if add_wifi_connection "WiFi${NETWORK_COUNT}" "$SSID" "$PASSWORD" "$PRIORITY"; then
                    echo "WiFi${NETWORK_COUNT} configured successfully"
                    ((NETWORK_COUNT++))
                fi
            done
            ;;
            
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac
else
    echo "No configuration file found at: $CONFIG_FILE"
    echo "Proceeding with manual entry..."
    
    # Manual entry only
    echo "Please enter WiFi network details."
    echo "Press Enter for SSID or Ctrl+C to finish adding networks."
    
    while true; do
        echo ""
        echo "WiFi Network $NETWORK_COUNT"
        echo "-------------"
        read -p "Enter network name (SSID or Enter to finish): " SSID
        
        [ -z "$SSID" ] && break
        
        read -s -p "Enter password: " PASSWORD
        echo ""
        read -p "Enter priority (lower number = higher priority): " PRIORITY
        
        if add_wifi_connection "WiFi${NETWORK_COUNT}" "$SSID" "$PASSWORD" "$PRIORITY"; then
            echo "WiFi${NETWORK_COUNT} configured successfully"
            ((NETWORK_COUNT++))
        fi
    done
fi

# Verify all connections
echo ""
echo "Verifying connections..."
nmcli connection show

# Show network status
echo ""
echo "Current network status:"
nmcli device status

# Save log file
echo ""
echo "Setup complete!"
echo "Log saved to: $LOG_FILE"

# Instructions for manual connection
echo ""
echo "To manually connect to a network:"
echo "nmcli connection up WiFi1|WiFi2|WiFi3"
echo ""
echo "To show all configured networks:"
echo "nmcli connection show"
echo ""
echo "To show active connection:"
echo "nmcli connection show --active"
echo ""
echo "To edit the configuration file:"
echo "nano wifi_networks.conf" 

