"""
# FeedbackController.py
# StateModel controller for store customer feedback station.
# Coordinates ultrasonic sensor, buttons, display, buzzer, light strip, and FeedbackStats.
# Author: insert your name here
"""

import sys
import time

from Log import *
from StateModel import StateModel
from Counters import SoftwareTimer
from FeedbackStats import FeedbackStats

# Check hardware availability for MicroPython
try:
    from Displays import LCDDisplay
    from Buzzer import PassiveBuzzer
    from LightStrip import LightStrip
    from Button import Button
    from Sensors_advanced import UltrasonicSensor
    HARDWARE_AVAILABLE = True
except Exception as e:
    print("HARDWARE IMPORT ERROR:", e)
    HARDWARE_AVAILABLE = False
    LCDDisplay = None
    PassiveBuzzer = None
    LightStrip = None
    Button = None
    UltrasonicSensor = None


class SimDisplay:
    """Simulation fallback for 2-line LCD display."""

    def __init__(self):
        self.lines = ["", ""]

    def showText(self, text, row=0, col=0):
        if 0 <= row < len(self.lines):
            self.lines[row] = text
        if row == 1 or text == "Welcome to Ikea":
            Log.i(f"FeedbackController LCD: {self.lines}")

    def clear(self):
        self.lines = ["", ""]

    def reset(self):
        self.clear()


class SimBuzzer:
    """Simulation fallback for passive buzzer tones."""

    def __init__(self, name="buzzer"):
        self._name = name
        self._playing = False
        self.last_tone = None

    def play(self, tone=500):
        self._playing = True
        self.last_tone = tone
        Log.d(f"SimBuzzer: Playing tone {tone}Hz")

    def stop(self):
        self._playing = False
        Log.d("SimBuzzer: Tone stopped")

    def beep(self, tone=500, duration=150):
        self.play(tone)
        self.stop()


class SimLightStrip:
    """Simulation fallback for multi-LED light strip."""

    def __init__(self, name="StatusStrip", numleds=8):
        self._name = name
        self._numleds = numleds
        self.cur_color = None
        self.cur_level = 0

    def setColor(self, color, numPixels=None):
        self.cur_color = color
        self.cur_level = self._numleds if numPixels is None else numPixels
        Log.d(f"SimLightStrip: Set color {color} on {self.cur_level}/{self._numleds} LEDs")

    def off(self):
        self.cur_level = 0
        Log.d("SimLightStrip: Lights OFF")

    def on(self):
        self.cur_level = self._numleds
        Log.d("SimLightStrip: Lights ON")


class SimButton:
    """Simulation fallback for push button."""

    def __init__(self, pin=0, name="button", handler=None):
        self._pinNo = pin
        self._name = name
        self._handler = handler

    def setHandler(self, handler):
        self._handler = handler

    def press(self):
        if self._handler:
            self._handler.buttonPressed(self._name)

    def release(self):
        if self._handler:
            self._handler.buttonReleased(self._name)


class SimUltrasonicSensor:
    """Simulation fallback for ultrasonic distance sensor."""

    def __init__(self, name="uss", threshold=10.0):
        self._name = name
        self._threshold = threshold
        self._tripped = False
        self._handler = None

    def setHandler(self, handler):
        self._handler = handler

    def tripped(self):
        return self._tripped

    def trip(self):
        self._tripped = True
        if self._handler:
            self._handler.sensorTripped(self._name)

    def untrip(self):
        self._tripped = False
        if self._handler:
            self._handler.sensorUntripped(self._name)


