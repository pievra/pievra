#!/bin/bash
set -e
echo "=== Installing Prebid Server ==="

# Install Go if not present
if ! command -v go &>/dev/null; then
    echo "Installing Go..."
    wget -q https://go.dev/dl/go1.21.6.linux-amd64.tar.gz -O /tmp/go.tar.gz
    rm -rf /usr/local/go
    tar -C /usr/local -xzf /tmp/go.tar.gz
    export PATH=$PATH:/usr/local/go/bin
    echo 'export PATH=$PATH:/usr/local/go/bin' >> /root/.bashrc
fi
go version

# Clone Prebid Server
echo "Cloning Prebid Server..."
if [ ! -d /opt/prebid-server ]; then
    git clone --depth=1 https://github.com/prebid/prebid-server.git /opt/prebid-server
fi

cd /opt/prebid-server

# Build Prebid Server
echo "Building Prebid Server..."
export PATH=$PATH:/usr/local/go/bin
go build -o prebid-server .
echo "Build complete: $(./prebid-server --version 2>&1 | head -1)"

# Create minimal config
mkdir -p /opt/prebid-server/config
cat > /opt/prebid-server/pievra.yaml << 'YAML'
port: 8080
admin_port: 6060
host: "127.0.0.1"
max_request_size: 1048576
gdpr:
  enabled: false
  default_value: "1"
ccpa:
  enforce: false
currency_converter:
  fetch_url: ""
  fetch_interval_ms: 0
metrics:
  influxdb:
    enabled: false
bidderInfos:
  pubmatic:
    enabled: true
  appnexus:
    enabled: true
  rubicon:
    enabled: true
  openx:
    enabled: true
  ix:
    enabled: true
YAML

echo "Prebid Server configured"
