"""
# NamePlate.py
# Object-Oriented controller implementation for an interactive Employee NamePlate
# Author: insert your name here
"""

import time
from Log import *
try:
    from Lights import GREEN, YELLOW, RED, WHITE, BLACK
except (ImportError, ModuleNotFoundError):
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 200, 0)
    GREEN = (0, 255, 0)
    WHITE = (255, 255, 255)
from Employee import Employee

# Safe MicroPython/CPython time helper definitions
try:
    ticks_ms = time.ticks_ms
    ticks_diff = time.ticks_diff
    sleep_ms = time.sleep_ms
except AttributeError:
    ticks_ms = lambda: int(time.time() * 1000)
    ticks_diff = lambda a, b: a - b
    sleep_ms = lambda ms: time.sleep(ms / 1000.0)


class NamePlate:
    """
    Main controller class for the Employee NamePlate digital system.
    Coordinates the LCD display, navigation and status buttons, passive buzzer audio,
    and NeoPixel light strip status indicators.

    Parameters:
    ----------
    employees : list of Employee
        List of configured employee instances to cycle and display
    display : LCDDisplay
        LCDDisplay hardware instance for displaying text pages
    buttons : list of Button
        List containing [btnPrev, btnNext, btnStatus]
    buzzer : PassiveBuzzer
        PassiveBuzzer hardware instance for audible feedback
    lightStrip : LightStrip
        LightStrip hardware instance for availability color-coding
    pageInterval : int, optional
        Interval in seconds before rotating to the next information page (default: 3)

    Examples:
    ---------
    1. nameplate = NamePlate(employees, display, [btn_prev, btn_next, btn_status], buzzer, light_strip)
       nameplate.nextEmployee()
       nameplate.cycleAvailability()
       nameplate.run()
    """

    def __init__(self, employees, display, buttons, buzzer, lightStrip, pageInterval=3):
        """Initialize controller attributes, bind button handlers, and setup initial state."""
        self._employees = employees if employees is not None else []
        self._currentIndex = 0
        self._currentPage = 0
        self._pageInterval = pageInterval
        self._display = display
        self._buzzer = buzzer
        self._lightStrip = lightStrip
        self._running = False

        # Extract the three individual buttons
        if isinstance(buttons, (list, tuple)) and len(buttons) >= 3:
            self._btnPrev = buttons[0]
            self._btnNext = buttons[1]
            self._btnStatus = buttons[2]
        else:
            self._btnPrev = None
            self._btnNext = None
            self._btnStatus = None

        # Register NamePlate as the event handler for all three buttons
        if self._btnPrev:
            self._btnPrev.setHandler(self)
        if self._btnNext:
            self._btnNext.setHandler(self)
        if self._btnStatus:
            self._btnStatus.setHandler(self)

        Log.i(f"NamePlate initialized with {len(self._employees)} employees, pageInterval={self._pageInterval}s")
        self.updateDisplay()
        self.updateStatusLights()

    def getCurrentEmployee(self):
        """
        Get the currently active Employee object.

        Returns:
        -------
        Employee or None
            Current employee being displayed, or None if list is empty.
        """
        if not self._employees:
            return None
        return self._employees[self._currentIndex]

    def nextEmployee(self):
        """
        Navigate forward to the next employee in the list, wrapping to the start.
        Resets page index and updates display, lights, and sounds.
        """
        if not self._employees:
            return
        self._currentIndex = (self._currentIndex + 1) % len(self._employees)
        self._currentPage = 0
        emp = self.getCurrentEmployee()
        Log.i(f"NamePlate: Next employee selected -> {emp.name} (index {self._currentIndex})")
        self.playNavigationSound()
        self.updateDisplay()
        self.updateStatusLights()

    def previousEmployee(self):
        """
        Navigate backward to the previous employee in the list, wrapping to the end.
        Resets page index and updates display, lights, and sounds.
        """
        if not self._employees:
            return
        self._currentIndex = (self._currentIndex - 1) % len(self._employees)
        self._currentPage = 0
        emp = self.getCurrentEmployee()
        Log.i(f"NamePlate: Previous employee selected -> {emp.name} (index {self._currentIndex})")
        self.playNavigationSound()
        self.updateDisplay()
        self.updateStatusLights()

    def cycleAvailability(self):
        """
        Cycle the availability status of the currently selected employee.
        Emits a higher-pitch confirmation tone and refreshes display and status lights.
        """
        emp = self.getCurrentEmployee()
        if emp:
            new_status = emp.cycleAvailability()
            Log.i(f"NamePlate: Cycled availability of '{emp.name}' to '{new_status}'")
            if self._buzzer:
                try:
                    self._buzzer.beep(tone=1200, duration=100)
                except Exception as e:
                    Log.w(f"NamePlate buzzer error: {e}")
            self.updateDisplay()
            self.updateStatusLights()

    def rotateDisplayPage(self):
        """Advance to the next display page for the current employee if multi-page."""
        emp = self.getCurrentEmployee()
        if not emp:
            return
        pages = emp.getDisplayPages()
        if len(pages) > 1:
            self._currentPage = (self._currentPage + 1) % len(pages)
            Log.d(f"NamePlate: Rotated page to {self._currentPage + 1}/{len(pages)}")
            self.updateDisplay()

    def updateDisplay(self):
        """Render the current employee's current page to the LCDDisplay."""
        if not self._display:
            return
        emp = self.getCurrentEmployee()
        if not emp:
            try:
                self._display.showText(f"{'No Employees':<16}", row=0, col=0)
                self._display.showText(f"{'Configured':<16}", row=1, col=0)
            except Exception as e:
                Log.w(f"Display error: {e}")
            return

        pages = emp.getDisplayPages()
        if not pages:
            return

        page_idx = self._currentPage % len(pages)
        line1, line2 = pages[page_idx]

        # Format and pad to exactly 16 characters to overwrite LCD cleanly
        text_line1 = f"{line1[:16]:<16}"
        text_line2 = f"{line2[:16]:<16}"

        try:
            self._display.showText(text_line1, row=0, col=0)
            self._display.showText(text_line2, row=1, col=0)
        except Exception as e:
            Log.w(f"Display update error: {e}")

    def updateStatusLights(self):
        """Update the NeoPixel light strip color according to current employee availability."""
        if not self._lightStrip:
            return
        emp = self.getCurrentEmployee()
        if not emp:
            try:
                self._lightStrip.off()
            except Exception as e:
                Log.w(f"LightStrip error: {e}")
            return

        status = emp.getAvailability()
        try:
            if status == Employee.STATUS_AVAILABLE:
                self._lightStrip.setColor(GREEN)
            elif status == Employee.STATUS_AWAY:
                self._lightStrip.setColor(YELLOW)
            elif status == Employee.STATUS_BUSY:
                self._lightStrip.setColor(RED)
            else:
                self._lightStrip.setColor(WHITE)
        except Exception as e:
            Log.w(f"LightStrip setColor error: {e}")

    def playNavigationSound(self):
        """Play a short audible chirp when navigating between employees."""
        if self._buzzer:
            try:
                self._buzzer.beep(tone=800, duration=60)
            except Exception as e:
                Log.w(f"Buzzer navigation sound error: {e}")

    def buttonPressed(self, name):
        """
        Handle button pressed events dispatched by Button callbacks.

        Parameters:
        ----------
        name : str
            The name identifier of the pressed button
        """
        Log.i(f"NamePlate: buttonPressed from '{name}'")
        if self._btnPrev and name == self._btnPrev._name:
            self.previousEmployee()
        elif self._btnNext and name == self._btnNext._name:
            self.nextEmployee()
        elif self._btnStatus and name == self._btnStatus._name:
            self.cycleAvailability()
        else:
            Log.w(f"NamePlate: Received press from unmapped button '{name}'")

    def buttonReleased(self, name):
        """
        Handle button released events dispatched by Button callbacks.

        Parameters:
        ----------
        name : str
            The name identifier of the released button
        """
        Log.d(f"NamePlate: buttonReleased from '{name}'")

    def run(self):
        """
        Run the main execution loop, periodically rotating display pages
        while maintaining responsiveness to hardware button interrupts.
        """
        Log.i("NamePlate: Starting application run loop...")
        self._running = True
        self.updateDisplay()
        self.updateStatusLights()

        last_rotate_time = ticks_ms()
        interval_ms = self._pageInterval * 1000

        try:
            while self._running:
                now = ticks_ms()
                if ticks_diff(now, last_rotate_time) >= interval_ms:
                    self.rotateDisplayPage()
                    last_rotate_time = now
                sleep_ms(50)
        except KeyboardInterrupt:
            Log.i("NamePlate: Run loop stopped by KeyboardInterrupt.")
        finally:
            self.stop()

    def stop(self):
        """Stop the application loop and safely shut down hardware outputs."""
        self._running = False
        if self._lightStrip:
            try:
                self._lightStrip.off()
            except Exception:
                pass
        if self._buzzer:
            try:
                self._buzzer.stop()
            except Exception:
                pass
        if self._display:
            try:
                self._display.clear()
            except Exception:
                pass
        Log.i("NamePlate: Application safely stopped.")