class FeedbackController:
    """
    Controller implementation for a store customer feedback station using a StateModel.

    Coordinates customer interaction across 5 states:
    - **State 0 (Welcome)**: Customer greeting on LCD, idle outputs.
    - **State 1 (Selection)**: Prompts for rating, starts 5-second timeout.
    - **State 2 (Happy)**: Records happy rating, displays rating %, plays upbeat melody.
    - **State 3 (Unhappy)**: Records unhappy rating, plays sad tone; if satisfaction is
      below threshold, triggers transition to Alarm state.
    - **State 4 (Alarm)**: Calling manager alert, plays two-tone alarm in do-action,
      resets statistics on exit.

    Examples:
    ---------
    1. Basic controller initialization and run:
       ```python
       controller = FeedbackController()
       controller.run()
       ```
    2. Simulated event flow:
       ```python
       controller = FeedbackController(debug=True)
       controller.processEvent("uss_trip")     # Goes to Selection
       controller.processEvent("green_press")  # Records happy feedback
       controller.stop()
       ```
    """

    # State Constants
    STATE_WELCOME = 0
    STATE_SELECTION = 1
    STATE_HAPPY = 2
    STATE_UNHAPPY = 3
    STATE_ALARM = 4

    def __init__(self,
                 display=None,
                 buzzer=None,
                 lights=None,
                 uss=None,
                 green_button=None,
                 red_button=None,
                 manager_button=None,
                 timer=None,
                 stats=None,
                 satisfaction_threshold=30.0,
                 debug=True):
        """
        Initialize the FeedbackController, hardware peripherals, and StateModel transitions.

        Parameters:
        ----------
        display : LCDDisplay, optional
            LCD Display instance for textual output (default: LCDDisplay or SimDisplay)
        buzzer : PassiveBuzzer, optional
            Passive buzzer for auditory feedback (default: PassiveBuzzer or SimBuzzer)
        lights : LightStrip, optional
            NeoPixel light strip for visual level display (default: LightStrip or SimLightStrip)
        uss : UltrasonicSensor, optional
            Ultrasonic sensor for presence detection (default: UltrasonicSensor or SimUltrasonicSensor)
        green_button : Button, optional
            Button for positive feedback (default: Button pin 18 or SimButton 'green')
        red_button : Button, optional
            Button for negative feedback (default: Button pin 19 or SimButton 'red')
        timer : SoftwareTimer, optional
            Software timer for state timeouts (default: SoftwareTimer 'timer')
        stats : FeedbackStats, optional
            Business model instance tracking feedback metrics (default: FeedbackStats())
        satisfaction_threshold : float, optional
            Minimum satisfaction percentage before triggering manager alarm (default: 50.0)
        debug : bool, optional
            Enable verbose StateModel debug logging (default: True)

        Examples:
        ---------
        1. Initialize with simulation defaults:
           ```python
           controller = FeedbackController(debug=True)
           ```
        """
        Log.i("FeedbackController: Initializing feedback controller...")

        self.satisfaction_threshold = float(satisfaction_threshold)
        self.stats = stats if stats is not None else FeedbackStats()
        self._alarm_toggle = False

        # Initialize hardware components or simulation fallbacks
        if display is not None:
            self.display = display
        elif HARDWARE_AVAILABLE and LCDDisplay is not None:
            self.display = LCDDisplay(sda=0, scl=1)
        else:
            self.display = SimDisplay()

        if buzzer is not None:
            self.buzzer = buzzer
        elif HARDWARE_AVAILABLE and PassiveBuzzer is not None:
            self.buzzer = PassiveBuzzer(pin=16, name="buzzer")
        else:
            self.buzzer = SimBuzzer(name="buzzer")

        if lights is not None:
            self.lights = lights
        elif HARDWARE_AVAILABLE and LightStrip is not None:
            self.lights = LightStrip(pin=2, name="StatusStrip", numleds=8)
        else:
            self.lights = SimLightStrip(name="StatusStrip", numleds=8)

        if uss is not None:
            self.uss = uss
        elif HARDWARE_AVAILABLE and UltrasonicSensor is not None:
            self.uss = UltrasonicSensor(trigger=14, echo=15, name="uss")
        else:
            self.uss = SimUltrasonicSensor(name="uss")

        if green_button is not None:
            self.green_button = green_button
        elif HARDWARE_AVAILABLE and Button is not None:
            self.green_button = Button(11, name="green")
        else:
            self.green_button = SimButton(pin=11, name="green")

        if red_button is not None:
            self.red_button = red_button
        elif HARDWARE_AVAILABLE and Button is not None:
            self.red_button = Button(12, name="red")
        else:
            self.red_button = SimButton(pin=12, name="red")
        
        if manager_button is not None:
            self.manager_button = manager_button
        elif HARDWARE_AVAILABLE and Button is not None:
            self.manager_button = Button(20, name="manager")
        else:
            self.manager_button = SimButton(pin=20, name="manager")

        if timer is not None:
            self.timer = timer
        else:
            self.timer = SoftwareTimer(name="timer", handler=None)

        # Initialize StateModel with 5 states
        self._model = StateModel(5, self, debug=debug)

        # Register input peripherals with the StateModel
        self._model.addButton(self.green_button)
        self._model.addButton(self.red_button)
        self._model.addButton(self.manager_button)
        self._model.addSensor(self.uss)
        self._model.addTimer(self.timer)

        # Register custom transition events
        self._model.addCustomEvent("feedback_below_threshold")
        self._model.addCustomEvent("happy_press")

        # Define state transitions matching the UML state model
        # 0 - Welcome: Customer approaches -> 1 - Selection
        self._model.addTransition(self.STATE_WELCOME, ["uss_trip"], self.STATE_SELECTION)

        # 1 - Selection: green/happy -> 2, red -> 3, timeout -> 0
        self._model.addTransition(self.STATE_SELECTION, ["green_press", "happy_press"], self.STATE_HAPPY)
        self._model.addTransition(self.STATE_SELECTION, ["red_press"], self.STATE_UNHAPPY)
        self._model.addTransition(self.STATE_SELECTION, ["timer_timeout"], self.STATE_WELCOME)

        # 2 - Happy: timeout -> 0
        self._model.addTransition(self.STATE_HAPPY, ["timer_timeout"], self.STATE_WELCOME)
        self._model.addTransition(self.STATE_HAPPY, ["feedback_below_threshold"], self.STATE_ALARM)

        # 3 - Unhappy: below threshold -> 4 (Alarm), timeout -> 0
        self._model.addTransition(self.STATE_UNHAPPY, ["feedback_below_threshold"], self.STATE_ALARM)
        self._model.addTransition(self.STATE_UNHAPPY, ["timer_timeout"], self.STATE_WELCOME)

        # 4 - Alarm: manager reset on happy/green press -> 0
        self._model.addTransition(self.STATE_ALARM, ["manager_press"], self.STATE_WELCOME)

        Log.i("FeedbackController: Initialization complete with 5 states and transitions configured.")

    def run(self, delay=0.1):
        """
        Start the state model event loop.

        Parameters:
        ----------
        delay : float, optional
            Delay in seconds between loop iterations (default: 0.1)

        Examples:
        ---------
        1. Start running controller loop:
           ```python
           controller.run()
           ```
        """
        Log.i("FeedbackController: Starting controller...")
        self._model.run(delay=delay)

    def stop(self):
        """
        Stop the state model, cancel timers, and shut off outputs.

        Examples:
        ---------
        1. Safely stop the controller:
           ```python
           controller.stop()
           ```
        """
        Log.i("FeedbackController: Stopping controller...")
        self._model.stop()
        if self.timer:
            self.timer.cancel()
        if self.buzzer:
            self.buzzer.stop()
        if self.lights:
            self.lights.off()

    def processEvent(self, event):
        """
        Process an event directly through the internal StateModel.

        Parameters:
        ----------
        event : str
            Event identifier string (e.g. 'uss_trip', 'green_press', 'timer_timeout')

        Examples:
        ---------
        1. Manually trigger a customer approach event:
           ```python
           controller.processEvent("uss_trip")
           ```
        """
        self._model.processEvent(event)

    def stateEntered(self, state, event):
        """
        StateModel callback executing state entry actions.

        Parameters:
        ----------
        state : int
            The state number just entered (0 to 4)
        event : str
            The event string that caused the transition

        Examples:
        ---------
        Automatically invoked by the StateModel during state transitions.
        """
        Log.d(f"FeedbackController: stateEntered -> State {state} on event '{event}'")

        if state == self.STATE_WELCOME:
            # 0 - Welcome: entry / display 'Welcome to Ikea'
            self.show_lcd("Welcome to Ikea", "")
            if self.lights:
                self.lights.off()
            if self.buzzer:
                self.buzzer.stop()

        elif state == self.STATE_SELECTION:
            # 1 - Selection: entry / display 'How was your visit?'; start a 5 sec timer
            self.show_lcd("How was your", "visit?")
            self.timer.start(5)

        elif state == self.STATE_HAPPY:
            self.stats.add_happy()
            pct = self.stats.calculate_percentage()
            self.show_lcd("Thank you!", f"Rating: {pct:.0f}%")
            self.update_lights()
            self.play_happy_music()

            if pct < self.satisfaction_threshold:
                Log.i(f"Satisfaction {pct:.1f}% is below threshold. Triggering Alarm!")
                self._model.processEvent("feedback_below_threshold")
            else:
                self.timer.start(5)

        elif state == self.STATE_UNHAPPY:
            # 3 - unhappy
            self.stats.add_unhappy()
            self.update_lights()
            self.play_sad_tone()

            pct = self.stats.calculate_percentage()
            self.show_lcd("Sorry to hear", f"Rating: {pct:.0f}%")

            if pct < self.satisfaction_threshold:
                Log.i(f"FeedbackController: Satisfaction {pct:.1f}% is below threshold {self.satisfaction_threshold}%. Triggering Alarm!")
                self._model.processEvent("feedback_below_threshold")
            else:
                self.timer.start(5)

        elif state == self.STATE_ALARM:
            # 4 - Alarm: entry / display 'Calling manager'
            self.show_lcd("Calling manager", "Please wait...")
            if self.lights and hasattr(self.lights, 'setColor'):
                try:
                    from Lights import RED
                    self.lights.setColor(RED)
                except (ImportError, Exception):
                    self.lights.setColor((255, 0, 0))

    def stateLeft(self, state, event):
        """
        StateModel callback executing state exit actions.

        Parameters:
        ----------
        state : int
            The state number being left (0 to 4)
        event : str
            The event string that caused the transition

        Examples:
        ---------
        Automatically invoked by the StateModel during state transitions.
        """
        Log.d(f"FeedbackController: stateLeft -> State {state} on event '{event}'")

        if state in (self.STATE_SELECTION, self.STATE_HAPPY, self.STATE_UNHAPPY):
            self.timer.cancel()
            if self.buzzer:
                self.buzzer.stop()

        elif state == self.STATE_ALARM:
            # 4 - Alarm: exit / reset stats
            if self.buzzer:
                self.buzzer.stop()
            Log.i("FeedbackController: Exiting Alarm state -> resetting statistics")
            self.stats.reset()
            if self.lights:
                self.lights.off()

    def stateDo(self, state):
        """
        StateModel callback executing ongoing activities for the active state.

        Parameters:
        ----------
        state : int
            The current active state number (0 to 4)

        Examples:
        ---------
        Automatically invoked by StateModel.run() on each iteration.
        """
        if state == self.STATE_ALARM:
            # 4 - Alarm: do / play a 2 tone alarm
            self.play_two_tone_alarm()

    def stateEvent(self, state, event) -> bool:
        """
        StateModel callback handling in-state events without transitioning.

        Parameters:
        ----------
        state : int
            The current active state number
        event : str
            The event name received

        Returns:
        -------
        bool
            True if handled, False otherwise.
        """
        return False

    def show_lcd(self, line1, line2=""):
        """
        Update the 2-line LCD display text.

        Parameters:
        ----------
        line1 : str
            Text string for line 0
        line2 : str, optional
            Text string for line 1 (default: "")

        Examples:
        ---------
        1. Update display greeting:
           ```python
           controller.show_lcd("Welcome to Ikea", "")
           ```
        """
        if self.display:
            self.display.clear()
            self.display.showText(line1, row=0, col=0)
            self.display.showText(line2, row=1, col=0)

    def update_lights(self):
        """
        Update the light strip based on current satisfaction percentage and light level.

        Examples:
        ---------
        1. Refresh light strip LEDs:
           ```python
           controller.update_lights()
           ```
        """
        if not self.lights:
            return

        num_leds = getattr(self.lights, '_numleds', 8)
        level = self.stats.get_light_level(max_levels=num_leds)
        pct = self.stats.calculate_percentage()

        try:
            from Lights import GREEN, YELLOW, RED
        except (ImportError, Exception):
            GREEN = (0, 255, 0)
            YELLOW = (255, 255, 0)
            RED = (255, 0, 0)

        color = GREEN if pct >= 70.0 else YELLOW if pct >= 50.0 else RED
        if hasattr(self.lights, 'setColor'):
            self.lights.setColor(color, level)

    def play_happy_music(self):
        """
        Play an uplifting multi-tone chime on the passive buzzer.

        Examples:
        ---------
        1. Play happy confirmation chime:
           ```python
           controller.play_happy_music()
           ```
        """
        if not self.buzzer:
            return

        try:
            from Buzzer import DO, MI, SO, DO2
            notes = [DO, MI, SO, DO2]
        except (ImportError, Exception):
            notes = [523, 659, 784, 1047]

        for note in notes:
            self.buzzer.play(note)
            time.sleep(0.08)
        self.buzzer.stop()

    def play_sad_tone(self):
        """
        Play a descending tone on the passive buzzer.

        Examples:
        ---------
        1. Play sad acknowledgment tone:
           ```python
           controller.play_sad_tone()
           ```
        """
        if not self.buzzer:
            return

        try:
            from Buzzer import SO, MI, DO
            notes = [SO, MI, DO]
        except (ImportError, Exception):
            notes = [392, 330, 262]

        for note in notes:
            self.buzzer.play(note)
            time.sleep(0.12)
        self.buzzer.stop()

    def play_two_tone_alarm(self):
        """
        Play an alternating two-tone alarm signal on the passive buzzer.

        Examples:
        ---------
        1. Play one cycle of alarm sound:
           ```python
           controller.play_two_tone_alarm()
           ```
        """
        if not self.buzzer:
            return

        tone = 880 if self._alarm_toggle else 587
        self._alarm_toggle = not self._alarm_toggle
        self.buzzer.play(tone)
        time.sleep(0.15)
        self.buzzer.stop()


