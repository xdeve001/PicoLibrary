"""
# main.py
# Main entrypoint script for the Digital Employee NamePlate application on Raspberry Pi Pico.
# Initializes the LCD display, buttons, passive buzzer, NeoPixel light strip, and starts NamePlate.
# Author: insert your name here
"""

import time
from Log import *
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
from Calendar import Calendar
from Employee import Employee, Faculty, Staff, StudentWorker, Administrator
from NamePlate import NamePlate


def create_sample_employees():
    """
    Instantiate diverse employee profiles representing Faculty, Staff,
    StudentWorker, and an Administrator with a linked Calendar.

    Returns:
    -------
    list of Employee
        List of initialized employee instances.
    """
    Log.i("main: Creating employee profiles...")

    # 1. Faculty Member
    faculty = Faculty(
        name="Dr. Ada Lovelace",
        title="Professor",
        department="CompSci",
        email="ada@univ.edu",
        phone="555-0101",
        availability=Employee.STATUS_AVAILABLE,
        courses=["CS101", "CS201"],
        officeHours="Mon/Wed 2-4PM"
    )

    # 2. Staff Member
    staff = Staff(
        name="Grace Hopper",
        title="Coordinator",
        department="IT Serv",
        email="grace@univ.edu",
        phone="555-0102",
        availability=Employee.STATUS_AVAILABLE,
        workSchedule="8AM-4:30PM M-F"
    )

    # 3. Student Worker
    student = StudentWorker(
        name="Alan Turing",
        title="Helpdesk",
        department="IT Supp",
        email="alan@univ.edu",
        phone="555-0103",
        availability=Employee.STATUS_AVAILABLE,
        shiftHours="Tue/Thu 1-5PM"
    )

    # 4. Administrator linked with scheduled Calendar
    # Define scheduled meeting windows: 09:00-11:00 and 14:00-15:30
    meetings = [("09:00", "11:00"), ("14:00", "15:30")]
    calendar = Calendar(meetingTimes=meetings, currentStatus="Available")
    admin = Administrator(
        name="Dr. K. Johnson",
        title="Dean",
        department="Sciences",
        email="kjohnson@u.edu",
        phone="555-0100",
        availability=Employee.STATUS_AVAILABLE,
        calendar=calendar
    )

    return [faculty, staff, student, admin]


def main():
    """
    Main function to initialize hardware components, configure employees,
    instantiate the NamePlate controller, and start the application loop.
    """
    Log.i("main: Initializing Employee NamePlate hardware components...")

    if not HARDWARE_AVAILABLE:
        Log.w("main: MicroPython hardware modules ('machine') not detected. Running simulation mode.")

        class SimDisplay:
            def showText(self, text, row=0, col=0):
                Log.i(f"[LCD Line {row}] {text}")
            def clear(self):
                Log.d("[LCD] Screen cleared")

        class SimBuzzer:
            def beep(self, tone=500, duration=150):
                Log.i(f"[Buzzer] Beep at {tone}Hz for {duration}ms")
            def stop(self):
                pass

        class SimLightStrip:
            def setColor(self, color, numPixels=None):
                Log.i(f"[LightStrip] Status LED color set to: {color}")
            def off(self):
                Log.i("[LightStrip] Lights OFF")

        class SimButton:
            def __init__(self, name):
                self._name = name
                self._handler = None
            def setHandler(self, handler):
                self._handler = handler
            def press(self):
                if self._handler:
                    self._handler.buttonPressed(self._name)

        display = SimDisplay()
        buzzer = SimBuzzer()
        light_strip = SimLightStrip()
        btn_prev = SimButton("btn_prev")
        btn_next = SimButton("btn_next")
        btn_status = SimButton("btn_status")
        buttons = [btn_prev, btn_next, btn_status]

        employees = create_sample_employees()
        nameplate = NamePlate(
            employees=employees,
            display=display,
            buttons=buttons,
            buzzer=buzzer,
            lightStrip=light_strip,
            pageInterval=1
        )

        Log.i("main: Simulating user interactions...")
        # 1. Next employee
        btn_next.press()
        # 2. Rotate page
        nameplate.rotateDisplayPage()
        # 3. Cycle availability
        btn_status.press()
        # 4. Next employee
        btn_next.press()
        # 5. Previous employee
        btn_prev.press()
        nameplate.stop()
        Log.i("main: Simulation complete - NamePlate functional verification passed.")
        return

    # 1. LCD Display initialization (I2C on GP0/GP1 with fallback to GPIO)
    try:
        display = LCDDisplay(sda=0, scl=1)
    except Exception as e:
        Log.w(f"main: I2C LCD initialization failed ({e}), attempting GPIO pin fallback...")
        try:
            display = LCDDisplay()
        except Exception as e2:
            Log.e(f"main: Failed to initialize LCDDisplay: {e2}")
            display = None

    # 2. Passive Buzzer on GP15
    try:
        buzzer = PassiveBuzzer(pin=15, name="NamePlateBuzzer")
    except Exception as e:
        Log.w(f"main: Failed to initialize PassiveBuzzer on GP15 ({e}), continuing without buzzer...")
        buzzer = None

    # 3. 16-LED NeoPixel Light Strip on GP2
    try:
        light_strip = LightStrip(pin=2, name="StatusStrip", numleds=16)
    except Exception as e:
        Log.w(f"main: Failed to initialize LightStrip on GP2 ({e}), continuing without light strip...")
        light_strip = None

    # 4. Three control Buttons:
    #    GP10 -> Previous Employee
    #    GP11 -> Next Employee
    #    GP12 -> Cycle Availability Status
    try:
        btn_prev = Button(pin=10, name="btn_prev", lowActive=True)
        btn_next = Button(pin=11, name="btn_next", lowActive=True)
        btn_status = Button(pin=12, name="btn_status", lowActive=True)
        buttons = [btn_prev, btn_next, btn_status]
    except Exception as e:
        Log.w(f"main: Failed to initialize Buttons ({e}), continuing with mock/empty buttons...")
        buttons = []

    # 5. Create employee profiles
    employees = create_sample_employees()

    # 6. Instantiate the NamePlate Controller
    Log.i("main: Launching NamePlate application...")
    nameplate = NamePlate(
        employees=employees,
        display=display,
        buttons=buttons,
        buzzer=buzzer,
        lightStrip=light_strip,
        pageInterval=3
    )

    try:
        # Run the application loop (rotates pages, responds to interrupts)
        nameplate.run()
    except KeyboardInterrupt:
        Log.i("main: Application interrupted by user.")
    finally:
        nameplate.stop()
        Log.i("main: NamePlate application shutdown complete.")


if __name__ == "__main__":
    main()
