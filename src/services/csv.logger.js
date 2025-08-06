/**
 * CSV Logger Service
 * Handles CSV file creation, writing, and rotation
 * Optimized for Raspberry Pi 1 Model B+ with memory constraints
 */

const fs = require("fs");
const path = require("path");

class CSVLogger {
  constructor() {
    this.initialized = false;
    this.filePath = null;
    this.writeStream = null;
    this.fileSize = 0;
    this.maxFileSize = null;
    this.rotationCount = 0;
    this.headers = null;
  }

  /**
   * Initialize CSV logger
   * @param {string} filePath - Path to CSV file
   * @param {Object} options - Configuration options
   */
  initialize(filePath, options = {}) {
    try {
      this.filePath = path.resolve(filePath);
      this.maxFileSize =
        options.maxFileSize ||
        parseInt(process.env.CSV_MAX_FILE_SIZE) ||
        50 * 1024 * 1024; // 50MB default

      console.log(`Initializing CSV logger: ${this.filePath}`);
      console.log(
        `Max file size: ${Math.round(this.maxFileSize / 1024 / 1024)}MB`
      );

      // Ensure directory exists
      const dir = path.dirname(this.filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`Created directory: ${dir}`);
      }

      // Check if file exists and get current size
      if (fs.existsSync(this.filePath)) {
        const stats = fs.statSync(this.filePath);
        this.fileSize = stats.size;
        console.log(
          `Existing CSV file size: ${Math.round(this.fileSize / 1024)}KB`
        );
      }

      // Create write stream in append mode
      this.writeStream = fs.createWriteStream(this.filePath, {
        flags: "a",
        encoding: "utf8",
      });

      this.writeStream.on("error", (error) => {
        console.error("CSV write stream error:", error);
      });

      this.initialized = true;
      console.log("CSV logger initialized successfully");
    } catch (error) {
      console.error("Failed to initialize CSV logger:", error);
      throw error;
    }
  }

  /**
   * Write CSV headers if file is new or empty
   * @param {Array} headers - Array of header strings
   */
  writeHeaders(headers) {
    if (!this.initialized) {
      throw new Error("CSV logger not initialized");
    }

    try {
      this.headers = headers;

      // Only write headers if file is new/empty
      if (this.fileSize === 0) {
        const headerLine = headers.join(",") + "\n";
        this.writeStream.write(headerLine);
        this.fileSize += Buffer.byteLength(headerLine, "utf8");
        console.log("CSV headers written:", headers.join(", "));
      }
    } catch (error) {
      console.error("Failed to write CSV headers:", error);
      throw error;
    }
  }

  /**
   * Log data to CSV file
   * @param {Object|Array} data - Data to log (object with key-value pairs or array of values)
   */
  async logData(data) {
    if (!this.initialized) {
      throw new Error("CSV logger not initialized");
    }

    try {
      let csvLine;

      if (Array.isArray(data)) {
        // Data is already an array of values
        csvLine = data.join(",") + "\n";
      } else if (typeof data === "object") {
        // Data is an object - convert to CSV line
        if (data.timestamp && data.values) {
          // Special format for fuse monitoring: {timestamp: "...", values: [...]}
          csvLine = [data.timestamp, ...data.values].join(",") + "\n";
        } else {
          // Regular object - use values in order
          const values = Object.values(data);
          csvLine = values.join(",") + "\n";
        }
      } else {
        throw new Error("Data must be an object or array");
      }

      // Check if file rotation is needed
      const lineSize = Buffer.byteLength(csvLine, "utf8");
      if (this.fileSize + lineSize > this.maxFileSize) {
        await this.rotateFile();
      }

      // Write data
      await new Promise((resolve, reject) => {
        this.writeStream.write(csvLine, "utf8", (error) => {
          if (error) {
            reject(error);
          } else {
            this.fileSize += lineSize;
            resolve();
          }
        });
      });
    } catch (error) {
      console.error("Failed to log data to CSV:", error);
      throw error;
    }
  }

  /**
   * Rotate CSV file when it reaches max size
   */
  async rotateFile() {
    try {
      console.log("Rotating CSV file...");

      // Close current stream
      if (this.writeStream) {
        this.writeStream.end();
      }

      // Generate rotated filename
      this.rotationCount++;
      const ext = path.extname(this.filePath);
      const baseName = path.basename(this.filePath, ext);
      const dir = path.dirname(this.filePath);
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      const rotatedPath = path.join(
        dir,
        `${baseName}_${timestamp}_${this.rotationCount}${ext}`
      );

      // Rename current file
      fs.renameSync(this.filePath, rotatedPath);
      console.log(`Rotated file to: ${rotatedPath}`);

      // Create new file and stream
      this.writeStream = fs.createWriteStream(this.filePath, {
        flags: "w",
        encoding: "utf8",
      });

      this.writeStream.on("error", (error) => {
        console.error("CSV write stream error after rotation:", error);
      });

      this.fileSize = 0;

      // Write headers to new file if we have them
      if (this.headers) {
        const headerLine = this.headers.join(",") + "\n";
        this.writeStream.write(headerLine);
        this.fileSize += Buffer.byteLength(headerLine, "utf8");
      }

      console.log("File rotation completed");
    } catch (error) {
      console.error("Error during file rotation:", error);
      throw error;
    }
  }

  /**
   * Get file statistics
   */
  getFileStats() {
    try {
      if (!this.initialized || !fs.existsSync(this.filePath)) {
        return null;
      }

      const stats = fs.statSync(this.filePath);
      return {
        path: this.filePath,
        size: stats.size,
        sizeMB: Math.round((stats.size / 1024 / 1024) * 100) / 100,
        maxSizeMB: Math.round(this.maxFileSize / 1024 / 1024),
        created: stats.birthtime,
        modified: stats.mtime,
        rotationCount: this.rotationCount,
      };
    } catch (error) {
      console.error("Error getting file stats:", error);
      return null;
    }
  }

  /**
   * Flush any pending writes
   */
  async flush() {
    if (this.writeStream) {
      return new Promise((resolve) => {
        this.writeStream.write("", resolve);
      });
    }
  }

  /**
   * Close CSV logger
   */
  close() {
    try {
      console.log("Closing CSV logger...");

      if (this.writeStream) {
        this.writeStream.end();
        this.writeStream = null;
      }

      this.initialized = false;
      console.log("CSV logger closed");
    } catch (error) {
      console.error("Error closing CSV logger:", error);
    }
  }

  /**
   * Check if logger is initialized
   */
  isInitialized() {
    return this.initialized;
  }

  /**
   * Get current file path
   */
  getCurrentFilePath() {
    return this.filePath;
  }

  /**
   * Get current file size
   */
  getCurrentFileSize() {
    return this.fileSize;
  }
}

// Export singleton instance
module.exports = new CSVLogger();
