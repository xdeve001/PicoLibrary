"""
# Activity.py
# Represents a customer activity entity in the IoT CRM application.
# Holds activity attributes (id, activity_type, name, description, activity_date, owner, location)
# and provides formatting helpers for 16x2 LCD display.
# Author: xdeve001
"""

from Log import *


class Activity:
    """
    Data model representing a customer interaction or activity record.

    Parameters:
    ----------
    id : int, optional
        Unique identifier for the activity record (default: 0).
    activity_type : str, optional
        Category of activity, e.g., Meeting, Call, Email, Demo (default: "").
    name : str, optional
        Subject or brief title of the activity (default: "").
    description : str, optional
        Detailed description or summary of what occurred (default: "").
    activity_date : str, optional
        Timestamp or date string of the activity, e.g., '2026-11-20' (default: "").
    owner : str, optional
        Employee or representative responsible for the activity (default: "").
    location : str, optional
        Physical place, URL, or communication channel used (default: "").

    Examples:
    ---------
    1. act = Activity(301, "Meeting", "Q4 Review", "Discussed renewal", "2026-11-15", "Jane", "Zoom")
    2. act = Activity.from_json({"id": 302, "activity_type": "Call", "name": "Intro Call"})
    """

    def __init__(self, id=0, activity_type="", name="", description="",
                 activity_date="", owner="", location=""):
        self._id = int(id) if id is not None else 0
        self._activity_type = str(activity_type) if activity_type is not None else ""
        self._name = str(name) if name is not None else ""
        self._description = str(description) if description is not None else ""
        self._activity_date = str(activity_date) if activity_date is not None else ""
        self._owner = str(owner) if owner is not None else ""
        self._location = str(location) if location is not None else ""

    @property
    def id(self):
        """Get the unique activity ID."""
        return self._id

    @property
    def activity_type(self):
        """Get the activity type/category."""
        return self._activity_type

    @property
    def name(self):
        """Get the activity title or subject."""
        return self._name

    @property
    def description(self):
        """Get the detailed description."""
        return self._description

    @property
    def activity_date(self):
        """Get the activity date string."""
        return self._activity_date

    @property
    def owner(self):
        """Get the activity owner/representative."""
        return self._owner

    @property
    def location(self):
        """Get the activity location."""
        return self._location

    def format_line_1(self, index=None, total=None, max_len=16):
        """
        Format the first line of text for a 16-character LCD display.

        Parameters:
        ----------
        index : int, optional
            Current item index (1-based) to show position in list (default: None).
        total : int, optional
            Total count of activities (default: None).
        max_len : int, optional
            Maximum characters allowed (default: 16).

        Returns:
        -------
        str
            A 16-character formatted string for LCD row 0.

        Examples:
        ---------
        1. act.format_line_1(1, 2) -> "A[1/2] Q4 Review"
        """
        if index is not None and total is not None:
            prefix = f"A[{index}/{total}] "
            available = max_len - len(prefix)
            name_part = self._name[:available]
            return f"{prefix}{name_part}"[:max_len]
        return self._name[:max_len]

    def format_line_2(self, max_len=16):
        """
        Format the second line of text for a 16-character LCD display.
        Displays date and activity type compactly.

        Parameters:
        ----------
        max_len : int, optional
            Maximum characters allowed (default: 16).

        Returns:
        -------
        str
            A 16-character formatted string for LCD row 1.

        Examples:
        ---------
        1. act.format_line_2() -> "11-20 Call"
        """
        # Trim date to fit (e.g. '2026-11-20' -> '11-20' or '2026-11-20' if fits)
        dt = self._activity_date.strip()
        if len(dt) >= 10 and dt[4] == "-":
            dt_short = dt[5:]  # '11-20'
        else:
            dt_short = dt[:7]

        type_part = self._activity_type[:7].strip()
        if dt_short and type_part:
            line = f"{dt_short} {type_part}"
        elif dt_short:
            line = dt_short
        elif type_part:
            line = type_part
        else:
            line = self._owner[:max_len]
        return line[:max_len]

    @classmethod
    def from_json(cls, data):
        """
        Instantiate an Activity instance from a JSON dictionary response.

        Parameters:
        ----------
        data : dict
            Dictionary returned by REST API endpoint `/customer/get_activities/{id}`.

        Returns:
        -------
        Activity
            Initialized Activity instance.

        Examples:
        ---------
        1. act = Activity.from_json({"id": 1, "name": "Review", "activity_type": "Call"})
        """
        if not isinstance(data, dict):
            Log.e(f"Activity.from_json: expected dict, got {type(data).__name__}")
            return cls()

        return cls(
            id=data.get("id", 0),
            activity_type=data.get("activity_type") or data.get("type") or "",
            name=data.get("name") or data.get("subject") or "",
            description=data.get("description") or "",
            activity_date=data.get("activity_date") or data.get("date") or "",
            owner=data.get("owner") or "",
            location=data.get("location") or ""
        )

    def __repr__(self):
        return f"Activity(id={self._id}, type='{self._activity_type}', name='{self._name}', date='{self._activity_date}')"


if __name__ == "__main__":
    Log.i("Starting Activity verification...")

    # 1. Instantiate Activity with direct parameters
    a1 = Activity(
        id=301,
        activity_type="Meeting",
        name="Contract Review",
        description="Discussed service level agreement terms",
        activity_date="2026-11-20",
        owner="Alice",
        location="Zoom"
    )
    assert a1.id == 301, "ID mismatch"
    assert a1.activity_type == "Meeting", "Type mismatch"
    assert a1.name == "Contract Review", "Name mismatch"
    assert a1.description == "Discussed service level agreement terms", "Description mismatch"
    assert a1.activity_date == "2026-11-20", "Date mismatch"
    assert a1.owner == "Alice", "Owner mismatch"
    assert a1.location == "Zoom", "Location mismatch"

    # 2. Verify LCD line formatting
    l1 = a1.format_line_1(1, 3)
    l2 = a1.format_line_2()
    assert len(l1) <= 16, f"Line 1 length exceeded: {l1}"
    assert len(l2) <= 16, f"Line 2 length exceeded: {l2}"
    Log.i(f"LCD Line 1: '{l1}'")
    Log.i(f"LCD Line 2: '{l2}'")

    # 3. Test from_json parser
    json_data = {
        "id": 402,
        "activity_type": "Demo",
        "name": "Product Walkthrough",
        "description": "Showed new UI dashboard features",
        "activity_date": "2026-11-21",
        "owner": "Bob",
        "location": "HQ Room 4"
    }
    a2 = Activity.from_json(json_data)
    assert a2.id == 402
    assert a2.activity_type == "Demo"
    assert a2.name == "Product Walkthrough"
    assert a2.activity_date == "2026-11-21"

    # 4. Test empty JSON fallback
    a_empty = Activity.from_json(None)
    assert a_empty.id == 0
    assert a_empty.name == ""

    Log.i("Testing complete - all checks passed")

