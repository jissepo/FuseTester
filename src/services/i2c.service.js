/**
 * I2C Service
 * Handles I2C communication using pigpio library
 * Optimized for Raspberry Pi 1 Model B+ ARM6 architecture
 */

let pigpio;
try {
  pigpio = require("pigpio");
} catch {
  console.warn("pigpio not available - I2C functionality disabled");
  pigpio = null;
}

class I2CService {
  constructor() {
    this.initialized = false;
    this.connectedDevices = new Map();
  }

  /**
   * Initialize I2C service
   */
  initialize() {
    if (!pigpio) {
      throw new Error("pigpio library not available");
    }

    try {
      console.log("Initializing I2C service...");

      // pigpio initialization is handled automatically when creating Gpio instances
      this.initialized = true;
      console.log("I2C service initialized successfully");
    } catch (error) {
      console.error("Failed to initialize I2C service:", error);
      throw error;
    }
  }

  /**
   * Connect to an I2C device
   * @param {number} address - I2C device address (7-bit)
   * @param {number} bus - I2C bus number (default: 1)
   */
  async connectDevice(address, bus = 1) {
    if (!this.initialized) {
      throw new Error("I2C service not initialized");
    }

    try {
      const deviceKey = `${bus}:${address}`;

      if (this.connectedDevices.has(deviceKey)) {
        return this.connectedDevices.get(deviceKey);
      }

      // Create pigpio I2C instance
      const i2c = pigpio.i2c(bus, address);
      this.connectedDevices.set(deviceKey, i2c);

      console.log(
        `Connected to I2C device at address 0x${address.toString(
          16
        )} on bus ${bus}`
      );
      return i2c;
    } catch (error) {
      console.error(
        `Failed to connect to I2C device 0x${address.toString(16)}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Write word (16-bit) data to a register
   * @param {number} address - I2C device address
   * @param {number} register - Register address
   * @param {number} data - 16-bit data to write
   * @param {number} bus - I2C bus number (default: 1)
   */
  async writeWordData(address, register, data, bus = 1) {
    const i2c = await this.connectDevice(address, bus);

    try {
      // Convert to big-endian format for I2C
      const highByte = (data >> 8) & 0xff;
      const lowByte = data & 0xff;
      const buffer = Buffer.from([register, highByte, lowByte]);

      await new Promise((resolve, reject) => {
        i2c.write(buffer, (error) => {
          if (error) {
            reject(error);
          } else {
            resolve();
          }
        });
      });
    } catch (error) {
      console.error(
        `Failed to write word data to 0x${address.toString(
          16
        )} register 0x${register.toString(16)}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Read word (16-bit) data from a register
   * @param {number} address - I2C device address
   * @param {number} register - Register address
   * @param {number} bus - I2C bus number (default: 1)
   */
  async readWordData(address, register, bus = 1) {
    const i2c = await this.connectDevice(address, bus);

    try {
      // First write the register address
      const regBuffer = Buffer.from([register]);
      await new Promise((resolve, reject) => {
        i2c.write(regBuffer, (error) => {
          if (error) {
            reject(error);
          } else {
            resolve();
          }
        });
      });

      // Then read 2 bytes
      const result = await new Promise((resolve, reject) => {
        i2c.read(2, (error, data) => {
          if (error) {
            reject(error);
          } else {
            resolve(data);
          }
        });
      });

      // Convert from big-endian format
      const value = (result[0] << 8) | result[1];
      return value;
    } catch (error) {
      console.error(
        `Failed to read word data from 0x${address.toString(
          16
        )} register 0x${register.toString(16)}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Write a single byte to a register
   * @param {number} address - I2C device address
   * @param {number} register - Register address
   * @param {number} data - Byte data to write
   * @param {number} bus - I2C bus number (default: 1)
   */
  async writeByteData(address, register, data, bus = 1) {
    const i2c = await this.connectDevice(address, bus);

    try {
      const buffer = Buffer.from([register, data]);
      await new Promise((resolve, reject) => {
        i2c.write(buffer, (error) => {
          if (error) {
            reject(error);
          } else {
            resolve();
          }
        });
      });
    } catch (error) {
      console.error(
        `Failed to write byte data to 0x${address.toString(
          16
        )} register 0x${register.toString(16)}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Read a single byte from a register
   * @param {number} address - I2C device address
   * @param {number} register - Register address
   * @param {number} bus - I2C bus number (default: 1)
   */
  async readByteData(address, register, bus = 1) {
    const i2c = await this.connectDevice(address, bus);

    try {
      // Write register address
      const regBuffer = Buffer.from([register]);
      await new Promise((resolve, reject) => {
        i2c.write(regBuffer, (error) => {
          if (error) {
            reject(error);
          } else {
            resolve();
          }
        });
      });

      // Read 1 byte
      const result = await new Promise((resolve, reject) => {
        i2c.read(1, (error, data) => {
          if (error) {
            reject(error);
          } else {
            resolve(data);
          }
        });
      });

      return result[0];
    } catch (error) {
      console.error(
        `Failed to read byte data from 0x${address.toString(
          16
        )} register 0x${register.toString(16)}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Get list of connected device addresses
   */
  getConnectedDevices() {
    return Array.from(this.connectedDevices.keys());
  }

  /**
   * Check if service is initialized
   */
  isInitialized() {
    return this.initialized;
  }

  /**
   * Get service information
   */
  getInfo() {
    return {
      initialized: this.initialized,
      connectedDevices: this.getConnectedDevices(),
      totalConnections: this.connectedDevices.size,
    };
  }

  /**
   * Shutdown I2C service
   */
  shutdown() {
    console.log("Shutting down I2C service...");

    // Close all I2C connections
    for (const [deviceKey, i2c] of this.connectedDevices) {
      try {
        i2c.close();
        console.log(`Closed I2C connection: ${deviceKey}`);
      } catch (error) {
        console.error(`Error closing I2C connection ${deviceKey}:`, error);
      }
    }

    this.connectedDevices.clear();
    this.initialized = false;
    console.log("I2C service shutdown complete");
  }
}

// Export singleton instance
module.exports = new I2CService();
