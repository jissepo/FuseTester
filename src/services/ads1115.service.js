/**
 * ADS1115 ADC Service
 * Handles communication with the ADS1115 16-bit ADC
 */

const I2CService = require("./i2c.service");

// ADS1115 I2C address (default)
const ADS1115_ADDRESS = 0x48;

// ADS1115 Registers
const ADS1115_POINTER_CONVERSION = 0x00;
const ADS1115_POINTER_CONFIG = 0x01;

// Config register bits
const ADS1115_CONFIG_OS_SINGLE = 0x8000; // Start single conversion
const ADS1115_CONFIG_MUX_DIFF_0_1 = 0x0000; // Differential P = AIN0, N = AIN1
const ADS1115_CONFIG_MUX_DIFF_0_3 = 0x1000; // Differential P = AIN0, N = AIN3
const ADS1115_CONFIG_MUX_DIFF_1_3 = 0x2000; // Differential P = AIN1, N = AIN3
const ADS1115_CONFIG_MUX_DIFF_2_3 = 0x3000; // Differential P = AIN2, N = AIN3
const ADS1115_CONFIG_MUX_SINGLE_0 = 0x4000; // Single-ended AIN0
const ADS1115_CONFIG_MUX_SINGLE_1 = 0x5000; // Single-ended AIN1
const ADS1115_CONFIG_MUX_SINGLE_2 = 0x6000; // Single-ended AIN2
const ADS1115_CONFIG_MUX_SINGLE_3 = 0x7000; // Single-ended AIN3

const ADS1115_CONFIG_PGA_6_144V = 0x0000; // +/-6.144V range = Gain 2/3
const ADS1115_CONFIG_PGA_4_096V = 0x0200; // +/-4.096V range = Gain 1
const ADS1115_CONFIG_PGA_2_048V = 0x0400; // +/-2.048V range = Gain 2
const ADS1115_CONFIG_PGA_1_024V = 0x0600; // +/-1.024V range = Gain 4
const ADS1115_CONFIG_PGA_0_512V = 0x0800; // +/-0.512V range = Gain 8
const ADS1115_CONFIG_PGA_0_256V = 0x0a00; // +/-0.256V range = Gain 16

const ADS1115_CONFIG_MODE_SINGLE = 0x0100; // Single-shot mode
const ADS1115_CONFIG_DR_128SPS = 0x0000; // 128 samples per second
const ADS1115_CONFIG_DR_250SPS = 0x0020; // 250 samples per second
const ADS1115_CONFIG_DR_490SPS = 0x0040; // 490 samples per second
const ADS1115_CONFIG_DR_920SPS = 0x0060; // 920 samples per second
const ADS1115_CONFIG_DR_1600SPS = 0x0080; // 1600 samples per second

const ADS1115_CONFIG_CMODE_TRAD = 0x0000; // Traditional comparator
const ADS1115_CONFIG_CPOL_ACTVLOW = 0x0000; // Alert/Rdy active low
const ADS1115_CONFIG_CLAT_NONLAT = 0x0000; // Non-latching comparator
const ADS1115_CONFIG_CQUE_NONE = 0x0003; // Disable the comparator

class ADS1115Service {
  constructor() {
    this.address = ADS1115_ADDRESS;
    this.gain = ADS1115_CONFIG_PGA_4_096V; // Default to +/-4.096V range
    this.isConnected = false;
    this.conversionDelay = 8; // ms - time to wait for conversion (125 SPS = 8ms)
  }

  /**
   * Initialize connection to ADS1115
   */
  async initialize() {
    try {
      await I2CService.connectDevice(this.address);
      this.isConnected = true;
      console.log("ADS1115 ADC initialized successfully");
    } catch (error) {
      console.error("Failed to initialize ADS1115:", error);
      throw error;
    }
  }

  /**
   * Set the gain/voltage range for readings
   * @param {number} gain - Gain configuration (use ADS1115_CONFIG_PGA_* constants)
   */
  setGain(gain) {
    this.gain = gain;
  }

