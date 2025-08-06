/**
 * Fuse Monitor Service
 * Coordinates GPIO, I2C, and CSV logging for fuse monitoring system
 */

const ADS1115Service = require("./ads1115.service");
const GPIOService = require("./gpio.service");
const CSVLogger = require("./csv.logger");

class FuseMonitorService {
	constructor() {
		this.initialized = false;
		this.monitoring = false;
		this.monitorInterval = null;
		this.totalFuses = 64; // 4 muxes × 16 channels each
		this.totalMuxes = 4;
		this.channelsPerMux = 16;
	}

	/**
	 * Initialize all services
	 */
	async initialize() {
		console.log("Initializing Fuse Monitor Service...");

		try {
			// Initialize GPIO service
			GPIOService.initialize();
			console.log("GPIO service ready");

			// Initialize ADS1115 ADC
			await ADS1115Service.initialize();
			console.log("ADS1115 ADC ready");

			// Initialize CSV logger with proper headers
			const csvFilePath = process.env.CSV_FILE_PATH || "./data/fuse_data.csv";
			CSVLogger.initialize(csvFilePath);

			// Create CSV header if file is new
			await this.ensureCSVHeader();
			console.log("CSV logger ready");

			this.initialized = true;
			console.log("Fuse Monitor Service initialized successfully");
		} catch (error) {
			console.error("Failed to initialize Fuse Monitor Service:", error);
			throw error;
		}
	}

	/**
	 * Ensure CSV file has proper headers
	 */
	async ensureCSVHeader() {
		const headers = ["timestamp"];

		// Add headers for all 64 fuses
		for (let i = 1; i <= this.totalFuses; i++) {
			headers.push(`fuse ${i}`);
		}

		// Actually write the headers to the CSV file
		CSVLogger.writeHeaders(headers);
		console.log(`CSV headers written for ${this.totalFuses} fuses`);
	}

	/**
	 * Start monitoring loop
	 */
	startMonitoring() {
		if (!this.initialized) {
			throw new Error("Fuse Monitor Service not initialized");
		}

		if (this.monitoring) {
			console.log("Monitoring already started");
			return;
		}

		const interval = parseInt(process.env.DATA_COLLECTION_INTERVAL) || 5000;
		console.log(`Starting fuse monitoring every ${interval}ms`);

		this.monitoring = true;
		this.monitorInterval = setInterval(async () => {
			await this.collectAndLogData();
		}, interval);

		console.log("Fuse monitoring started");
	}

	/**
	 * Stop monitoring loop
	 */
	stopMonitoring() {
		if (this.monitorInterval) {
			clearInterval(this.monitorInterval);
			this.monitorInterval = null;
		}
		this.monitoring = false;
		console.log("Fuse monitoring stopped");
	}

	/**
	 * Collect data from all fuses and log to CSV
	 */
	async collectAndLogData() {
		const startTime = Date.now();
		const timestamp = new Date().toISOString().split(".")[0] + "Z"; // ISO format to seconds
		const fuseData = [];

		try {
			console.log("Starting data collection cycle...");

			// Collect data from all 4 multiplexers
			for (let muxIndex = 0; muxIndex < this.totalMuxes; muxIndex++) {
				console.log(`Reading mux ${muxIndex}...`);

				// Enable the current mux
				GPIOService.enableMux(muxIndex);
				await this.delay(1); // Wait 1ms after mux change

				// Read all 16 channels on this mux
				for (let channel = 0; channel < this.channelsPerMux; channel++) {
					try {
						// Set the channel on the mux
						GPIOService.setMuxChannel(channel);
						await this.delay(1); // Wait 1ms after channel change

						// Read voltage from the ADC channel corresponding to this mux
						const voltage = await ADS1115Service.readChannel(muxIndex);
						fuseData.push(voltage); // Format as "3.3"

						// Optional: Log detailed info for debugging
						const fuseNumber = muxIndex * this.channelsPerMux + channel + 1;
						console.log(
							`Fuse ${fuseNumber} (Mux ${muxIndex}, Ch ${channel}): ${voltage}V`,
						);
					} catch (error) {
						console.error(
							`Error reading mux ${muxIndex} channel ${channel}:`,
							error,
						);
						fuseData.push("0.0"); // Default value on error
					}
				}
			}

			// Disable all muxes after collection
			GPIOService.disableAllMux();

			// Log data to CSV
			const csvData = {
				timestamp: timestamp,
				values: fuseData,
			};

			await this.logToCSV(csvData);

			// Clean up variables to reduce memory usage
			fuseData.length = 0;

			const duration = Date.now() - startTime;
			console.log(`Data collection cycle completed in ${duration}ms`);
		} catch (error) {
			console.error("Error in data collection cycle:", error);

			// Ensure muxes are disabled even on error
			try {
				GPIOService.disableAllMux();
			} catch (gpioError) {
				console.error(
					"Error disabling muxes after collection error:",
					gpioError,
				);
			}
		}
	}

