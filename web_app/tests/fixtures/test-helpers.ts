import { Page, expect } from '@playwright/test';

export class MapHelpers {
  constructor(private page: Page) {}

  async waitForMapLoad() {
    // Wait for Leaflet map container
    await this.page.waitForSelector('.leaflet-container', { timeout: 30000 });
    // Wait for tiles to load
    await this.page.waitForSelector('.leaflet-tile-loaded', { timeout: 30000 });
    // Give it a moment for full initialization
    await this.page.waitForTimeout(1000);
  }

  async drawRectangle(x1: number, y1: number, x2: number, y2: number) {
    console.log(`Drawing rectangle from (${x1}, ${y1}) to (${x2}, ${y2})`);
    
    // Click rectangle tool
    await this.page.click('[title="Draw Rectangle"]');
    await this.page.waitForTimeout(500);
    
    // Get map container
    const map = this.page.locator('.leaflet-container');
    
    // Click first corner
    await map.click({ position: { x: x1, y: y1 } });
    await this.page.waitForTimeout(500);
    
    // Click second corner
    await map.click({ position: { x: x2, y: y2 } });
    await this.page.waitForTimeout(500);
  }

  async drawCircle(centerX: number, centerY: number, radiusX: number, radiusY: number) {
    console.log(`Drawing circle at (${centerX}, ${centerY}) with radius to (${radiusX}, ${radiusY})`);
    
    // Click circle tool
    await this.page.click('[title="Draw Circle"]');
    await this.page.waitForTimeout(500);
    
    const map = this.page.locator('.leaflet-container');
    
    // Click center
    await map.click({ position: { x: centerX, y: centerY } });
    await this.page.waitForTimeout(500);
    
    // Click to set radius
    await map.click({ position: { x: radiusX, y: radiusY } });
    await this.page.waitForTimeout(500);
  }

  async clearDrawings() {
    await this.page.click('[title="Clear Drawings"]');
    await this.page.waitForTimeout(500);
  }
}

export class APIDebugger {
  private requests: any[] = [];
  private responses: any[] = [];

  constructor(private page: Page) {
    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Capture requests
    this.page.on('request', request => {
      if (request.url().includes('/api/')) {
        const requestInfo = {
          url: request.url(),
          method: request.method(),
          headers: request.headers(),
          postData: request.postData(),
          timestamp: new Date().toISOString()
        };
        this.requests.push(requestInfo);
        console.log('API Request:', requestInfo);
      }
    });

    // Capture responses
    this.page.on('response', async response => {
      if (response.url().includes('/api/')) {
        let responseBody = null;
        try {
          responseBody = await response.text();
        } catch (e) {
          responseBody = 'Could not read response body';
        }

        const responseInfo = {
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
          headers: response.headers(),
          body: responseBody,
          timestamp: new Date().toISOString()
        };
        this.responses.push(responseInfo);
        
        console.log('API Response:', {
          url: responseInfo.url,
          status: responseInfo.status,
          statusText: responseInfo.statusText
        });
        
        if (responseInfo.status >= 400) {
          console.error('Error Response Body:', responseBody);
        }
      }
    });

    // Capture console errors
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('Browser Console Error:', msg.text());
      }
    });

    // Capture page errors
    this.page.on('pageerror', error => {
      console.error('Page Error:', error.message);
    });
  }

  getLastError() {
    const errorResponses = this.responses.filter(r => r.status >= 400);
    return errorResponses[errorResponses.length - 1];
  }

  getLastRequest() {
    return this.requests[this.requests.length - 1];
  }

  getAllRequests() {
    return this.requests;
  }

  getAllResponses() {
    return this.responses;
  }
}

export async function takeDebugScreenshot(page: Page, name: string) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const path = `debug/screenshot-${name}-${timestamp}.png`;
  await page.screenshot({ path, fullPage: true });
  console.log(`Screenshot saved: ${path}`);
  return path;
}