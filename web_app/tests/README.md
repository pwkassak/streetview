# StreetView Route Planner E2E Tests

End-to-end tests using Playwright to test and debug the StreetView Route Planner web application.

## Setup

1. Install dependencies:
```bash
cd streetview/web_app/tests
npm install
npm run playwright:install
```

2. Ensure the backend and frontend servers are running:
```bash
# Terminal 1
cd streetview/web_app/backend
conda activate streetview310
python app.py

# Terminal 2
cd streetview/web_app/frontend
npm run dev
```

Or let Playwright start them automatically (configured in playwright.config.ts).

## Running Tests

### Run all tests (headless)
```bash
npm test
```

### Debug mode (with browser visible)
```bash
npm run test:debug
```

### UI mode (interactive debugging)
```bash
npm run test:ui
```

### Run with headed browser
```bash
npm run test:headed
```

### View test report
```bash
npm run test:report
```

## Test Coverage

### Route Planning Test (`route-planning.spec.ts`)
Main test that reproduces the 500 error:
1. Loads the application
2. Waits for map initialization
3. Draws a rectangle on the Berkeley area
4. Clicks "Plan Route" button
5. Captures all API requests/responses
6. Logs detailed error information if it fails
7. Takes screenshots at each step

### Debugging Features

The tests include extensive debugging capabilities:

- **API Request/Response Logging**: All API calls are intercepted and logged
- **Console Error Capture**: Browser console errors are captured
- **Screenshots**: Automatic screenshots on failure and at key steps
- **Video Recording**: Full test execution video (on failure)
- **Network Tracing**: Complete network activity trace
- **Detailed Error Reporting**: Full request/response bodies for debugging

### Debug Output

Debug artifacts are saved in:
- `debug/` - Screenshots with timestamps
- `test-results/` - Playwright test artifacts
- `playwright-report/` - HTML test report
- Console output includes detailed API information

## Troubleshooting

### Test fails to find elements
- Increase timeouts in `playwright.config.ts`
- Check if selectors in tests match current UI

### Servers not starting
- Manually start backend and frontend
- Set `reuseExistingServer: true` in config

### 500 Error debugging
The test will output:
- Full request payload
- Response status and body
- Backend error details
- Screenshots of the error state

## Test Helpers

### MapHelpers
- `waitForMapLoad()` - Waits for Leaflet map to initialize
- `drawRectangle()` - Draws a rectangle on the map
- `drawCircle()` - Draws a circle on the map  
- `clearDrawings()` - Clears all drawn shapes

### APIDebugger
- Automatically captures all API requests/responses
- Logs errors to console
- Provides methods to retrieve error details

### Screenshot Helper
- `takeDebugScreenshot()` - Takes timestamped screenshots for debugging