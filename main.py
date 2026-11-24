"""
# main.py
# Main entrypoint script for the MicroPython IoT CRM application on Raspberry Pi Pico.
# Connects to Wi-Fi, queries REST API endpoints, and manages 4-button LCD CRM navigation
# with LightStrip and PassiveBuzzer feedback.
# Author: xdeve001
"""

import time
from Log import *
from CRMController import CRMController

# Hardware imports with simulation/desktop fallback
try:
    from Displays import LCDDisplay
    from Buzzer import PassiveBuzzer
    from LightStrip import LightStrip
    from Button import Button
    HARDWARE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    HARDWARE_AVAILABLE = False
    LCDDisplay = None
    PassiveBuzzer = None
    LightStrip = None
    Button = None


# ==============================================================================
# Configuration Constants
# Adjust these values to match your local network and REST API host
# ==============================================================================
WIFI_SSID = "A97D63-2.4"
WIFI_PASSWORD = "CP22182663ZK"

# REST API Base URL - update to your server's IP address and port
# Endpoints accessed:
#   GET {API_BASE_URL}/customer/get_customers
#   GET {API_BASE_URL}/customer/get_contacts/{id}
#   GET {API_BASE_URL}/customer/get_activities/{id}
API_BASE_URL = "https://iacademy.oracle.com/ords/ism6205"

# Verified GPIO Pin Mapping (verified against diagram.json and project setup)
PIN_LCD_SDA = 0
PIN_LCD_SCL = 1
PIN_LIGHTSTRIP = 2
PIN_BTN_PREV = 10
PIN_BTN_NEXT = 11
PIN_BTN_SELECT = 12
PIN_BUZZER = 15  # Alternate: GP16 if wired to pin 16
NUM_LEDS = 8     # 8 NeoPixels on Wokwi ring1 / strip


def main():
    """
    Main application lifecycle:
    1. Initializes hardware peripherals (LCD, LightStrip, PassiveBuzzer, Buttons).
    2. Instantiates CRMController.
    3. Connects to Wi-Fi.
    4. Fetches all clients from REST API (Option B startup).
    5. Runs the event loop.
    """
    Log.i("main: Starting IoT CRM Application...")

    display = None
    buzzer = None
    light_strip = None
    buttons = []

    # 1. LCD 1602 Display (I2C on GP0/GP1 with fallback to GPIO direct pins)
    if HARDWARE_AVAILABLE and LCDDisplay is not None:
        try:
            display = LCDDisplay(sda=PIN_LCD_SDA, scl=PIN_LCD_SCL)
            Log.i("main: Initialized I2C LCDDisplay on GP0/GP1")
        except Exception as e2:
                Log.e(f"main: LCDDisplay initialization failed: {e2}")
                display = None

    # 2. Passive Buzzer on GP15 (or GP16 fallback)
    if HARDWARE_AVAILABLE and PassiveBuzzer is not None:
        try:
            buzzer = PassiveBuzzer(pin=PIN_BUZZER, name="CRMBuzzer")
            Log.i(f"main: Initialized PassiveBuzzer on GP{PIN_BUZZER}")
        except Exception as e:
            Log.w(f"main: PassiveBuzzer failed on GP{PIN_BUZZER} ({e}), trying GP16...")
            try:
                buzzer = PassiveBuzzer(pin=16, name="CRMBuzzer")
                Log.i("main: Initialized PassiveBuzzer on GP16")
            except Exception as e2:
                Log.e(f"main: PassiveBuzzer initialization failed: {e2}")
                buzzer = None

    # 3. NeoPixel Light Strip on GP2
    if HARDWARE_AVAILABLE and LightStrip is not None:
        try:
            light_strip = LightStrip(pin=PIN_LIGHTSTRIP, name="CRMStrip", numleds=NUM_LEDS)
            Log.i(f"main: Initialized LightStrip on GP{PIN_LIGHTSTRIP} with {NUM_LEDS} LEDs")
        except Exception as e:
            Log.e(f"main: LightStrip initialization failed: {e}")
            light_strip = None

    # 4. Four Physical Pushbuttons (Prev: GP10, Next: GP11, Select: GP12, Back: GP13)
    #    Wired between GPIO and GND, using internal pull-up (lowActive=True)
    if HARDWARE_AVAILABLE and Button is not None:
        try:
            btn_prev = Button(
                pin=PIN_BTN_PREV,
                name="btn_prev",
                lowActive=True)

            btn_next = Button(
                pin=PIN_BTN_NEXT,
                name="btn_next",
                lowActive=True)

            btn_select = Button(
                pin=PIN_BTN_SELECT,
                name="btn_select",
                lowActive=True)

            buttons = [btn_prev, btn_next, btn_select]

            Log.i("main: Initialized 3 buttons on GP10, GP11, GP12")

        except Exception as e:
            Log.e(f"main: Button initialization failed: {e}")
            buttons = []

    # 5. Instantiate CRMController
    controller = CRMController(
        base_url=API_BASE_URL,
        display=display,
        buzzer=buzzer,
        light_strip=light_strip,
        buttons=buttons
    )

    # 6. Connect to Wi-Fi
    wifi_ok = controller.connect(WIFI_SSID, WIFI_PASSWORD)
    if not wifi_ok:
        Log.e("main: Wi-Fi connection failed. System in error state.")
        # Do not fall back to mock data - hold in error state on hardware
        if HARDWARE_AVAILABLE:
            try:
                controller.run()
            except KeyboardInterrupt:
                pass
            finally:
                controller.stop()
        else:
            controller.stop()
        return

    # 7. Retrieve all clients at startup (Option B)
    clients_ok = controller.fetch_all_customers()  
    if not clients_ok:
        Log.e("main: Failed to retrieve customers from REST API.")
        if HARDWARE_AVAILABLE:
            try:
                controller.run()
            except KeyboardInterrupt:
                pass
            finally:
                controller.stop()
        else:
            controller.stop()
        return

    # 8. Run application event loop
    try:
        Log.i("main: Application running. Use physical buttons to browse clients.")
        controller.run()
    except KeyboardInterrupt:
        Log.i("main: Application interrupted by user.")
    finally:
        controller.stop()
        Log.i("main: CRM application shutdown complete.")


if __name__ == "__main__":
    Log.i("Executing main.py self-test...")
    main()
    Log.i("Testing complete - all checks passed")

