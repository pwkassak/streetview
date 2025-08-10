# Page snapshot

```yaml
- img
- button "Zoom in"
- button "Zoom out"
- link "Leaflet":
  - /url: https://leafletjs.com
- text: ©
- link "OpenStreetMap":
  - /url: https://www.openstreetmap.org/copyright
- text: contributors
- button "Draw Rectangle":
  - img
- button "Draw Circle":
  - img
- button "Draw Polygon":
  - img
- button "Clear Drawings":
  - img
- heading "StreetView Route Planner" [level=2]
- heading "Region Selection" [level=3]
- text: "Use the drawing tools on the map to select a region:"
- list:
  - listitem: "Rectangle: Draw a bounding box"
  - listitem: "Circle: Select area around a point"
  - listitem: "Polygon: Draw custom area"
- textbox "Or enter a place name..."
- button "Search Place"
- heading "Network Type" [level=3]
- combobox:
  - option "Drive" [selected]
  - option "Walk"
  - option "Bike"
- button "Plan Route"
- text: "Error: Request failed with status code 500"
```