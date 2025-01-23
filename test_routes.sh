#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

BASE_URL="http://localhost:5000"

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local method=${2:-GET}
    local data=${3:-""}
    
    echo -n "Testing $method $endpoint... "
    
    if [ -n "$data" ]; then
        response=$(curl -s -X $method -H "Content-Type: application/json" -d "$data" -w "%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -X $method -w "%{http_code}" "$BASE_URL$endpoint")
    fi
    
    http_code=${response: -3}
    response_body=${response:0:${#response}-3}
    
    if [ "$http_code" == "200" ]; then
        echo -e "${GREEN}OK${NC}"
        echo "Response: $response_body"
    else
        echo -e "${RED}FAILED${NC} (HTTP $http_code)"
        echo "Response: $response_body"
    fi
    echo "----------------------------------------"
}

echo "Testing Main Routes..."
test_endpoint "/"
test_endpoint "/camera"
test_endpoint "/hardware"
test_endpoint "/config"

echo -e "\nTesting Camera API Routes..."
test_endpoint "/api/v1/camera/status"
test_endpoint "/api/v1/camera/initialize/0" "POST"
test_endpoint "/api/v1/camera/stop" "POST"

echo -e "\nTesting GPIO API Routes..."
test_endpoint "/gpio/"
test_endpoint "/gpio/api/pins"
test_endpoint "/gpio/api/configure" "POST" '{"pin": 18, "mode": "OUT"}'
test_endpoint "/gpio/api/state" "POST" '{"pin": 18, "state": 1}'
test_endpoint "/gpio/api/state" "POST" '{"pin": 18, "state": 0}'
test_endpoint "/gpio/api/cleanup" "POST"

echo -e "\nTesting System API Routes..."
test_endpoint "/api/v1/system/status"
test_endpoint "/api/v1/system/health"

echo -e "\nTest Complete!" 