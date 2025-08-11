#!/usr/bin/env python3
"""
Hardware Testing Script for FuseTester
Test specific ADC channels and multiplexer inputs interactively

Usage:
    python3 test_hardware.py
    
This script allows you to:
- Select a specific ADC channel (0-3)  
- Select a specific multiplexer input (0-15)
- Read voltage from that specific combination
- Useful for debugging and hardware validation
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from services.gpio_service import GPIOService
from services.ads1115_service import ADS1115Service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger('hardware_test')

class HardwareTester:
    """Interactive hardware testing utility"""
    
    def __init__(self):
        self.gpio_service = None
        self.ads1115_service = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize GPIO and ADS1115 services"""
        try:
            logger.info("Initializing hardware services...")
            
            # Initialize GPIO service
            self.gpio_service = GPIOService()
            await self.gpio_service.initialize()
            logger.info("✓ GPIO service initialized")
            
            # Initialize ADS1115 service
            self.ads1115_service = ADS1115Service()
            await self.ads1115_service.initialize()
            
            # Set gain for fuse monitoring (0-5V range)
            self.ads1115_service.set_gain('6.144V')
            logger.info("✓ ADS1115 service initialized with 6.144V range")
            
            self.initialized = True
            logger.info("✓ Hardware services ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize hardware: {e}")
            raise
    
    async def test_specific_input(self, adc_channel: int, mux_input: int):
        """
        Test a specific ADC channel and multiplexer input combination
        
        Args:
            adc_channel: ADC channel (0-3)
            mux_input: Multiplexer input (0-15)
        """
        if not self.initialized:
            raise RuntimeError("Hardware not initialized")
        
        try:
            logger.info(f"Testing ADC channel {adc_channel}, MUX input {mux_input}")
            
            # First, disable all multiplexers to ensure clean state
            await self.gpio_service.disable_all_mux()
            logger.debug("✓ All MUXes disabled")
            
            # Calculate which multiplexer this corresponds to
            # ADC0->MUX0, ADC1->MUX1, ADC2->MUX2, ADC3->MUX3
            mux_number = adc_channel
            
            # Set multiplexer channel
            await self.gpio_service.set_mux_channel(mux_input)
            logger.info(f"✓ Set MUX channel to {mux_input}")
            
            # Enable the specific multiplexer
            await self.gpio_service.enable_mux(mux_number)
            logger.info(f"✓ Enabled MUX {mux_number}")
            
            # Small delay for settling
            await asyncio.sleep(0.1)
            
            # Read voltage from ADC channel
            voltage = await self.ads1115_service.read_channel(adc_channel)
            
            # Calculate fuse number (for reference)
            fuse_number = (mux_number * 16) + mux_input + 1
            
            logger.info(f"📊 Results:")
            logger.info(f"   ADC Channel: {adc_channel}")
            logger.info(f"   MUX Number: {mux_number}")
            logger.info(f"   MUX Input: {mux_input}")
            logger.info(f"   Fuse Number: {fuse_number}")
            logger.info(f"   Voltage: {voltage:.4f}V")
            
            return {
                'adc_channel': adc_channel,
                'mux_number': mux_number,
                'mux_input': mux_input,
                'fuse_number': fuse_number,
                'voltage': voltage
            }
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise
    
    async def test_all_adc_channels(self, mux_input: int = 0):
        """
        Test all ADC channels with the same multiplexer input
        
        Args:
            mux_input: Multiplexer input to test (0-15)
        """
        logger.info(f"Testing all ADC channels with MUX input {mux_input}")
        
        results = []
        for adc_channel in range(4):
            try:
                result = await self.test_specific_input(adc_channel, mux_input)
                results.append(result)
                await asyncio.sleep(0.2)  # Small delay between readings
            except Exception as e:
                logger.error(f"Failed to test ADC {adc_channel}: {e}")
        
        return results
    
    async def test_mux_sweep(self, adc_channel: int = 0):
        """
        Test all multiplexer inputs on a single ADC channel
        
        Args:
            adc_channel: ADC channel to test (0-3)
        """
        logger.info(f"Testing all MUX inputs on ADC channel {adc_channel}")
        
        results = []
        for mux_input in range(16):
            try:
                result = await self.test_specific_input(adc_channel, mux_input)
                results.append(result)
                await asyncio.sleep(0.2)  # Small delay between readings
            except Exception as e:
                logger.error(f"Failed to test MUX input {mux_input}: {e}")
        
        return results
    
    async def cleanup(self):
        """Cleanup hardware services"""
        try:
            # Disable all muxes before cleanup
            if self.gpio_service and self.initialized:
                logger.info("Disabling all multiplexers...")
                await self.gpio_service.disable_all_mux()
                logger.info("✓ All multiplexers disabled")
        except Exception as e:
            logger.warning(f"Error disabling muxes during cleanup: {e}")
        
        if self.gpio_service:
            await self.gpio_service.cleanup()
        if self.ads1115_service:
            await self.ads1115_service.cleanup()
        logger.info("✓ Hardware services cleaned up")

