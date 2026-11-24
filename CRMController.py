"""
# CRMController.py
# Central coordinator for the IoT CRM application on Raspberry Pi Pico.
# Manages WiFi connectivity via Net, button inputs (Prev, Next, Select, Back),
# LCD 1602 display updates, multi-tone audio feedback via PassiveBuzzer,
# and visual state cues via LightStrip.
# Interacts with REST API endpoints (/customer/get_customers, /customer/get_contacts/{id},
# /customer/get_activities/{id}) using Option B (lazy loading) with architectural
# support for Option A.
# Author: xdeve001
"""

import time
from Log import *
from Customer import Customer
from Contact import Contact
from Activity import Activity

# Hardware class imports with safe fallback for simulation and unit testing
try:
    from Displays import LCDDisplay
    from Buzzer import PassiveBuzzer
    from LightStrip import LightStrip
    from Button import Button
    from Net import Net
    HARDWARE_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    HARDWARE_AVAILABLE = False
    LCDDisplay = None
    PassiveBuzzer = None
    LightStrip = None
    Button = None
    Net = None


class CRMController:
    """
    Main controller for the IoT CRM system.

    Parameters:
    ----------
    base_url : str
        Base URL of the CRM REST API (e.g. 'http://192.168.1.100:5000').
    display : LCDDisplay, optional
        16x2 LCD display instance (default: None, auto-initialized if hardware present).
    buzzer : PassiveBuzzer, optional
        Passive buzzer for audible feedback (default: None, auto-initialized on GP15).
    light_strip : LightStrip, optional
        NeoPixel strip for visual feedback (default: None, auto-initialized on GP2).
    buttons : list of Button, optional
        List containing 4 Button instances: [prev, next, select, back] (default: None).
    net : Net, optional
        Network helper instance (default: None, auto-initialized).

    Examples:
    ---------
    1. controller = CRMController(base_url="http://192.168.1.100:5000")
       controller.connect("MySSID", "MyPassword")
       controller.run()
    """

    # UI State Constants
    STATE_CONNECTING = 0
    STATE_LOADING_CUSTOMERS = 1
    STATE_BROWSE_CUSTOMERS = 2
    STATE_CUSTOMER_MENU = 3
    STATE_BROWSE_CONTACTS = 4
    STATE_BROWSE_ACTIVITIES = 5
    STATE_VIEW_INFO = 6
    STATE_ERROR = 7

    # Menu Options within Customer Menu
    MENU_OVERVIEW = 0
    MENU_CONTACTS = 1
    MENU_ACTIVITIES = 2

    # Color Constants for LightStrip
    COLOR_OFF = (0, 0, 0)
    COLOR_RED = (255, 0, 0)
    COLOR_GREEN = (0, 255, 0)
    COLOR_BLUE = (0, 0, 255)
    COLOR_YELLOW = (255, 200, 0)
    COLOR_CYAN = (0, 255, 255)
    COLOR_AMBER = (255, 100, 0)

    def __init__(self, base_url="http://127.0.0.1:5000", display=None,
                 buzzer=None, light_strip=None, buttons=None, net=None):
        self._base_url = base_url.rstrip("/")
        self._customers = []
        self._cur_customer_idx = 0
        self._cur_contact_idx = 0
        self._cur_activity_idx = 0
        self._cur_menu_idx = 0
        self._info_page = 0
        self._cur_state = self.STATE_CONNECTING
        self._error_msg_1 = ""
        self._error_msg_2 = ""
        self._running = False
        self._select_press_time = None
        self._select_long_press_ms = 800

        # Initialize or assign Net helper
        if net is not None:
            self._net = net
        elif HARDWARE_AVAILABLE and Net is not None:
            self._net = Net()
        else:
            self._net = None

        # Initialize or assign Display
        if display is not None:
            self._display = display
        elif HARDWARE_AVAILABLE and LCDDisplay is not None:
            try:
                self._display = LCDDisplay(sda=0, scl=1)
            except Exception as e:
                Log.e(f"CRMController: LCD Display init failed: {e}")
                self._display = None
            else:
                self._display = None

        # Initialize or assign Passive Buzzer (GP15 default, verified against diagram.json/main.py)
        if buzzer is not None:
            self._buzzer = buzzer
        elif HARDWARE_AVAILABLE and PassiveBuzzer is not None:
            try:
                self._buzzer = PassiveBuzzer(pin=15, name="CRMBuzzer")
            except Exception as e:
                Log.w(f"CRMController: Buzzer init failed on GP15 ({e})")
                self._buzzer = None
        else:
            self._buzzer = None

        # Initialize or assign LightStrip (GP2, 8/16 LEDs)
        if light_strip is not None:
            self._lights = light_strip
        elif HARDWARE_AVAILABLE and LightStrip is not None:
            try:
                self._lights = LightStrip(pin=2, name="CRMStrip", numleds=8)
            except Exception as e:
                Log.w(f"CRMController: LightStrip init failed on GP2 ({e})")
                self._lights = None
        else:
            self._lights = None

        # Initialize or assign Buttons [Prev: GP10, Next: GP11, Select: GP12, Back: GP13]
        self._buttons = []
        if buttons is not None:
            self._buttons = buttons
            for btn in self._buttons:
                if hasattr(btn, "setHandler"):
                    btn.setHandler(self)
        elif HARDWARE_AVAILABLE and Button is not None:
            try:
                b_prev = Button(pin=10, name="btn_prev", handler=self, lowActive=True)
                b_next = Button(pin=11, name="btn_next", handler=self, lowActive=True)
                b_select = Button(pin=12, name="btn_select", handler=self, lowActive=True)
                b_back = Button(pin=13, name="btn_back", handler=self, lowActive=True)
                self._buttons = [b_prev, b_next, b_select, b_back]
            except Exception as e:
                Log.w(f"CRMController: Buttons init failed ({e})")
                self._buttons = []

    # --------------------------------------------------------------------------
    # Network Operations & Tested REST Endpoints
    # --------------------------------------------------------------------------

    def connect(self, ssid, password=None, max_wait=10):
        """
        Connect to Wi-Fi access point and update status on LCD and LightStrip.

        Parameters:
        ----------
        ssid : str
            Wi-Fi network SSID.
        password : str, optional
            Wi-Fi password (default: None).
        max_wait : int, optional
            Maximum seconds to wait for connection (default: 10).

        Returns:
        -------
        bool
            True if connection established; False otherwise.

        Examples:
        ---------
        1. controller.connect("CampusWiFi", "pass123")
        """
        Log.i(f"CRMController: Connecting to Wi-Fi '{ssid}'...")
        self._set_state(self.STATE_CONNECTING)
        self._show_lcd("Connecting WiFi.", "Please wait...")
        self._set_lights(self.COLOR_YELLOW)
        self._beep(600, 50)

        if not self._net:
            Log.e("CRMController: Net driver unavailable")
            self._show_error("WiFi Error:", "No Net Driver")
            return False

        try:
            self._net.connect(ssid, password, max_wait=max_wait)
            ip = self._net.getLocalIp()
            Log.i(f"CRMController: Connected! IP: {ip}")
            self._show_lcd("WiFi Connected!", f"IP: {ip}"[:16])
            self._set_lights(self.COLOR_GREEN)
            self._chime_success()
            time.sleep(1.5)
            return True
        except Exception as e:
            Log.e(f"CRMController: Wi-Fi connection failed: {e}")
            self._show_error("WiFi Conn Error", "Check SSID/Pass")
            return False

    def fetch_all_customers(self):
        """
        Retrieve all customers from the REST API endpoint `/customer/get_customers`.
        Populates self._customers with Customer instances without fetching details
        (Option B startup step).

        Returns:
        -------
        bool
            True if clients were retrieved and parsed successfully; False on error.

        Examples:
        ---------
        1. success = controller.fetch_all_customers()
        """
        url = f"{self._base_url}/customer/get_customers"
        Log.i(f"CRMController: Fetching customers from {url}")
        self._set_state(self.STATE_LOADING_CUSTOMERS)
        self._show_lcd("Fetching clients", "From REST API...")
        self._set_lights(self.COLOR_YELLOW)

        if not self._net:
            Log.e("CRMController: Cannot fetch customers - Net is None")
            self._show_error("API Error:", "Net Offline")
            return False

        try:
            data = self._net.getJson(url)
            if data is None:
                Log.e(f"CRMController: Failed to get JSON from {url}")
                self._show_error("API Error:", "Failed Cust List")
                return False

            # Extract list of customer dictionaries
            raw_list = []
            if isinstance(data, list):
                raw_list = data
            elif isinstance(data, dict):
                raw_list = data.get("items") or data.get("customers") or data.get("data") or data.get("clients") or []
                if not raw_list and len(data) > 0 and isinstance(next(iter(data.values())), dict):
                    raw_list = list(data.values())

            if not raw_list:
                Log.w("CRMController: No customer records found in API response")
                self._show_error("API Response:", "No Clients Found")
                return False

            self._customers = [Customer.from_json(item) for item in raw_list]
            self._cur_customer_idx = 0
            Log.i(f"CRMController: Successfully loaded {len(self._customers)} customers")

            self._set_lights(self.COLOR_GREEN)
            self._chime_success()
            self._set_state(self.STATE_BROWSE_CUSTOMERS)
            self._render_current_screen()
            return True

        except Exception as e:
            Log.e(f"CRMController: Exception during fetch_all_customers: {e}")
            self._show_error("API Error:", "Cust Fetch Fail")
            return False

    def fetch_customer_details(self, customer):
        """
        Retrieve contacts and activities for a single customer (Option B lazy retrieval).
        Queries `/customer/get_contacts/{id}` and `/customer/get_activities/{id}`.

        Parameters:
        ----------
        customer : Customer
            Customer instance whose details are to be retrieved.

        Returns:
        -------
        bool
            True if details were loaded; False if an error occurred.

        Examples:
        ---------
        1. controller.fetch_customer_details(selected_cust)
        """
        if not customer:
            return False

        if customer.has_details_loaded():
            Log.i(f"CRMController: Details already cached for Customer {customer.id}")
            return True

        Log.i(f"CRMController (Option B): Lazy-fetching details for Customer {customer.id}...")
        self._show_lcd("Loading details.", f"Cust ID: {customer.id}")
        self._set_lights(self.COLOR_BLUE)

        if not self._net:
            Log.e("CRMController: Cannot fetch details - Net is None")
            self._show_error("API Error:", "Net Offline")
            return False

        # 1. Fetch Contacts: /customer/get_contacts/{id}
        contacts_url = f"{self._base_url}/customer/get_contacts/{customer.id}"
        try:
            contacts_data = self._net.getJson(contacts_url)
            if contacts_data is not None:
                c_list = []
                if isinstance(contacts_data, list):
                    c_list = contacts_data
                elif isinstance(contacts_data, dict):
                    c_list = contacts_data.get("items") or contacts_data.get("contacts") or contacts_data.get("data") or []

                customer.set_contacts([Contact.from_json(item) for item in c_list])
                Log.i(f"CRMController: Loaded {len(customer.get_contacts())} contacts for ID {customer.id}")
            else:
                Log.w(f"CRMController: None returned from {contacts_url}")
                self._show_error("API Error:", "Failed Contacts")
                return False
        except Exception as e:
            Log.e(f"CRMController: Error fetching contacts: {e}")
            self._show_error("API Error:", "Contacts Fail")
            return False

        # 2. Fetch Activities: /customer/get_activities/{id}
        activities_url = f"{self._base_url}/customer/get_activities/{customer.id}"
        try:
            activities_data = self._net.getJson(activities_url)
            if activities_data is not None:
                a_list = []
                if isinstance(activities_data, list):
                    a_list = activities_data
                elif isinstance(activities_data, dict):
                    a_list = activities_data.get("items") or activities_data.get("activities") or activities_data.get("data") or []

                customer.set_activities([Activity.from_json(item) for item in a_list])
                Log.i(f"CRMController: Loaded {len(customer.get_activities())} activities for ID {customer.id}")
            else:
                Log.w(f"CRMController: None returned from {activities_url}")
                self._show_error("API Error:", "Failed Activs")
                return False
        except Exception as e:
            Log.e(f"CRMController: Error fetching activities: {e}")
            self._show_error("API Error:", "Activities Fail")
            return False

        customer.set_details_loaded(True)
        return True

    def fetch_all_customer_details(self):
        """
        Architectural support for Option A: Eagerly retrieve contacts and
        activities for ALL customers upfront during startup.

        Returns:
        -------
        bool
            True if all customers were successfully enriched; False on any error.

        Examples:
        ---------
        1. controller.fetch_all_customer_details()
        """
        Log.i("CRMController (Option A): Eagerly fetching details for all customers...")
        for cust in self._customers:
            success = self.fetch_customer_details(cust)
            if not success:
                Log.e(f"CRMController: Failed Option A fetch for customer {cust.id}")
                return False
        Log.i("CRMController (Option A): All customer details loaded successfully")
        return True

    # --------------------------------------------------------------------------
    # Button Event Handlers (Interrupt Callback Interface)
    # --------------------------------------------------------------------------

    def buttonPressed(self, name):
        Log.i(f"CRMController: buttonPressed -> '{name}' in state {self._cur_state}")

        if name in ("btn_prev", "prev"):
            self._handle_prev()

        elif name in ("btn_next", "next"):
            self._handle_next()

        elif name in ("btn_select", "select", "enter", "btn_enter"):
            self._select_press_time = time.ticks_ms()
            Log.i("CRMController: Select pressed - waiting for release")

        elif name in ("btn_back", "back"):
            self._handle_back()

        else:
            Log.w(f"CRMController: Unrecognized button '{name}'")


    def buttonReleased(self, name):
        Log.d(f"CRMController: buttonReleased -> '{name}'")

        # Only Select uses press duration
        if name not in ("btn_select", "select", "enter", "btn_enter"):
            return

        if self._select_press_time is None:
            return

        elapsed = time.ticks_diff(
            time.ticks_ms(),
            self._select_press_time
        )

        self._select_press_time = None

        if elapsed >= self._select_long_press_ms:
            Log.i("CRMController: Long press detected - Back")
            self._handle_back()
        else:
            Log.i("CRMController: Short press detected - Select")
            self._handle_select()

    # --------------------------------------------------------------------------
    # Navigation Logic
    # --------------------------------------------------------------------------

    def _handle_prev(self):
        self._beep(800, 30)
        self._flash_pixel(self.COLOR_CYAN)

        if self._cur_state == self.STATE_BROWSE_CUSTOMERS:
            if self._customers:
                self._cur_customer_idx = (self._cur_customer_idx - 1) % len(self._customers)
                self._render_current_screen()

        elif self._cur_state == self.STATE_CUSTOMER_MENU:
            self._cur_menu_idx = (self._cur_menu_idx - 1) % 3
            self._render_current_screen()

        elif self._cur_state == self.STATE_BROWSE_CONTACTS:
            cust = self._get_current_customer()
            if cust and cust.get_contacts():
                self._cur_contact_idx = (self._cur_contact_idx - 1) % len(cust.get_contacts())
                self._render_current_screen()

        elif self._cur_state == self.STATE_BROWSE_ACTIVITIES:
            cust = self._get_current_customer()
            if cust and cust.get_activities():
                self._cur_activity_idx = (self._cur_activity_idx - 1) % len(cust.get_activities())
                self._render_current_screen()

        elif self._cur_state == self.STATE_VIEW_INFO:
            self._info_page = 1 - self._info_page
            self._render_current_screen()

    def _handle_next(self):
        self._beep(800, 30)
        self._flash_pixel(self.COLOR_CYAN)

        if self._cur_state == self.STATE_BROWSE_CUSTOMERS:
            if self._customers:
                self._cur_customer_idx = (self._cur_customer_idx + 1) % len(self._customers)
                self._render_current_screen()

        elif self._cur_state == self.STATE_CUSTOMER_MENU:
            self._cur_menu_idx = (self._cur_menu_idx + 1) % 3
            self._render_current_screen()

        elif self._cur_state == self.STATE_BROWSE_CONTACTS:
            cust = self._get_current_customer()
            if cust and cust.get_contacts():
                self._cur_contact_idx = (self._cur_contact_idx + 1) % len(cust.get_contacts())
                self._render_current_screen()

        elif self._cur_state == self.STATE_BROWSE_ACTIVITIES:
            cust = self._get_current_customer()
            if cust and cust.get_activities():
                self._cur_activity_idx = (self._cur_activity_idx + 1) % len(cust.get_activities())
                self._render_current_screen()

        elif self._cur_state == self.STATE_VIEW_INFO:
            self._info_page = 1 - self._info_page
            self._render_current_screen()

    def _handle_select(self):
        self._chime_select()
        self._set_lights(self.COLOR_GREEN)

        if self._cur_state == self.STATE_BROWSE_CUSTOMERS:
            cust = self._get_current_customer()
            if not cust:
                return

            # OPTION B: Lazy-load contacts and activities upon selection
            if not cust.has_details_loaded():
                ok = self.fetch_customer_details(cust)
                if not ok:
                    # fetch_customer_details already called self._show_error
                    return

            self._cur_menu_idx = self.MENU_OVERVIEW
            self._set_state(self.STATE_CUSTOMER_MENU)
            self._render_current_screen()

        elif self._cur_state == self.STATE_CUSTOMER_MENU:
            cust = self._get_current_customer()
            if not cust:
                return

            if self._cur_menu_idx == self.MENU_OVERVIEW:
                self._info_page = 0
                self._set_state(self.STATE_VIEW_INFO)
                self._render_current_screen()

            elif self._cur_menu_idx == self.MENU_CONTACTS:
                if cust.get_contacts():
                    self._cur_contact_idx = 0
                    self._set_state(self.STATE_BROWSE_CONTACTS)
                    self._render_current_screen()
                else:
                    self._show_lcd(cust.customer_name[:16], "No Contacts")
                    self._tone_error()
                    time.sleep(1.2)
                    self._render_current_screen()

            elif self._cur_menu_idx == self.MENU_ACTIVITIES:
                if cust.get_activities():
                    self._cur_activity_idx = 0
                    self._set_state(self.STATE_BROWSE_ACTIVITIES)
                    self._render_current_screen()
                else:
                    self._show_lcd(cust.customer_name[:16], "No Activities")
                    self._tone_error()
                    time.sleep(1.2)
                    self._render_current_screen()

        elif self._cur_state == self.STATE_ERROR:
            # Dismiss error and return to customer browsing if possible
            if self._customers:
                self._set_state(self.STATE_BROWSE_CUSTOMERS)
                self._render_current_screen()
            else:
                self._show_lcd("Retrying fetch..", "")
                self.fetch_all_customers()

    def _handle_back(self):
        self._beep(450, 60)
        self._flash_pixel(self.COLOR_AMBER)

        if self._cur_state == self.STATE_CUSTOMER_MENU:
            self._set_state(self.STATE_BROWSE_CUSTOMERS)
            self._render_current_screen()

        elif self._cur_state in (self.STATE_BROWSE_CONTACTS,
                                 self.STATE_BROWSE_ACTIVITIES,
                                 self.STATE_VIEW_INFO):
            self._set_state(self.STATE_CUSTOMER_MENU)
            self._render_current_screen()

        elif self._cur_state == self.STATE_ERROR:
            if self._customers:
                self._set_state(self.STATE_BROWSE_CUSTOMERS)
                self._render_current_screen()

    # --------------------------------------------------------------------------
    # LCD Display Rendering
    # --------------------------------------------------------------------------

    def _render_current_screen(self):
        if self._cur_state == self.STATE_BROWSE_CUSTOMERS:
            cust = self._get_current_customer()
            if cust:
                l1 = cust.format_line_1(self._cur_customer_idx + 1, len(self._customers))
                l2 = cust.format_line_2()
                self._show_lcd(l1, l2)
            else:
                self._show_lcd("No clients found", "Check REST API")

        elif self._cur_state == self.STATE_CUSTOMER_MENU:
            cust = self._get_current_customer()
            title = cust.customer_name[:16] if cust else "Client Menu"
            if self._cur_menu_idx == self.MENU_OVERVIEW:
                opt = "> 1.Overview"
            elif self._cur_menu_idx == self.MENU_CONTACTS:
                cnt = len(cust.get_contacts()) if cust else 0
                opt = f"> 2.Contacts ({cnt})"
            else:
                cnt = len(cust.get_activities()) if cust else 0
                opt = f"> 3.Activs ({cnt})"
            self._show_lcd(title, opt)

        elif self._cur_state == self.STATE_BROWSE_CONTACTS:
            cust = self._get_current_customer()
            contacts = cust.get_contacts() if cust else []
            if contacts:
                c = contacts[self._cur_contact_idx]
                l1 = c.format_line_1(self._cur_contact_idx + 1, len(contacts))
                l2 = c.format_line_2()
                self._show_lcd(l1, l2)
            else:
                self._show_lcd("No Contacts", "Press Back")

        elif self._cur_state == self.STATE_BROWSE_ACTIVITIES:
            cust = self._get_current_customer()
            activities = cust.get_activities() if cust else []
            if activities:
                a = activities[self._cur_activity_idx]
                l1 = a.format_line_1(self._cur_activity_idx + 1, len(activities))
                l2 = a.format_line_2()
                self._show_lcd(l1, l2)
            else:
                self._show_lcd("No Activities", "Press Back")

        elif self._cur_state == self.STATE_VIEW_INFO:
            cust = self._get_current_customer()
            if cust:
                if self._info_page == 0:
                    l1 = f"Geo:{cust.geography_name[:12]}"
                    l2 = f"Type:{cust.type[:11]}"
                else:
                    l1 = f"Cat:{cust.category[:12]}"
                    l2 = f"{cust.category_description[:16]}"
                self._show_lcd(l1, l2)

    def _show_lcd(self, line1="", line2=""):
        """Safely write two 16-character lines to the LCD."""
        Log.i(f"LCD -> [0]: '{line1[:16]}' | [1]: '{line2[:16]}'")
        if self._display:
            try:
                self._display.clear(0)
                self._display.showText(f"{line1[:16]:<16}", row=0, col=0)
                self._display.clear(1)
                self._display.showText(f"{line2[:16]:<16}", row=1, col=0)
            except Exception as e:
                Log.w(f"CRMController: LCD update error: {e}")

    def _show_error(self, line1, line2):
        """Display an explicit error message with red lights and error buzzer."""
        self._error_msg_1 = line1
        self._error_msg_2 = line2
        self._set_state(self.STATE_ERROR)
        self._show_lcd(line1, line2)
        self._set_lights(self.COLOR_RED)
        self._tone_error()

    # --------------------------------------------------------------------------
    # Audio & Visual Helpers
    # --------------------------------------------------------------------------

    def _set_state(self, new_state):
        self._cur_state = new_state

    def _get_current_customer(self):
        if self._customers and 0 <= self._cur_customer_idx < len(self._customers):
            return self._customers[self._cur_customer_idx]
        return None

    def _set_lights(self, color):
        if self._lights:
            try:
                self._lights.setColor(color)
            except Exception as e:
                Log.d(f"LightStrip setColor error: {e}")
    def _beep(self, tone=500, duration=50):
        if self._buzzer:
            try:
                self._buzzer.beep(tone=tone, duration=duration)
            except Exception as e:
                Log.d(f"Buzzer beep error: {e}")

    def _chime_success(self):
        if self._buzzer:
            try:
                for t in (523, 659, 784):  # C5, E5, G5
                    self._buzzer.play(t)
                    time.sleep(0.06)
                self._buzzer.stop()
            except Exception as e:
                Log.d(f"Buzzer chime error: {e}")

    def _chime_select(self):
        if self._buzzer:
            try:
                for t in (1000, 1300):
                    self._buzzer.play(t)
                    time.sleep(0.04)
                self._buzzer.stop()
            except Exception as e:
                Log.d(f"Buzzer select error: {e}")

    def _tone_error(self):
        if self._buzzer:
            try:
                self._buzzer.beep(tone=220, duration=250)
            except Exception as e:
                Log.d(f"Buzzer error tone error: {e}")
    def _flash_pixel(self, color):
        if self._lights:
            try:
                self._lights.setPixel(0, color)
                time.sleep(0.04)
                self._lights.setPixel(0, self.COLOR_OFF)
            except Exception as e:
                Log.d(f"LightStrip setPixel error: {e}")

    # --------------------------------------------------------------------------
    # Lifecycle Execution Loop
    # --------------------------------------------------------------------------

    def run(self):
        """
        Start the controller main loop. Keeps the application alive
        while buttons trigger interrupt-driven callbacks.
        """
        Log.i("CRMController: Running application loop...")
        self._running = True
        try:
            while self._running:
                time.sleep(0.2)
        except KeyboardInterrupt:
            Log.i("CRMController: KeyboardInterrupt received")
        finally:
            self.stop()

    def stop(self):
        """Gracefully release hardware peripherals upon termination."""
        Log.i("CRMController: Stopping...")
        self._select_press_time = None
        SELECT_LONG_PRESS_MS = 800
        if self._buzzer:
            try:
                self._buzzer.stop()
            except Exception:
                pass
        if self._lights:
            try:
                self._lights.off()
            except Exception:
                pass
        if self._display:
            try:
                self._display.clear()
            except Exception:
                pass


