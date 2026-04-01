#!/bin/sh
# Prints the local LAN IP address of this machine (for use with mobile MQTT clients).
# Works on macOS (ipconfig) and Linux (ip/hostname fallbacks).

if command -v ipconfig >/dev/null 2>&1; then
    # macOS: find the IP of the active Wi-Fi or Ethernet interface
    IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
else
    # Linux: pick the first non-loopback IPv4 address
    IP=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}')
    # fallback
    [ -z "$IP" ] && IP=$(hostname -I 2>/dev/null | awk '{print $1}')
fi

if [ -z "$IP" ]; then
    echo "Could not determine LAN IP address." >&2
    exit 1
fi

echo "$IP"
echo ""
echo "Use this address in your MQTT app:"
echo "  Host: $IP"
echo "  Port: 1883"
echo "  Topic: home/network/status"