	/**
	 * Log data to CSV file
	 * @param {Object} csvData - Data object with timestamp and values
	 */
	async logToCSV(csvData) {
		try {
			// Create CSV row
			const row = [csvData.timestamp, ...csvData.values].join(",") + "\n";

			// Write to CSV using the logger's writeStream directly for efficiency
			const writeStream = CSVLogger.writeStream;
			if (writeStream) {
				await new Promise((resolve, reject) => {
					writeStream.write(row, (error) => {
						if (error) {
							reject(error);
						} else {
							resolve();
						}
					});
				});
			}

			console.log("Data logged to CSV successfully");
		} catch (error) {
			console.error("Error writing to CSV:", error);
		}
	}

	/**
	 * Test system functionality
	 */
	async testSystem() {
		if (!this.initialized) {
			throw new Error("Fuse Monitor Service not initialized");
		}

		console.log("Testing system functionality...");

		const results = {
			gpio: null,
			adc: null,
			testReadings: [],
		};

		try {
			// Test GPIO
			console.log("Testing GPIO pins...");
			results.gpio = await GPIOService.testPins();

			// Test ADC
			console.log("Testing ADC health...");
			results.adc = await ADS1115Service.isHealthy();

			// Test reading from first few channels
			console.log("Testing sample readings...");
			for (let mux = 0; mux < 2; mux++) {
				// Test first 2 muxes
				GPIOService.enableMux(mux);
				await this.delay(1);

				for (let channel = 0; channel < 4; channel++) {
					// Test first 4 channels
					GPIOService.setMuxChannel(channel);
					await this.delay(1);

					try {
						const voltage = await ADS1115Service.readChannel(mux);
						results.testReadings.push({
							mux: mux,
							channel: channel,
							voltage: voltage,
						});
					} catch (error) {
						results.testReadings.push({
							mux: mux,
							channel: channel,
							error: error.message,
						});
					}
				}
			}

			// Disable all muxes after test
			GPIOService.disableAllMux();

			console.log("System test completed");
			return results;
		} catch (error) {
			console.error("Error during system test:", error);
			results.error = error.message;
			return results;
		}
	}

	/**
	 * Get current system status
	 */
	getStatus() {
		return {
			initialized: this.initialized,
			monitoring: this.monitoring,
			totalFuses: this.totalFuses,
			gpio: GPIOService.getInfo(),
			adc: ADS1115Service.getInfo(),
			csv: CSVLogger.getFileStats(),
			currentMux: GPIOService.getEnabledMux(),
			currentChannel: GPIOService.getCurrentChannel(),
		};
	}

	/**
	 * Utility delay function
	 * @param {number} ms - Milliseconds to delay
	 */
	async delay(ms) {
		return new Promise((resolve) => setTimeout(resolve, ms));
	}

	/**
	 * Shutdown the service
	 */
	shutdown() {
		console.log("Shutting down Fuse Monitor Service...");

		// Stop monitoring
		this.stopMonitoring();

		// Shutdown GPIO
		GPIOService.shutdown();

		// Close CSV logger
		CSVLogger.close();

		this.initialized = false;
		console.log("Fuse Monitor Service shutdown complete");
	}

	/**
	 * Check if service is initialized
	 */
	isInitialized() {
		return this.initialized;
	}

	/**
	 * Check if monitoring is active
	 */
	isMonitoring() {
		return this.monitoring;
	}
}

// Export singleton instance
module.exports = new FuseMonitorService();
