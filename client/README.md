# FuseTester Web Client

A simple HTML dashboard for visualizing fuse monitoring data from the FuseTester HTTP server.

## Features

- **Interactive Voltage Charts** - Line graphs showing voltage readings over time
- **Date Range Filtering** - Select start/end dates with quick filter buttons
- **Fuse Selection** - Choose which fuses (3-64) to display on the graph
- **Server Health Check** - Test connection to HTTP server
- **Real-time Statistics** - Display reading counts, battery averages, and time ranges
- **Responsive Design** - Works on desktop and mobile devices

## Usage

### Quick Start

1. Make sure your FuseTester HTTP server is running:
   ```bash
   cd server
   npm start
   ```

2. Open the client in your browser:
   ```bash
   cd client
   open index.html
   ```
   Or simply double-click `index.html` in your file manager.

### Dashboard Controls

#### Server Connection
- **Server URL**: Default is `http://localhost:3000` - change if server runs elsewhere
- **Check Server**: Test connection to verify server is online

#### Date Filtering
- **Start Date**: Beginning of time range to query
- **End Date**: End of time range to query
- **Quick Filters**: 
  - Last Hour
  - Last 6 Hours  
  - Last 24 Hours
  - Last 7 Days

#### Fuse Selection
- **Individual Checkboxes**: Select specific fuses (3-64) to display
- **Select All**: Check all available fuses
- **Select None**: Uncheck all fuses
- **Common (3-20)**: Select first 18 fuses for typical monitoring

#### Data Loading
- **Load Data**: Query server with current filters and update chart
- **Device ID**: Optional filter for specific FuseTester device

### Chart Features

- **Interactive Legend**: Click fuse names to show/hide lines
- **Zoom and Pan**: Mouse wheel to zoom, drag to pan
- **Hover Values**: Mouse over data points to see exact values
- **Time-based X-axis**: Automatic time formatting
- **Voltage Y-axis**: Scaled appropriately for fuse voltages

### Statistics Panel

- **Total Readings**: Number of data points from server
- **Data Points**: Total fuse measurements across all readings
- **Avg Battery**: Average battery voltage across time range
- **Time Range**: Duration of data in minutes

## Server Integration

The client is designed to work with the FuseTester HTTP server API:

- `GET /health` - Server status check
- `GET /data?start={ISO_DATE}&end={ISO_DATE}&device_id={ID}` - Data query

### Expected Data Format

The client expects the server to return data in this format:

```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "id": 123,
      "timestamp": "2025-08-10T12:00:00.000Z",
      "device_id": "fusetester-001",
      "battery_voltage": 12.8,
      "fuse_readings": {
        "3": 12.45,
        "4": 11.92,
        "5": 12.01
      }
    }
  ]
}
```

## Browser Compatibility

- **Modern Browsers**: Chrome 60+, Firefox 55+, Safari 12+, Edge 79+
- **JavaScript Requirements**: ES6+ features (async/await, fetch)
- **External Dependencies**:
  - Chart.js 3.x (loaded from CDN)
  - Date-fns 2.x (loaded from CDN)

## Customization

### Adding New Chart Types

The dashboard uses Chart.js. You can modify the chart configuration in the `updateChart()` function to:

- Change chart type (bar, scatter, etc.)
- Adjust colors and styling
- Add additional scales or plugins
- Modify interaction behavior

### Styling

The CSS is embedded in the HTML file. Key customization areas:

- **Color Scheme**: Modify CSS variables for primary colors
- **Layout**: Adjust grid layouts in `.controls` and `.stats-container`
- **Chart Size**: Modify canvas dimensions and container padding
- **Responsive Breakpoints**: Adjust `minmax()` values in grid layouts

### Additional Features

Easy to extend with:

- Export to CSV/PDF functionality
- Real-time updates with WebSockets
- Alert thresholds for voltage ranges
- Historical comparison views
- Device management interface

## Troubleshooting

### Common Issues

1. **Server Connection Failed**
   - Check server is running on correct port
   - Verify server URL in dashboard
   - Check browser console for CORS errors

2. **No Data Displayed**
   - Ensure date range contains data
   - Check at least one fuse is selected
   - Verify server has data in database

3. **Chart Not Loading**
   - Check browser console for JavaScript errors
   - Ensure internet connection for CDN resources
   - Try refreshing the page

### CORS Issues

If accessing server from different domain/port, ensure server has CORS enabled:

```javascript
app.use(cors({
  origin: ['http://localhost:3000', 'file://']
}));
```

### Performance

For large datasets:
- Limit time ranges to reasonable periods
- Select fewer fuses for better performance
- Consider implementing server-side pagination
- Use chart decimation for large point counts

## File Structure

```
client/
├── index.html          # Complete single-page application
└── README.md           # This documentation
```

The entire client is contained in a single HTML file for simplicity and portability.