  /**
   * Get voltage range based on current gain setting
   * @returns {number} Maximum voltage for current range
   */
  getVoltageRange() {
    switch (this.gain) {
      case ADS1115_CONFIG_PGA_6_144V:
        return 6.144;
      case ADS1115_CONFIG_PGA_4_096V:
        return 4.096;
      case ADS1115_CONFIG_PGA_2_048V:
        return 2.048;
      case ADS1115_CONFIG_PGA_1_024V:
        return 1.024;
      case ADS1115_CONFIG_PGA_0_512V:
        return 0.512;
      case ADS1115_CONFIG_PGA_0_256V:
        return 0.256;
      default:
        return 4.096;
    }
  }

  /**
   * Read voltage from a specific channel (0-3)
   * @param {number} channel - ADC channel (0-3)
   * @returns {Promise<number>} Voltage reading
   */
  async readChannel(channel) {
    if (!this.isConnected) {
      throw new Error("ADS1115 not initialized");
    }

    if (channel < 0 || channel > 3) {
      throw new Error("Channel must be 0-3");
    }

    // Select the appropriate mux configuration for single-ended reading
    let muxConfig;
    switch (channel) {
      case 0:
        muxConfig = ADS1115_CONFIG_MUX_SINGLE_0;
        break;
      case 1:
        muxConfig = ADS1115_CONFIG_MUX_SINGLE_1;
        break;
      case 2:
        muxConfig = ADS1115_CONFIG_MUX_SINGLE_2;
        break;
      case 3:
        muxConfig = ADS1115_CONFIG_MUX_SINGLE_3;
        break;
    }

    // Build configuration
    const config =
      ADS1115_CONFIG_OS_SINGLE | // Start single conversion
      muxConfig | // Select channel
      this.gain | // Set gain
      ADS1115_CONFIG_MODE_SINGLE | // Single-shot mode
      ADS1115_CONFIG_DR_128SPS | // 128 samples per second
      ADS1115_CONFIG_CMODE_TRAD | // Traditional comparator
      ADS1115_CONFIG_CPOL_ACTVLOW | // Alert/Rdy active low
      ADS1115_CONFIG_CLAT_NONLAT | // Non-latching comparator
      ADS1115_CONFIG_CQUE_NONE; // Disable comparator

    // Write config to start conversion
    await I2CService.writeWordData(
      this.address,
      ADS1115_POINTER_CONFIG,
      config
    );

    // Wait for conversion to complete
    await this.delay(this.conversionDelay);

    // Read the conversion result
    const rawValue = await I2CService.readWordData(
      this.address,
      ADS1115_POINTER_CONVERSION
    );

    // Convert to voltage
    const voltage = this.convertRawToVoltage(rawValue);

    return Math.round(voltage * 100) / 100; // Round to 2 decimal places
  }

  /**
   * Convert raw ADC value to voltage
   * @param {number} rawValue - Raw 16-bit ADC value
   * @returns {number} Voltage value
   */
  convertRawToVoltage(rawValue) {
    // ADS1115 returns 16-bit signed value
    let value = rawValue;
    if (value > 32767) {
      value -= 65536;
    }

    // Convert to voltage based on gain setting
    const voltageRange = this.getVoltageRange();
    const voltage = (value / 32767.0) * voltageRange;

    return voltage;
  }

  /**
   * Read all channels sequentially
   * @returns {Promise<Array>} Array of voltage readings [ch0, ch1, ch2, ch3]
   */
  async readAllChannels() {
    const readings = [];

    for (let channel = 0; channel < 4; channel++) {
      try {
        const voltage = await this.readChannel(channel);
        readings.push(voltage);
      } catch (error) {
        console.error(`Error reading channel ${channel}:`, error);
        readings.push(null);
      }
    }

    return readings;
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
   * Check if ADS1115 is connected and responding
   * @returns {Promise<boolean>}
   */
  async isHealthy() {
    if (!this.isConnected) {
      return false;
    }

    try {
      // Try to read the config register
      await I2CService.readWordData(this.address, ADS1115_POINTER_CONFIG);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get current configuration info
   * @returns {Object} Configuration information
   */
  getInfo() {
    return {
      address: `0x${this.address.toString(16)}`,
      connected: this.isConnected,
      voltageRange: `+/-${this.getVoltageRange()}V`,
      conversionDelay: `${this.conversionDelay}ms`,
    };
  }
}

// Export singleton instance
module.exports = new ADS1115Service();
