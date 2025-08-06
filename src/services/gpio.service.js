/**
 * GPIO Service for Multiplexer Control
 * Handles GPIO operations for CD74HC4067M multiplexers
 */

let pigpio;
try {
  pigpio = require("pigpio");
} catch (error) {
  console.warn("pigpio not available - GPIO functionality disabled");
  pigpio = null;
}

// GPIO Pin definitions
const MUX_CONTROL_PINS = {
  S0: 27, // Pi Pin 13 (GPIO27)
  S1: 17, // Pi Pin 11 (GPIO17)
  S2: 24, // Pi Pin 18 (GPIO24)
  S3: 23, // Pi Pin 16 (GPIO23)
};

const MUX_ENABLE_PINS = {
  MUX0: 7, // Pi Pin 26 (GPIO7)
  MUX1: 8, // Pi Pin 24 (GPIO8)
  MUX2: 6, // Pi Pin 31 (GPIO6)
  MUX3: 13, // Pi Pin 33 (GPIO13)
};

class GPIOService {
  constructor() {
    this.initialized = false;
    this.gpioPins = {};
  }

  /**
   * Initialize GPIO pins
   */
  initialize() {
    if (!pigpio) {
      throw new Error("pigpio library not available");
    }

    if (!this.initialized) {
      try {
        pigpio.initialize();

        // Initialize control pins (S0, S1, S2, S3) as outputs
        for (const [pinName, pinNumber] of Object.entries(MUX_CONTROL_PINS)) {
          const pin = new pigpio.Gpio(pinNumber, { mode: pigpio.Gpio.OUTPUT });
          this.gpioPins[pinName] = pin;
          pin.digitalWrite(0); // Start with all control pins low
        }

        // Initialize enable pins as outputs (active low, so start high = disabled)
        for (const [muxName, pinNumber] of Object.entries(MUX_ENABLE_PINS)) {
          const pin = new pigpio.Gpio(pinNumber, { mode: pigpio.Gpio.OUTPUT });
          this.gpioPins[muxName] = pin;
          pin.digitalWrite(1); // Start with all muxes disabled (high = disabled)
        }

        this.initialized = true;
        console.log("GPIO service initialized successfully");
        console.log("Control pins:", MUX_CONTROL_PINS);
        console.log("Enable pins:", MUX_ENABLE_PINS);
      } catch (error) {
        console.error("Failed to initialize GPIO:", error);
        throw error;
      }
    }
  }

  /**
   * Set multiplexer channel (0-15)
   * @param {number} channel - Channel number (0-15)
   */
  setMuxChannel(channel) {
    if (!this.initialized) {
      throw new Error("GPIO service not initialized");
    }

    if (channel < 0 || channel > 15) {
      throw new Error("Channel must be 0-15");
    }

    // Convert channel to binary and set S0, S1, S2, S3 pins
    this.gpioPins.S0.digitalWrite(channel & 0x01);
    this.gpioPins.S1.digitalWrite((channel & 0x02) >> 1);
    this.gpioPins.S2.digitalWrite((channel & 0x04) >> 2);
    this.gpioPins.S3.digitalWrite((channel & 0x08) >> 3);
  }

  /**
   * Enable a specific multiplexer (disable others)
   * @param {number} muxIndex - Multiplexer index (0-3)
   */
  enableMux(muxIndex) {
    if (!this.initialized) {
      throw new Error("GPIO service not initialized");
    }

    if (muxIndex < 0 || muxIndex > 3) {
      throw new Error("Mux index must be 0-3");
    }

    // Disable all muxes first (set enable pins high)
    this.gpioPins.MUX0.digitalWrite(1);
    this.gpioPins.MUX1.digitalWrite(1);
    this.gpioPins.MUX2.digitalWrite(1);
    this.gpioPins.MUX3.digitalWrite(1);

    // Enable the selected mux (set enable pin low)
    const muxName = `MUX${muxIndex}`;
    this.gpioPins[muxName].digitalWrite(0);
  }

  /**
   * Disable all multiplexers
   */
  disableAllMux() {
    if (!this.initialized) {
      throw new Error("GPIO service not initialized");
    }

    // Set all enable pins high (disabled)
    this.gpioPins.MUX0.digitalWrite(1);
    this.gpioPins.MUX1.digitalWrite(1);
    this.gpioPins.MUX2.digitalWrite(1);
    this.gpioPins.MUX3.digitalWrite(1);
  }

