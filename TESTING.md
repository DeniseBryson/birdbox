# Testing BirdsOS

## Manual Testing with curl

1. Start the server:
```bash
python app.py
```

2. Run the curl test script:
```bash
./test_routes.sh
```

This will test all endpoints and display their responses.

## Automated Testing

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Run the tests:
```bash
pytest tests/test_routes.py -v
```

## Test Coverage

The tests verify:
- All main UI routes return 200 status
- All API endpoints return valid JSON responses
- Basic response structure for each endpoint
- WebSocket endpoints existence (connection testing in separate suite)

## Adding New Tests

1. For new UI routes:
   - Add route test in `tests/test_routes.py`
   - Verify template existence
   - Check response status

2. For new API endpoints:
   - Add endpoint test in `tests/test_routes.py`
   - Verify JSON response structure
   - Test all HTTP methods

3. For WebSocket endpoints:
   - Add connection test
   - Test message handling
   - Test disconnection handling 