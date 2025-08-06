const path = require("path");
const fs = require("fs");
const winston = require("winston");
const I2CService = require("./services/i2c.service");
const FuseMonitorService = require("./services/fuse-monitor.service");
require("dotenv").config();

// Configure logging
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: "fusetester" },
  transports: [
    new winston.transports.File({ filename: "logs/error.log", level: "error" }),
    new winston.transports.File({ filename: "logs/combined.log" }),
    new winston.transports.Console({
      format: winston.format.simple(),
    }),
  ],
});

// Memory monitoring for Pi 1 B+
function logMemoryUsage() {
  const used = process.memoryUsage();
  logger.info("Memory Usage:", {
    rss: `${Math.round((used.rss / 1024 / 1024) * 100) / 100} MB`,
    heapTotal: `${Math.round((used.heapTotal / 1024 / 1024) * 100) / 100} MB`,
    heapUsed: `${Math.round((used.heapUsed / 1024 / 1024) * 100) / 100} MB`,
    external: `${Math.round((used.external / 1024 / 1024) * 100) / 100} MB`,
  });
}

// Initialize services
async function initialize() {
  logger.info("Initializing FuseTester Fuse Monitoring System...");
  logger.info(`Platform: ${process.platform}, Architecture: ${process.arch}`);

  // Create data directory if it doesn't exist
  const dataDir = path.dirname(
    process.env.CSV_FILE_PATH || "./data/fuse_data.csv"
  );
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
    logger.info(`Created data directory: ${dataDir}`);
  }

  // Initialize I2C service if enabled
  if (process.env.I2C_ENABLED === "true") {
    try {
      I2CService.initialize();
      logger.info("I2C service initialized");
    } catch (error) {
      logger.error("Failed to initialize I2C service:", error);
      process.exit(1);
    }
  } else {
    logger.error("I2C is disabled - cannot run fuse monitoring without I2C");
    process.exit(1);
  }

  // Initialize Fuse Monitor Service
  try {
    await FuseMonitorService.initialize();
    logger.info("Fuse Monitor Service initialized");
  } catch (error) {
    logger.error("Failed to initialize Fuse Monitor Service:", error);
    process.exit(1);
  }

  logger.info("FuseTester initialization complete");
}

// Start fuse monitoring
async function startMonitoring() {
  logger.info("Starting fuse monitoring system...");

  try {
    // Run system test first
    logger.info("Running system test...");
    const testResults = await FuseMonitorService.testSystem();
    logger.info("System test results:", testResults);

    // Start monitoring if test passed
    if (testResults.adc && !testResults.error) {
      FuseMonitorService.startMonitoring();
      logger.info("Fuse monitoring started successfully");

      // Log system status
      const status = FuseMonitorService.getStatus();
      logger.info("System status:", status);
    } else {
      logger.error("System test failed - cannot start monitoring");
      logger.error("Test results:", testResults);
      process.exit(1);
    }
  } catch (error) {
    logger.error("Failed to start monitoring:", error);
    process.exit(1);
  }

  // Log memory usage every 5 minutes if enabled
  if (process.env.MEMORY_MONITORING === "true") {
    setInterval(logMemoryUsage, 300000);
  }

  // Log status every 10 minutes
  setInterval(() => {
    const status = FuseMonitorService.getStatus();
    logger.info("System status update:", {
      monitoring: status.monitoring,
      currentMux: status.currentMux,
      currentChannel: status.currentChannel,
      csvFile: status.csv ? status.csv.sizeMB + "MB" : "unknown",
    });
  }, 600000);
}

// Graceful shutdown
function shutdown() {
  logger.info("Shutting down gracefully...");

  // Stop monitoring
  if (FuseMonitorService.isInitialized()) {
    FuseMonitorService.shutdown();
  }

  // Shutdown I2C
  if (I2CService.isInitialized()) {
    I2CService.shutdown();
  }

  logger.info("Shutdown complete");
  process.exit(0);
}

// Signal handlers
process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);

// Uncaught exception handler
process.on("uncaughtException", (error) => {
  logger.error("Uncaught exception:", error);
  shutdown();
});

// Unhandled rejection handler
process.on("unhandledRejection", (reason, promise) => {
  logger.error("Unhandled rejection at:", promise, "reason:", reason);
  shutdown();
});

// Start application
async function start() {
  try {
    await initialize();
    await startMonitoring();
    logger.info("FuseTester Fuse Monitoring System running successfully");
  } catch (error) {
    logger.error("Failed to start application:", error);
    process.exit(1);
  }
}

// Run application
start();