if __name__ == "__main__":
    Log.i("Starting self-test for NamePlate.py...")

    # Mock classes to perform standalone non-hardware verification
    class MockDisplay:
        def __init__(self):
            self.lines = ["", ""]
        def showText(self, text, row=0, col=0):
            self.lines[row] = text
        def clear(self):
            self.lines = ["", ""]

    class MockBuzzer:
        def __init__(self):
            self.last_tone = None
        def beep(self, tone=500, duration=150):
            self.last_tone = tone
        def stop(self):
            self.last_tone = None

    class MockLightStrip:
        def __init__(self):
            self.last_color = None
        def setColor(self, color, numPixels=None):
            self.last_color = color
        def off(self):
            self.last_color = (0, 0, 0)

    class MockButton:
        def __init__(self, name):
            self._name = name
            self._handler = None
        def setHandler(self, handler):
            self._handler = handler
        def press(self):
            if self._handler:
                self._handler.buttonPressed(self._name)

    # 1. Setup mock components and sample employees
    from Employee import Employee, Faculty, Staff
    emp1 = Faculty("Dr. Alice", "Prof", "CS", "alice@univ.edu", "555-1111", courses=["CS101"], officeHours="MW 1-2")
    emp2 = Staff("Bob Jones", "Coordinator", "Eng", "bob@univ.edu", "555-2222", workSchedule="8-5")

    display = MockDisplay()
    buzzer = MockBuzzer()
    lights = MockLightStrip()
    btn_prev = MockButton("btn_prev")
    btn_next = MockButton("btn_next")
    btn_status = MockButton("btn_status")

    np = NamePlate(
        employees=[emp1, emp2],
        display=display,
        buttons=[btn_prev, btn_next, btn_status],
        buzzer=buzzer,
        lightStrip=lights,
        pageInterval=1
    )

    # Verify initial display and light state
    assert np.getCurrentEmployee() == emp1
    assert "Dr. Alice" in display.lines[0]
    assert lights.last_color == GREEN

    # 2. Test button navigation to next employee
    btn_next.press()
    assert np.getCurrentEmployee() == emp2
    assert "Bob Jones" in display.lines[0]
    assert buzzer.last_tone == 800

    # 3. Test cycling availability status
    btn_status.press()
    assert emp2.getAvailability() == Employee.STATUS_AWAY
    assert lights.last_color == YELLOW
    assert buzzer.last_tone == 1200

    # 4. Test page rotation
    np.rotateDisplayPage()
    assert "Status: Away" in display.lines[0]

    # 5. Test button navigation to previous employee
    btn_prev.press()
    assert np.getCurrentEmployee() == emp1
    assert "Dr. Alice" in display.lines[0]

    # Stop controller
    np.stop()
    assert lights.last_color == (0, 0, 0)

    Log.i("Testing complete - NamePlate.py checks passed successfully.")
