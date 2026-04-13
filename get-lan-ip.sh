#!/bin/sh
# Prints the local LAN IP addresses (WiFi and Ethernet) of this machine.
# Works on macOS (ipconfig/networksetup) and Linux (ip).

WIFI_IP=""
ETH_IP=""
USB_IP=""

if command -v ipconfig >/dev/null 2>&1; then
    # macOS: en0 is typically WiFi, en1+ may be Ethernet (or vice versa on some models).
    # Use networksetup to identify interface hardware ports when available.
    if command -v networksetup >/dev/null 2>&1; then
        WIFI_IFACE=$(networksetup -listallhardwareports 2>/dev/null | awk '/Wi-Fi|AirPort/{getline; print $2}')
        ETH_IFACE=$(networksetup -listallhardwareports 2>/dev/null | awk '/Ethernet/{getline; print $2; exit}')
        USB_IFACE=$(networksetup -listallhardwareports 2>/dev/null | awk  '/USB 10\/100\/1000 LAN/{getline; print $2; exit}')
    fi
    [ -n "$WIFI_IFACE" ] && WIFI_IP=$(ipconfig getifaddr "$WIFI_IFACE" 2>/dev/null)
    [ -n "$ETH_IFACE" ]  && ETH_IP=$(ipconfig getifaddr "$ETH_IFACE" 2>/dev/null)
    [ -n "$USB_IFACE" ]  && USB_IP=$(ipconfig getifaddr "$USB_IFACE" 2>/dev/null)

    # Fallback: probe common interface names if networksetup didn't resolve them
    if [ -z "$WIFI_IP" ] && [ -z "$ETH_IP" ] && [ -z "$USB_IP" ]; then
        WIFI_IP=$(ipconfig getifaddr en0 2>/dev/null)
        ETH_IP=$(ipconfig getifaddr en1 2>/dev/null)
    fi
else
    # Linux: identify WiFi (wlan* / wlp*) and Ethernet (eth* / enp* / ens*) interfaces
    if command -v ip >/dev/null 2>&1; then
        WIFI_IFACE=$(ip -o link show | awk -F': ' '$2 ~ /^wl/ {print $2; exit}')
        ETH_IFACE=$(ip -o link show | awk -F': ' '$2 ~ /^(eth|en[ps])/ {print $2; exit}')
        [ -n "$WIFI_IFACE" ] && WIFI_IP=$(ip -4 addr show "$WIFI_IFACE" 2>/dev/null | awk '/inet /{gsub(/\/.*/, "", $2); print $2; exit}')
        [ -n "$ETH_IFACE" ]  && ETH_IP=$(ip -4 addr show "$ETH_IFACE" 2>/dev/null | awk '/inet /{gsub(/\/.*/, "", $2); print $2; exit}')
    fi
fi

if [ -z "$WIFI_IP" ] && [ -z "$ETH_IP" ] && [ -z "$USB_IP" ]; then
    echo "Could not determine any LAN IP address." >&2
    exit 1
fi

print_entry() {
    LABEL="$1"
    ADDR="$2"
    if [ -n "$ADDR" ]; then
        echo "$LABEL IP : $ADDR"
    else
        echo "$LABEL IP : (not connected)"
    fi
}

print_entry "WiFi    " "$WIFI_IP"
print_entry "Ethernet" "$ETH_IP"
print_entry "USB LAN " "$USB_IP"
echo ""
echo "Use one of the above addresses in your MQTT app:"
echo "  Port: 1883"
echo "  Topic: home/network/status"
