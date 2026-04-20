#!/bin/vbash

source /opt/vyatta/etc/functions/script-template

INTERFACE="eth0"

NEW_USER="admin"
NEW_PASS="password"

CONTROLLER_URL="http://192.168.2.19:8000/device/register"
# ==========================================

echo "start configuring VyOS..."

configure

echo "-> opening SSH port 22..."
set service ssh port '22'

echo "-> creating admin account: $NEW_USER ..."
set system login user $NEW_USER authentication plaintext-password "$NEW_PASS"

echo "-> commit & save..."
commit
save

exit
echo " finish ssh setup"

echo " ready to register to Controller..."

# get IP & MAC
IP=$(ip -4 addr show $INTERFACE | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

MAC=$(cat /sys/class/net/$INTERFACE/address)


if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    OS=$(uname -s)
fi

# get OS type
if grep -qi "vyos" /etc/*release 2>/dev/null; then
    OS="vyos"
fi


echo "Interface: $INTERFACE"
echo "IP: $IP"
echo "MAC: $MAC"
echo "OS: $OS"


# JSON Payload
JSON_PAYLOAD=$(cat <<EOF
{
  "ip_address": "$IP",
  "mac": "$MAC",
  "os_type": "$OS",
  "status": "register",
  "device_type":"router"
}
EOF
)

echo "-> payload: $JSON_PAYLOAD"

# 4. send request
curl -k -X POST \
     -H "Content-Type: application/json" \
     -d "$JSON_PAYLOAD" \
     "$CONTROLLER_URL"



