import { test, expect } from '@playwright/test';
import { MapHelpers, APIDebugger, takeDebugScreenshot } from '../fixtures/test-helpers';

test.describe('Route Planning', () => {
  test('should plan route for drawn rectangle in Berkeley', async ({ page }) => {
    // Initialize helpers
    const mapHelpers = new MapHelpers(page);
    const apiDebugger = new APIDebugger(page);

    console.log('=== Starting Route Planning Test ===');
    
    // Navigate to the app
    console.log('1. Navigating to application...');
    await page.goto('/');
    
    // Wait for map to load
    console.log('2. Waiting for map to load...');
    await mapHelpers.waitForMapLoad();
    await takeDebugScreenshot(page, 'map-loaded');
    
    // Verify initial state
    console.log('3. Verifying initial state...');
    await expect(page.locator('.control-panel')).toBeVisible();
    await expect(page.locator('.drawing-toolbar')).toBeVisible();
    
    // Draw a rectangle on the map
    console.log('4. Drawing rectangle on map...');
    // Draw rectangle over Newton, MA streets area
    // Center of map is at Newton (42.3360, -71.2092), drawing near center
    await mapHelpers.drawRectangle(600, 350, 700, 400);
    await takeDebugScreenshot(page, 'rectangle-drawn');
    
    // Verify rectangle was drawn
    console.log('5. Verifying rectangle is visible...');
    const drawnRectangle = page.locator('.leaflet-interactive[d*="M"]');
    await expect(drawnRectangle).toBeVisible({ timeout: 5000 });
    
    // Click Plan Route button
    console.log('6. Clicking Plan Route button...');
    const planButton = page.locator('button:has-text("Plan Route")');
    await expect(planButton).toBeEnabled();
    
    // Set up promise to wait for API response (60s timeout for route calculation)
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/plan-route'),
      { timeout: 60000 }
    );
    
    await planButton.click();
    await takeDebugScreenshot(page, 'plan-route-clicked');
    
    // Wait for API response
    console.log('7. Waiting for API response...');
    const response = await responsePromise;
    
    console.log(`API Response Status: ${response.status()}`);
    const responseBody = await response.text();
    
    if (response.status() !== 200) {
      console.error('=== ERROR RESPONSE ===');
      console.error('Status:', response.status());
      console.error('Body:', responseBody);
      
      // Get last error from debugger
      const lastError = apiDebugger.getLastError();
      if (lastError) {
        console.error('Last Error Details:', JSON.stringify(lastError, null, 2));
      }
      
      // Get last request
      const lastRequest = apiDebugger.getLastRequest();
      if (lastRequest) {
        console.error('Last Request Details:', JSON.stringify(lastRequest, null, 2));
      }
      
      await takeDebugScreenshot(page, 'error-state');
    }
    
    // Check for success or error
    if (response.status() === 200) {
      console.log('8. Route planning successful!');
      
      // Wait for route to be displayed
      await page.waitForSelector('.leaflet-interactive[stroke="blue"]', { timeout: 10000 });
      await takeDebugScreenshot(page, 'route-displayed');
      
      // Verify route statistics are shown
      await expect(page.locator('.stats:has-text("Route Statistics")')).toBeVisible();
    } else {
      // Log all debugging information
      console.log('=== DEBUGGING INFORMATION ===');
      console.log('All Requests:', JSON.stringify(apiDebugger.getAllRequests(), null, 2));
      console.log('All Responses:', JSON.stringify(apiDebugger.getAllResponses(), null, 2));
      
      throw new Error(`Route planning failed with status ${response.status()}: ${responseBody}`);
    }
  });

  test('should handle place name search', async ({ page }) => {
    const apiDebugger = new APIDebugger(page);
    
    console.log('=== Testing Place Name Search ===');
    
    await page.goto('/');
    await page.waitForSelector('.control-panel');
    
    // Enter place name
    const placeInput = page.locator('input[placeholder*="place name"]');
    await placeInput.fill('Berkeley, California, USA');
    
    // Click search
    const searchButton = page.locator('button:has-text("Search Place")');
    
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/plan-route/place'),
      { timeout: 30000 }
    );
    
    await searchButton.click();
    
    const response = await responsePromise;
    console.log(`Place search response: ${response.status()}`);
    
    if (response.status() !== 200) {
      const body = await response.text();
      console.error('Place search error:', body);
      throw new Error(`Place search failed: ${body}`);
    }
  });

  test('should clear drawings', async ({ page }) => {
    const mapHelpers = new MapHelpers(page);
    
    await page.goto('/');
    await mapHelpers.waitForMapLoad();
    
    // Draw a shape
    await mapHelpers.drawRectangle(350, 350, 550, 450);
    
    // Verify shape exists
    await expect(page.locator('.leaflet-interactive[d*="M"]')).toBeVisible();
    
    // Clear drawings
    await mapHelpers.clearDrawings();
    
    // Verify shape is gone
    await expect(page.locator('.leaflet-interactive[d*="M"]')).not.toBeVisible();
  });
});