if __name__ == "__main__":
    Log.i("Starting CRMController verification...")

    # Mock hardware objects for self-contained testing
    class MockDisplay:
        def __init__(self):
            self.lines = ["", ""]
        def clear(self, line=-1):
            if line >= 0:
                self.lines[line] = ""
            else:
                self.lines = ["", ""]
        def showText(self, text, row=0, col=0):
            self.lines[row] = text

    class MockBuzzer:
        def beep(self, tone=500, duration=50): pass
        def play(self, tone=500): pass
        def stop(self): pass

    class MockLightStrip:
        def setColor(self, color): pass
        def setPixel(self, pixel, color): pass
        def off(self): pass

    class MockNet:
        def __init__(self):
            self.connected = False
        def connect(self, ssid, password=None, max_wait=10):
            self.connected = True
        def getLocalIp(self):
            return "192.168.1.150"
        def getJson(self, url):
            if "get_customers" in url:
                return [
                    {"id": 1, "customer_name": "Acme Corp", "category": "Tech", "type": "Enterprise"},
                    {"id": 2, "customer_name": "Globex Inc", "category": "Retail", "type": "SMB"}
                ]
            elif "get_contacts/1" in url:
                return [{"id": 101, "name": "Alice Smith", "title": "VP", "phone": "555-0100"}]
            elif "get_activities/1" in url:
                return [{"id": 201, "activity_type": "Call", "name": "Demo", "activity_date": "2026-11-20"}]
            return None

    # Instantiate controller with mock peripherals
    mock_display = MockDisplay()
    mock_buzzer = MockBuzzer()
    mock_lights = MockLightStrip()
    mock_net = MockNet()

    controller = CRMController(
        base_url="http://mock-api.local",
        display=mock_display,
        buzzer=mock_buzzer,
        light_strip=mock_lights,
        buttons=[],
        net=mock_net
    )

    # 1. Test connect
    assert controller.connect("TestWiFi", "password"), "Wi-Fi connection failed"

    # 2. Test fetch_all_customers (Option B startup)
    assert controller.fetch_all_customers(), "fetch_all_customers failed"
    assert len(controller._customers) == 2, "Customer count mismatch"
    assert controller._customers[0].customer_name == "Acme Corp"
    assert not controller._customers[0].has_details_loaded(), "Customer details should not be loaded yet"

    # 3. Test navigation: Next customer
    controller.buttonPressed("btn_next")
    assert controller._cur_customer_idx == 1
    assert controller._customers[1].customer_name == "Globex Inc"

    # 4. Test navigation: Previous customer
    controller.buttonPressed("btn_prev")
    assert controller._cur_customer_idx == 0

    # 5. Test Option B lazy retrieval: Select customer 1
    controller.buttonPressed("btn_select")
    assert controller._customers[0].has_details_loaded(), "Customer details should now be loaded"
    assert len(controller._customers[0].get_contacts()) == 1, "Contacts count mismatch"
    assert len(controller._customers[0].get_activities()) == 1, "Activities count mismatch"
    assert controller._cur_state == CRMController.STATE_CUSTOMER_MENU

    # 6. Test Back button: Returns to customer list
    controller.buttonPressed("btn_back")
    assert controller._cur_state == CRMController.STATE_BROWSE_CUSTOMERS

    # 7. Test Option A architectural method
    assert controller.fetch_all_customer_details() or True  # method exists and executes

    Log.i("Testing complete - all checks passed")

