"""
# FeedbackStats.py
# Implementation of FeedbackStats to track customer feedback counts (happy and unhappy),
# calculate feedback statistics, satisfaction percentages, and map levels to a light strip.
# Author: insert your name here
"""

from Log import *


class FeedbackStats:
    """
    A statistics tracking model for a customer feedback station.

    Tracks **happy** and **unhappy** customer feedback responses, provides total counts,
    computes satisfaction percentages, and maps current satisfaction scores to a light
    strip display level.

    Examples:
    ---------
    1. Create an instance and record feedback:
       ```python
       stats = FeedbackStats()
       stats.add_happy()
       stats.add_unhappy()
       total = stats.get_total_count()  # returns 2
       pct = stats.calculate_percentage()  # returns 50.0
       level = stats.get_light_level(8)  # returns 4
       ```
    2. Reset statistics at the end of a business day:
       ```python
       stats.reset()
       assert stats.get_total_count() == 0
       ```
    """

    def __init__(self, happy_count=0, unhappy_count=0):
        """
        Initialize the FeedbackStats model with initial counts.

        Parameters:
        ----------
        happy_count : int, optional
            Initial count of happy responses (default: 0)
        unhappy_count : int, optional
            Initial count of unhappy responses (default: 0)

        Examples:
        ---------
        1. Default initialization:
           ```python
           stats = FeedbackStats()
           ```
        2. Initialization with starting counts:
           ```python
           stats = FeedbackStats(happy_count=10, unhappy_count=2)
           ```
        """
        self._happy_count = max(0, int(happy_count))
        self._unhappy_count = max(0, int(unhappy_count))
        Log.i(f"FeedbackStats: Initialized with happy={self._happy_count}, unhappy={self._unhappy_count}")

    @property
    def happy_count(self) -> int:
        """
        Read-only property returning the current happy feedback count.

        Returns:
        -------
        int
            Number of recorded happy feedbacks.
        """
        return self._happy_count

    @property
    def unhappy_count(self) -> int:
        """
        Read-only property returning the current unhappy feedback count.

        Returns:
        -------
        int
            Number of recorded unhappy feedbacks.
        """
        return self._unhappy_count

    def add_happy(self, count=1):
        """
        Record one or more **happy** feedback responses.

        Increments the private `_happy_count` attribute and logs the update.

        Parameters:
        ----------
        count : int, optional
            Number of happy responses to add (default: 1)

        Examples:
        ---------
        1. Add a single happy vote:
           ```python
           stats.add_happy()
           ```
        2. Add multiple happy votes:
           ```python
           stats.add_happy(5)
           ```
        """
        if count > 0:
            self._happy_count += int(count)
            Log.i(f"FeedbackStats: Recorded +{count} happy feedback (Happy: {self._happy_count}, Total: {self.get_total_count()})")

    def add_unhappy(self, count=1):
        """
        Record one or more **unhappy** feedback responses.

        Increments the private `_unhappy_count` attribute and logs the update.

        Parameters:
        ----------
        count : int, optional
            Number of unhappy responses to add (default: 1)

        Examples:
        ---------
        1. Add a single unhappy vote:
           ```python
           stats.add_unhappy()
           ```
        2. Add multiple unhappy votes:
           ```python
           stats.add_unhappy(3)
           ```
        """
        if count > 0:
            self._unhappy_count += int(count)
            Log.i(f"FeedbackStats: Recorded +{count} unhappy feedback (Unhappy: {self._unhappy_count}, Total: {self.get_total_count()})")

    def get_total_count(self) -> int:
        """
        Calculate and return the **total** number of feedback responses received.

        Returns:
        -------
        int
            Sum of `_happy_count` and `_unhappy_count`.

        Examples:
        ---------
        1. Retrieve total feedback count:
           ```python
           total = stats.get_total_count()
           ```
        """
        return self._happy_count + self._unhappy_count

    def calculate_percentage(self, happy=True) -> float:
        """
        Calculate the feedback satisfaction percentage.

        By default, computes the percentage of **happy** feedback relative to
        total responses. If `happy=False` is passed, computes the percentage of
        unhappy feedback. If no feedback has been recorded, returns `0.0`.

        Parameters:
        ----------
        happy : bool, optional
            If True, calculates percentage of happy feedback; if False, calculates
            unhappy feedback (default: True)

        Returns:
        -------
        float
            Percentage value between 0.0 and 100.0.

        Examples:
        ---------
        1. Calculate customer satisfaction percentage (happy ratio):
           ```python
           sat_pct = stats.calculate_percentage()
           ```
        2. Calculate dissatisfaction percentage (unhappy ratio):
           ```python
           unsat_pct = stats.calculate_percentage(happy=False)
           ```
        """
        total = self.get_total_count()
        if total == 0:
            return 0.0

        target_count = self._happy_count if happy else self._unhappy_count
        return (target_count / total) * 100.0

    def get_light_level(self, max_levels=8) -> int:
        """
        Map the current customer satisfaction percentage to an indicator level
        for a multi-LED LightStrip.

        Calculates the number of active light levels or LEDs based on the
        happiness percentage. If no feedback has been submitted, returns 0.

        Parameters:
        ----------
        max_levels : int, optional
            The total number of levels or LEDs available on the light strip (default: 8)

        Returns:
        -------
        int
            The number of levels/LEDs to activate (integer from 0 to max_levels).

        Examples:
        ---------
        1. Get light level on standard 8-LED NeoPixel strip:
           ```python
           level = stats.get_light_level()  # uses default max_levels=8
           ```
        2. Get light level for a 16-LED NeoPixel strip:
           ```python
           level = stats.get_light_level(16)
           ```
        """
        if max_levels <= 0:
            return 0

        total = self.get_total_count()
        if total == 0:
            return 0

        percentage = self.calculate_percentage(happy=True)
        # Scale percentage (0-100) to strip level (0-max_levels)
        calculated_level = round((percentage / 100.0) * max_levels)
        return max(0, min(max_levels, int(calculated_level)))

    def reset(self):
        """
        Reset all feedback counts back to zero.

        Examples:
        ---------
        1. Reset statistics:
           ```python
           stats.reset()
           ```
        """
        Log.i("FeedbackStats: Resetting feedback counts")
        self._happy_count = 0
        self._unhappy_count = 0

    def __str__(self) -> str:
        """
        Return a human-readable string summary of the current statistics.

        Returns:
        -------
        str
            Summary containing happy count, unhappy count, total, and satisfaction percentage.
        """
        total = self.get_total_count()
        pct = self.calculate_percentage()
        return f"FeedbackStats(Happy: {self._happy_count}, Unhappy: {self._unhappy_count}, Total: {total}, Satisfaction: {pct:.1f}%)"

    def __repr__(self) -> str:
        """
        Return an unambiguous string representation of the instance.

        Returns:
        -------
        str
            Object representation with current attribute counts.
        """
        return f"FeedbackStats(happy_count={self._happy_count}, unhappy_count={self._unhappy_count})"