async def interactive_test():
    """Interactive testing mode"""
    tester = HardwareTester()
    
    # try:
    await tester.initialize()
    
    print("\n" + "="*60)
    print("🔧 FuseTester Hardware Test Utility")
    print("="*60)
    print()
    print("Available commands:")
    print("  1. Test specific ADC channel + MUX input")
    print("  2. Test all ADC channels (same MUX input)")
    print("  3. Test all MUX inputs (same ADC channel)")
    print("  4. Continuous monitoring")
    print("  5. Disable all multiplexers")
    print("  q. Quit")
    print()
    
    while True:
        try:
            choice = input("Enter command (1-5, q): ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == '1':
                adc_ch = int(input("Enter ADC channel (0-3): "))
                mux_in = int(input("Enter MUX input (0-15): "))
                
                if not (0 <= adc_ch <= 3):
                    print("❌ ADC channel must be 0-3")
                    continue
                if not (0 <= mux_in <= 15):
                    print("❌ MUX input must be 0-15")
                    continue
                
                await tester.test_specific_input(adc_ch, mux_in)
                
            elif choice == '2':
                mux_in = int(input("Enter MUX input (0-15): "))
                if not (0 <= mux_in <= 15):
                    print("❌ MUX input must be 0-15")
                    continue
                
                results = await tester.test_all_adc_channels(mux_in)
                print(f"\n📊 Summary for MUX input {mux_in}:")
                for r in results:
                    print(f"   ADC{r['adc_channel']} (Fuse {r['fuse_number']}): {r['voltage']:.4f}V")
                
            elif choice == '3':
                adc_ch = int(input("Enter ADC channel (0-3): "))
                if not (0 <= adc_ch <= 3):
                    print("❌ ADC channel must be 0-3")
                    continue
                
                results = await tester.test_mux_sweep(adc_ch)
                print(f"\n📊 Summary for ADC channel {adc_ch}:")
                for r in results:
                    print(f"   MUX{r['mux_input']:2d} (Fuse {r['fuse_number']}): {r['voltage']:.4f}V")
                
            elif choice == '4':
                adc_ch = int(input("Enter ADC channel (0-3): "))
                mux_in = int(input("Enter MUX input (0-15): "))
                interval = float(input("Enter interval in seconds (default 1.0): ") or "1.0")
                
                if not (0 <= adc_ch <= 3):
                    print("❌ ADC channel must be 0-3")
                    continue
                if not (0 <= mux_in <= 15):
                    print("❌ MUX input must be 0-15")
                    continue
                
                print(f"\n🔄 Continuous monitoring ADC{adc_ch}, MUX{mux_in} (Press Ctrl+C to stop)")
                try:
                    while True:
                        result = await tester.test_specific_input(adc_ch, mux_in)
                        print(f"Fuse {result['fuse_number']}: {result['voltage']:.4f}V")
                        await asyncio.sleep(interval)
                except KeyboardInterrupt:
                    print("\n⏹️ Monitoring stopped")
                
            elif choice == '5':
                print("🔌 Disabling all multiplexers...")
                try:
                    await tester.gpio_service.disable_all_mux()
                    print("✓ All multiplexers disabled successfully")
                    print("   All MUX enable pins set to LOW")
                    print("   Hardware is now in safe state")
                except Exception as e:
                    print(f"❌ Error disabling multiplexers: {e}")
                
            else:
                print("❌ Invalid choice")
            
            print()
            
        except ValueError:
            print("❌ Please enter valid numbers")
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            logger.error(f"Test error: {e}")
  
    # finally:
        # await tester.cleanup()

async def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Command line arguments for automated testing
        if len(sys.argv) >= 3:
            adc_ch = int(sys.argv[1])
            mux_in = int(sys.argv[2])
            
            tester = HardwareTester()
            # try:
            await tester.initialize()
            await tester.test_specific_input(adc_ch, mux_in)
            # finally:
            #     await tester.cleanup()
        else:
            print("Usage: python3 test_hardware.py [adc_channel] [mux_input]")
            print("   Or: python3 test_hardware.py    (for interactive mode)")
    else:
        # Interactive mode
        await interactive_test()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
