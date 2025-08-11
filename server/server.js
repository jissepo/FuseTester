const express = require("express");
const sqlite3 = require("sqlite3").verbose();
const cors = require("cors");
const helmet = require("helmet");
const path = require("path");

const app = express();
const PORT = process.env.PORT || 3000;
const DB_PATH = path.join(__dirname, "fusetester.db");

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: "10mb" }));

// Database initialization
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) {
    console.error("Error opening database:", err.message);
    process.exit(1);
  }
  console.log("Connected to SQLite database");
});

// Create tables if they don't exist
db.serialize(() => {
  // Main readings table
  db.run(`
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            device_id TEXT NOT NULL,
            battery_voltage REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            system_memory_percent REAL,
            system_cpu_temp REAL,
            system_uptime_seconds INTEGER
        )
    `);

  // Individual fuse readings table
  db.run(`
        CREATE TABLE IF NOT EXISTS fuse_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reading_id INTEGER NOT NULL,
            fuse_number INTEGER NOT NULL,
            voltage REAL NOT NULL,
            FOREIGN KEY (reading_id) REFERENCES readings (id)
        )
    `);

  // Create index for performance
  db.run(
    `CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp)`
  );
  db.run(
    `CREATE INDEX IF NOT EXISTS idx_readings_device ON readings(device_id)`
  );
  db.run(
    `CREATE INDEX IF NOT EXISTS idx_fuse_reading_id ON fuse_readings(reading_id)`
  );
});

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({
    status: "OK",
    timestamp: new Date().toISOString(),
    server: "FuseTester HTTP Server",
  });
});

// POST endpoint to receive fuse data
app.post("/data", async (req, res) => {
  try {
    const { timestamp, device_id, readings, battery, system_info } = req.body;

    // Validate required fields
    if (!timestamp || !device_id || !readings) {
      return res.status(400).json({
        error: "Missing required fields: timestamp, device_id, readings",
      });
    }

    // Extract system info
    const memoryPercent = system_info?.memory_percent || null;
    const cpuTemp = system_info?.cpu_temp || null;
    const uptimeSeconds = system_info?.uptime_seconds || null;

    // Insert main reading record
    const insertReading = `
            INSERT INTO readings (
                timestamp, device_id, battery_voltage, 
                system_memory_percent, system_cpu_temp, system_uptime_seconds
            ) VALUES (?, ?, ?, ?, ?, ?)
        `;

    db.run(
      insertReading,
      [timestamp, device_id, battery, memoryPercent, cpuTemp, uptimeSeconds],
      function (err) {
        if (err) {
          console.error("Database error:", err.message);
          return res.status(500).json({ error: "Database error" });
        }

        const readingId = this.lastID;

        // Insert individual fuse readings
        const insertFuse = `INSERT INTO fuse_readings (reading_id, fuse_number, voltage) VALUES (?, ?, ?)`;
        const fuseCount = Object.keys(readings).length;
        let completed = 0;

        if (fuseCount === 0) {
          return res.json({
            success: true,
            reading_id: readingId,
            fuses_recorded: 0,
            message: "Reading saved (no fuse data)",
          });
        }

        Object.entries(readings).forEach(([fuseNum, voltage]) => {
          db.run(insertFuse, [readingId, parseInt(fuseNum), voltage], (err) => {
            if (err) {
              console.error("Fuse insert error:", err.message);
            }

            completed++;
            if (completed === fuseCount) {
              console.log(
                `Saved reading ${readingId}: ${fuseCount} fuses, battery: ${battery}V`
              );
              res.json({
                success: true,
                reading_id: readingId,
                fuses_recorded: fuseCount,
                battery_voltage: battery,
              });
            }
          });
        });
      }
    );
  } catch (error) {
    console.error("Error processing data:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

// GET endpoint to query data with datetime filtering
app.get("/data", (req, res) => {
  try {
    const { start, end, device_id } = req.query;

    // Build query conditions
    let conditions = [];
    let params = [];

    if (start) {
      conditions.push("r.timestamp >= ?");
      params.push(start);
    }

    if (end) {
      conditions.push("r.timestamp <= ?");
      params.push(end);
    }

    if (device_id) {
      conditions.push("r.device_id = ?");
      params.push(device_id);
    }

    const whereClause =
      conditions.length > 0 ? "WHERE " + conditions.join(" AND ") : "";

    // Query with joins to get complete data
    const query = `
            SELECT 
                r.id,
                r.timestamp,
                r.device_id,
                r.battery_voltage,
                r.created_at,
                r.system_memory_percent,
                r.system_cpu_temp,
                r.system_uptime_seconds,
                GROUP_CONCAT(
                    f.fuse_number || ':' || f.voltage
                ) as fuse_data
            FROM readings r
            LEFT JOIN fuse_readings f ON r.id = f.reading_id
            ${whereClause}
            GROUP BY r.id
            ORDER BY r.timestamp DESC
            LIMIT 1000
        `;

    db.all(query, params, (err, rows) => {
      if (err) {
        console.error("Query error:", err.message);
        return res.status(500).json({ error: "Database query error" });
      }

      // Process results to structure fuse data properly
      const results = rows.map((row) => {
        const fuseReadings = {};

        if (row.fuse_data) {
          row.fuse_data.split(",").forEach((entry) => {
            const [fuseNum, voltage] = entry.split(":");
            fuseReadings[parseInt(fuseNum)] = parseFloat(voltage);
          });
        }

        return {
          id: row.id,
          timestamp: row.timestamp,
          device_id: row.device_id,
          battery_voltage: row.battery_voltage,
          created_at: row.created_at,
          system_info: {
            memory_percent: row.system_memory_percent,
            cpu_temp: row.system_cpu_temp,
            uptime_seconds: row.system_uptime_seconds,
          },
          fuse_readings: fuseReadings,
        };
      });

      res.json({
        success: true,
        count: results.length,
        data: results,
        query_params: { start, end, device_id },
      });
    });
  } catch (error) {
    console.error("Error querying data:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

// GET endpoint for statistics
app.get("/stats", (req, res) => {
  const statsQuery = `
        SELECT 
            COUNT(*) as total_readings,
            COUNT(DISTINCT device_id) as unique_devices,
            MIN(timestamp) as earliest_reading,
            MAX(timestamp) as latest_reading,
            AVG(battery_voltage) as avg_battery_voltage,
            COUNT(CASE WHEN battery_voltage < 2.5 THEN 1 END) as low_battery_count
        FROM readings
    `;

  db.get(statsQuery, (err, stats) => {
    if (err) {
      console.error("Stats query error:", err.message);
      return res.status(500).json({ error: "Stats query error" });
    }

    res.json({
      success: true,
      statistics: stats,
    });
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ error: "Internal server error" });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: "Endpoint not found" });
});

// Graceful shutdown
process.on("SIGINT", () => {
  console.log("\nReceived SIGINT, shutting down gracefully...");
  db.close((err) => {
    if (err) {
      console.error("Error closing database:", err.message);
    } else {
      console.log("Database connection closed.");
    }
    process.exit(0);
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`FuseTester HTTP Server listening on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`POST data: http://localhost:${PORT}/data`);
  console.log(
    `GET data: http://localhost:${PORT}/data?start=2025-01-01T00:00:00Z&end=2025-12-31T23:59:59Z`
  );
  console.log(`Statistics: http://localhost:${PORT}/stats`);
});

module.exports = app;