  /**
   * Utility delay function
   * @param {number} ms - Milliseconds to delay
   * @returns {Promise}
   */
  async delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Get current pin states for debugging
   * @returns {Object} Current pin states
   */
  getPinStates() {
    if (!this.initialized) {
      return { error: "GPIO service not initialized" };
    }

    const states = {};

    // Read control pins
    for (const [pinName, _] of Object.entries(MUX_CONTROL_PINS)) {
      states[pinName] = this.gpioPins[pinName].digitalRead();
    }

    // Read enable pins
    for (const [muxName, _] of Object.entries(MUX_ENABLE_PINS)) {
      states[muxName] = this.gpioPins[muxName].digitalRead();
    }

    return states;
  }

  /**
   * Get currently selected channel
   * @returns {number} Current channel (0-15)
   */
  getCurrentChannel() {
    if (!this.initialized) {
      return -1;
    }

    const s0 = this.gpioPins.S0.digitalRead();
    const s1 = this.gpioPins.S1.digitalRead();
    const s2 = this.gpioPins.S2.digitalRead();
    const s3 = this.gpioPins.S3.digitalRead();

    return s0 | (s1 << 1) | (s2 << 2) | (s3 << 3);
  }

  /**
   * Get currently enabled mux
   * @returns {number} Enabled mux index (0-3) or -1 if none enabled
   */
  getEnabledMux() {
    if (!this.initialized) {
      return -1;
    }

    for (let i = 0; i < 4; i++) {
      const muxName = `MUX${i}`;
      if (this.gpioPins[muxName].digitalRead() === 0) {
        return i;
      }
    }

    return -1; // No mux enabled
  }

  /**
   * Test all GPIO pins
   * @returns {Promise<Object>} Test results
   */
  async testPins() {
    if (!this.initialized) {
      throw new Error("GPIO service not initialized");
    }

    const results = {
      controlPins: {},
      enablePins: {},
    };

    try {
      // Test control pins
      for (const [pinName, _] of Object.entries(MUX_CONTROL_PINS)) {
        this.gpioPins[pinName].digitalWrite(1);
        await this.delay(1);
        const high = this.gpioPins[pinName].digitalRead();

        this.gpioPins[pinName].digitalWrite(0);
        await this.delay(1);
        const low = this.gpioPins[pinName].digitalRead();

        results.controlPins[pinName] = {
          high,
          low,
          working: high === 1 && low === 0,
        };
      }

      // Test enable pins
      for (const [muxName, _] of Object.entries(MUX_ENABLE_PINS)) {
        this.gpioPins[muxName].digitalWrite(1);
        await this.delay(1);
        const high = this.gpioPins[muxName].digitalRead();

        this.gpioPins[muxName].digitalWrite(0);
        await this.delay(1);
        const low = this.gpioPins[muxName].digitalRead();

        // Reset to disabled state
        this.gpioPins[muxName].digitalWrite(1);

        results.enablePins[muxName] = {
          high,
          low,
          working: high === 1 && low === 0,
        };
      }
    } catch (error) {
      console.error("Error testing GPIO pins:", error);
      results.error = error.message;
    }

    return results;
  }

  /**
   * Check if GPIO service is initialized
   * @returns {boolean}
   */
  isInitialized() {
    return this.initialized;
  }

  /**
   * Get GPIO configuration info
   * @returns {Object}
   */
  getInfo() {
    return {
      initialized: this.initialized,
      controlPins: MUX_CONTROL_PINS,
      enablePins: MUX_ENABLE_PINS,
      totalMuxes: 4,
      channelsPerMux: 16,
    };
  }

  /**
   * Shutdown GPIO service
   */
  shutdown() {
    if (this.initialized && pigpio) {
      try {
        // Disable all muxes
        this.disableAllMux();

        // Clean up GPIO pins
        for (const pin of Object.values(this.gpioPins)) {
          // pigpio pins are cleaned up automatically on termination
        }

        this.gpioPins = {};
        this.initialized = false;
        console.log("GPIO service shutdown complete");
      } catch (error) {
        console.error("Error during GPIO shutdown:", error);
      }
    }
  }
}

// Export singleton instance
module.exports = new GPIOService();
