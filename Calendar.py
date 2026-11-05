"""
# Calendar.py
# Implementation of a Calendar class to track scheduled meetings and determine availability
# Author: insert your name here
"""

import time
from Log import *


class Calendar:
    """
    A Calendar tracking scheduled meetings and current availability status.
    Used by Administrator employees to dynamically compute availability based on scheduled times.

    Parameters:
    ----------
    meetingTimes : list, optional
        A list of meeting intervals as tuples (e.g. [("09:00", "10:30"), ("14:00", "15:00")])
        or minute integers (default: None, initializes to empty list)
    currentStatus : str, optional
        Default base status when no meeting is scheduled (default: "Available")

    Examples:
    ---------
    1. cal = Calendar(meetingTimes=[("09:00", "10:30"), ("14:00", "15:00")])
       cal.isInMeeting("09:15") # returns True
       cal.checkAvailability("09:15") # returns "Busy"
    2. cal.isInMeeting("11:00") # returns False
       cal.checkAvailability("11:00") # returns "Available"
    """

    def __init__(self, meetingTimes=None, currentStatus="Available"):
        """
        Initialize the Calendar instance with scheduled meeting intervals and default status.

        Parameters:
        ----------
        meetingTimes : list, optional
            List of meeting time intervals (start, end)
        currentStatus : str, optional
            Base availability status when not in a meeting
        """
        self.meetingTimes = meetingTimes if meetingTimes is not None else []
        self.currentStatus = currentStatus
        Log.i(f"Calendar initialized with {len(self.meetingTimes)} scheduled meetings, default status='{self.currentStatus}'")

    def isInMeeting(self, currentTime=None):
        """
        Check whether a specific time (or current device time) falls within any meeting window.

        Parameters:
        ----------
        currentTime : str or int, optional
            Time string (e.g. "09:30") or integer to compare. If None, device local time is used.

        Returns:
        -------
        bool
            True if currentTime is inside any scheduled meeting interval, False otherwise.
        """
        if not self.meetingTimes:
            return False

        if currentTime is None:
            try:
                t = time.localtime()
                currentTime = f"{t[3]:02d}:{t[4]:02d}"
            except Exception:
                currentTime = "10:00"

        for start, end in self.meetingTimes:
            if start <= currentTime < end:
                Log.d(f"Calendar: currentTime '{currentTime}' falls within meeting ({start} - {end})")
                return True

        return False

    def checkAvailability(self, currentTime=None):
        """
        Determine availability status based on meeting schedule.

        Parameters:
        ----------
        currentTime : str or int, optional
            Time string (e.g. "09:30") to evaluate. If None, device time is checked.

        Returns:
        -------
        str
            "Busy" if currently in a meeting, otherwise returns currentStatus.
        """
        if self.isInMeeting(currentTime):
            return "Busy"
        return self.currentStatus


if __name__ == "__main__":
    Log.i("Starting self-test for Calendar.py...")

    # Instantiate calendar with scheduled meeting windows
    meetings = [("09:00", "10:30"), ("14:00", "15:30")]
    cal = Calendar(meetingTimes=meetings, currentStatus="Available")

    # Verification: during a meeting window
    in_meeting_status = cal.isInMeeting("09:30")
    avail_status = cal.checkAvailability("09:30")
    Log.i(f"At 09:30 - in meeting: {in_meeting_status}, availability: {avail_status}")
    assert in_meeting_status is True, "Expected to be in meeting at 09:30"
    assert avail_status == "Busy", "Expected 'Busy' during meeting"

    # Verification: outside meeting windows
    outside_status = cal.isInMeeting("11:00")
    avail_outside = cal.checkAvailability("11:00")
    Log.i(f"At 11:00 - in meeting: {outside_status}, availability: {avail_outside}")
    assert outside_status is False, "Expected not to be in meeting at 11:00"
    assert avail_outside == "Available", "Expected 'Available' outside meeting"

    Log.i("Testing complete - Calendar.py checks passed successfully.")