if __name__ == "__main__":
    Log.i("Running self-contained verification tests for FeedbackController...")

    # Initialize controller in simulation mode
    controller = FeedbackController(debug=True, satisfaction_threshold=30.0)
    controller._model.start()

    # 1. Verify initial State 0 (Welcome)
    assert controller._model._curState == FeedbackController.STATE_WELCOME
    assert controller.display.lines == ["Welcome to Ikea", ""]
    Log.i("Test 1 Passed: Initialized in State 0 (Welcome).")

    # 2. Simulate customer approaching (uss_trip -> State 1 Selection)
    controller.processEvent("uss_trip")
    assert controller._model._curState == FeedbackController.STATE_SELECTION
    assert controller.display.lines == ["How was your", "visit?"]
    assert controller.timer._started is True
    Log.i("Test 2 Passed: Transition to State 1 (Selection) on uss_trip verified.")

    # 3. Customer presses green button (green_press -> State 2 Happy)
    controller.processEvent("green_press")
    assert controller._model._curState == FeedbackController.STATE_HAPPY
    assert controller.stats.happy_count == 1
    assert controller.stats.unhappy_count == 0
    assert controller.display.lines == ["Thank you!", "Rating: 100%"]
    Log.i("Test 3 Passed: Transition to State 2 (happy) and stat recording verified.")

    # 4. 5-second timer expires -> State 0 (Welcome)
    controller.processEvent("timer_timeout")
    assert controller._model._curState == FeedbackController.STATE_WELCOME
    assert controller.display.lines == ["Welcome to Ikea", ""]
    Log.i("Test 4 Passed: Timeout from State 2 returns to State 0 (Welcome).")

    # 5. Customer 2 approaches and presses red (uss_trip -> State 1 -> red_press -> State 3 Unhappy)
    controller.processEvent("uss_trip")
    assert controller._model._curState == FeedbackController.STATE_SELECTION
    controller.processEvent("red_press")
    assert controller._model._curState == FeedbackController.STATE_UNHAPPY
    assert controller.stats.happy_count == 1
    assert controller.stats.unhappy_count == 1
    assert controller.stats.calculate_percentage() == 50.0
    assert controller.display.lines == ["Sorry to hear", "that"]
    Log.i("Test 5 Passed: Transition to State 3 (unhappy) at 50% satisfaction verified.")

    # 6. Timeout returns to State 0
    controller.processEvent("timer_timeout")
    assert controller._model._curState == FeedbackController.STATE_WELCOME
    assert controller.display.lines == ["Welcome to Ikea", ""]
    Log.i("Test 6 Passed: Timeout from State 3 returns to State 0 (Welcome).")

    # 7. Customer 3 approaches and presses red (33.3% satisfaction)
    controller.processEvent("uss_trip")
    controller.processEvent("red_press")

    # Satisfaction is 33.3%, above the 30% threshold
    assert controller._model._curState == FeedbackController.STATE_UNHAPPY
    Log.i("Test 7 Passed: 33.3% satisfaction does not trigger Alarm.")

    # Customer 3 timeout returns to Welcome
    controller.processEvent("timer_timeout")

    # 8. Customer 4 approaches and presses red (25% satisfaction)
    controller.processEvent("uss_trip")
    controller.processEvent("red_press")

    # Satisfaction is 25%, below the 30% threshold
    assert controller._model._curState == FeedbackController.STATE_ALARM
    assert controller.display.lines == ["Calling manager", "Please wait..."]
    Log.i("Test 8 Passed: 25% satisfaction triggers Alarm.")

    # 9. Manager arrives and presses green button -> resets stats and returns to State 0
    controller.processEvent("manager_press")
    assert controller._model._curState == FeedbackController.STATE_WELCOME
    assert controller.stats.happy_count == 0
    assert controller.stats.unhappy_count == 0
    assert controller.display.lines == ["Welcome to Ikea", ""]
    Log.i("Test 9 Passed: Manager acknowledgment resets stats and returns to State 0.")

    # Stop controller cleanly
    controller.stop()
    assert controller._model._running is False
    Log.i("Testing complete - all checks passed")


