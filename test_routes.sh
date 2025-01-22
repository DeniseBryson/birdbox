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
    echo -n "Testing $method $endpoint... "
    
    response=$(curl -s -X $method -w "%{http_code}" "$BASE_URL$endpoint")
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
test_endpoint "/maintenance"
test_endpoint "/analytics"

echo -e "\nTesting API Routes..."
test_endpoint "/api/v1/system/status"
test_endpoint "/api/v1/system/health"
test_endpoint "/api/v1/camera/stream"
test_endpoint "/api/v1/hardware/gpio/status"
test_endpoint "/api/v1/hardware/motors/status"
test_endpoint "/api/v1/config/profiles"
test_endpoint "/api/v1/config/settings"
test_endpoint "/api/v1/maintenance/food-level"
test_endpoint "/api/v1/maintenance/storage/status"
test_endpoint "/api/v1/analytics/statistics" 