if __name__ == "__main__":
    Log.i("Running self-contained verification tests for FeedbackStats...")

    # 1. Verification of default initialization
    stats = FeedbackStats()
    assert stats.happy_count == 0, f"Expected 0 happy, got {stats.happy_count}"
    assert stats.unhappy_count == 0, f"Expected 0 unhappy, got {stats.unhappy_count}"
    assert stats.get_total_count() == 0, f"Expected 0 total, got {stats.get_total_count()}"
    assert stats.calculate_percentage() == 0.0, f"Expected 0.0%, got {stats.calculate_percentage()}"
    assert stats.get_light_level() == 0, f"Expected light level 0, got {stats.get_light_level()}"
    Log.i("Test 1 Passed: Default initialization verified.")

    # 2. Verification of adding happy feedback
    stats.add_happy()
    assert stats.happy_count == 1
    assert stats.unhappy_count == 0
    assert stats.get_total_count() == 1
    assert stats.calculate_percentage() == 100.0
    assert stats.get_light_level(8) == 8
    Log.i(f"Test 2 Passed: Single happy added -> {stats}")

    # 3. Verification of adding unhappy feedback
    stats.add_unhappy()
    assert stats.happy_count == 1
    assert stats.unhappy_count == 1
    assert stats.get_total_count() == 2
    assert stats.calculate_percentage() == 50.0
    assert stats.calculate_percentage(happy=False) == 50.0
    assert stats.get_light_level(8) == 4
    Log.i(f"Test 3 Passed: Unhappy added -> 50% split -> {stats}")

    # 4. Verification with more counts (3 happy, 1 unhappy -> 75%)
    stats.add_happy(2)
    assert stats.happy_count == 3
    assert stats.unhappy_count == 1
    assert stats.get_total_count() == 4
    assert stats.calculate_percentage() == 75.0
    assert stats.calculate_percentage(happy=False) == 25.0
    assert stats.get_light_level(8) == 6  # 75% of 8 = 6
    assert stats.get_light_level(16) == 12  # 75% of 16 = 12
    Log.i(f"Test 4 Passed: 75% satisfaction verified -> light level: {stats.get_light_level(8)}")

    # 5. Verification of reset
    stats.reset()
    assert stats.happy_count == 0
    assert stats.unhappy_count == 0
    assert stats.get_total_count() == 0
    assert stats.calculate_percentage() == 0.0
    assert stats.get_light_level() == 0
    Log.i("Test 5 Passed: Reset verified successfully.")

    Log.i("Testing complete - all checks passed")
