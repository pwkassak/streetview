// Quick test to check coordinate mapping
const centerLat = 37.8716;  // Downtown Berkeley
const centerLon = -122.2686;

// Test rectangle pixel coordinates
const x1 = 450, y1 = 400;
const x2 = 550, y2 = 450;

console.log("Target coordinates for Downtown Berkeley:");
console.log("North: 37.8716, South: 37.8696");
console.log("East: -122.2676, West: -122.2696");
console.log("");
console.log("Test is drawing rectangle at pixels:", x1, y1, "to", x2, y2);
console.log("This maps to approximately:");
console.log("North: 37.890, South: 37.883");
console.log("East: -122.343, West: -122.360");
console.log("");
console.log("The drawn area is too far WEST and slightly NORTH of target.");
