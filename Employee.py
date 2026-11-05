"""
# Employee.py
# Object-Oriented hierarchy representing various employee types for a digital nameplate
# Includes Employee (base), Faculty, Staff, StudentWorker, and Administrator classes.
# Author: insert your name here
"""

from Log import *
from Calendar import Calendar


class Employee:
    """
    Base class representing an employee on the digital nameplate.

    Parameters:
    ----------
    name : str
        Full name of the employee
    title : str
        Job title or role
    department : str
        Department or academic unit
    email : str
        Contact email address
    phone : str
        Contact phone number
    availability : str, optional
        Initial availability status (default: "Available")

    Examples:
    ---------
    1. emp = Employee("Alex Smith", "Developer", "IT", "asmith@univ.edu", "555-1234")
       emp.getAvailability() # returns "Available"
       emp.cycleAvailability() # transitions to "Away"
    """

    STATUS_AVAILABLE = "Available"
    STATUS_AWAY = "Away"
    STATUS_BUSY = "Busy"

    def __init__(self, name, title, department, email, phone, availability=STATUS_AVAILABLE):
        """Initialize standard employee profile details."""
        self.name = name
        self.title = title
        self.department = department
        self.email = email
        self.phone = phone
        self.availability = availability
        Log.i(f"Employee created: {self.name} ({self.title}, {self.department})")

    def getAvailability(self):
        """
        Get the current availability status of the employee.

        Returns:
        -------
        str
            "Available", "Away", or "Busy"
        """
        return self.availability

    def setAvailability(self, status):
        """
        Set the employee availability status.

        Parameters:
        ----------
        status : str
            Target status value (STATUS_AVAILABLE, STATUS_AWAY, or STATUS_BUSY)
        """
        self.availability = status
        Log.i(f"Employee {self.name} availability set to: {self.availability}")

    def cycleAvailability(self):
        """
        Cycle availability status through the sequence: Available -> Away -> Busy -> Available.

        Returns:
        -------
        str
            The newly updated availability status.
        """
        if self.availability == Employee.STATUS_AVAILABLE:
            self.availability = Employee.STATUS_AWAY
        elif self.availability == Employee.STATUS_AWAY:
            self.availability = Employee.STATUS_BUSY
        else:
            self.availability = Employee.STATUS_AVAILABLE

        Log.i(f"Employee {self.name} availability cycled to: {self.availability}")
        return self.availability

    def getDisplayPages(self):
        """
        Generate pages of text tuples formatted for a 16x2 character LCD screen.

        Returns:
        -------
        list of tuple of (str, str)
            List of 2-line string tuples (line1, line2).
        """
        page0 = (self.name[:16], f"{self.title[:8]} {self.department[:7]}"[:16])
        page1 = (f"Status: {self.getAvailability()}"[:16], f"Em: {self.email}"[:16])
        page2 = (f"Ph: {self.phone}"[:16], f"Dept: {self.department}"[:16])
        return [page0, page1, page2]


class Faculty(Employee):
    """
    Represents a faculty member with teaching courses and office hours.

    Parameters:
    ----------
    name : str
        Full name of the faculty member
    title : str
        Academic title (e.g. Professor, Lecturer)
    department : str
        Academic department
    email : str
        Email address
    phone : str
        Phone number
    availability : str, optional
        Availability status (default: "Available")
    courses : list, optional
        List of course codes taught (default: None, initializes to empty list)
    officeHours : str, optional
        Office hours schedule string (default: "")

    Examples:
    ---------
    1. prof = Faculty("Dr. John", "Professor", "CS", "john@univ.edu", "555-0100", courses=["CS101", "CS201"], officeHours="MW 2-4PM")
       pages = prof.getDisplayPages()
    """

    def __init__(self, name, title, department, email, phone, availability=Employee.STATUS_AVAILABLE, courses=None, officeHours=""):
        super().__init__(name, title, department, email, phone, availability)
        self.courses = courses if courses is not None else []
        self.officeHours = officeHours
        Log.i(f"Faculty profile created: {self.name}, courses={self.courses}, officeHours='{self.officeHours}'")

    def getDisplayPages(self):
        """Generate LCD display pages including office hours and courses."""
        page0 = (self.name[:16], f"{self.title[:8]} {self.department[:7]}"[:16])
        page1 = (f"Status: {self.getAvailability()}"[:16], f"Em: {self.email}"[:16])
        course_str = ",".join(self.courses)
        page2 = (f"Office: {self.officeHours}"[:16], f"Courses: {course_str}"[:16])
        return [page0, page1, page2]


class Staff(Employee):
    """
    Represents a staff member with a defined work schedule.

    Parameters:
    ----------
    name : str
        Full name of the staff member
    title : str
        Staff title/position
    department : str
        Department/Unit
    email : str
        Email address
    phone : str
        Phone number
    availability : str, optional
        Availability status (default: "Available")
    workSchedule : str, optional
        Work schedule string (default: "")

    Examples:
    ---------
    1. staff = Staff("Jane Doe", "Advisor", "Engineering", "jane@univ.edu", "555-0102", workSchedule="8AM-5PM M-F")
    """

    def __init__(self, name, title, department, email, phone, availability=Employee.STATUS_AVAILABLE, workSchedule=""):
        super().__init__(name, title, department, email, phone, availability)
        self.workSchedule = workSchedule
        Log.i(f"Staff profile created: {self.name}, schedule='{self.workSchedule}'")

    def getDisplayPages(self):
        """Generate LCD display pages including work schedule."""
        page0 = (self.name[:16], f"{self.title[:8]} {self.department[:7]}"[:16])
        page1 = (f"Status: {self.getAvailability()}"[:16], f"Em: {self.email}"[:16])
        page2 = (f"Ph: {self.phone}"[:16], f"Sched: {self.workSchedule}"[:16])
        return [page0, page1, page2]


class StudentWorker(Staff):
    """
    Represents a student worker with specific shift hours, inheriting from Staff.

    Parameters:
    ----------
    name : str
        Full name of the student worker
    title : str
        Role/position title
    department : str
        Department where working
    email : str
        Email address
    phone : str
        Phone number
    availability : str, optional
        Availability status (default: "Available")
    shiftHours : str, optional
        Shift hours string (default: "")

    Examples:
    ---------
    1. sw = StudentWorker("Alex Lee", "Lab Assistant", "IT", "alee@univ.edu", "555-0103", shiftHours="Tue/Thu 1-5PM")
    """

    def __init__(self, name, title, department, email, phone, availability=Employee.STATUS_AVAILABLE, shiftHours=""):
        super().__init__(name, title, department, email, phone, availability, workSchedule=shiftHours)
        self.shiftHours = shiftHours
        Log.i(f"StudentWorker profile created: {self.name}, shift='{self.shiftHours}'")

    def getDisplayPages(self):
        """Generate LCD display pages including shift hours."""
        page0 = (self.name[:16], f"{self.title[:8]} {self.department[:7]}"[:16])
        page1 = (f"Status: {self.getAvailability()}"[:16], f"Em: {self.email}"[:16])
        page2 = (f"Shift: {self.shiftHours}"[:16], f"Ph: {self.phone}"[:16])
        return [page0, page1, page2]


class Administrator(Employee):
    """
    Represents an administrator whose availability is managed in coordination with a Calendar.

    Parameters:
    ----------
    name : str
        Full name of administrator
    title : str
        Administrative title
    department : str
        Administrative department
    email : str
        Email address
    phone : str
        Phone number
    availability : str, optional
        Base availability status (default: "Available")
    calendar : Calendar, optional
        Associated Calendar instance tracking scheduled meetings (default: None)

    Examples:
    ---------
    1. cal = Calendar([("10:00", "11:30")])
       admin = Administrator("Dr. Miller", "Dean", "Business", "miller@univ.edu", "555-0104", calendar=cal)
    """

    def __init__(self, name, title, department, email, phone, availability=Employee.STATUS_AVAILABLE, calendar=None):
        super().__init__(name, title, department, email, phone, availability)
        self._calendar = calendar
        Log.i(f"Administrator created: {self.name}, calendar linked: {self._calendar is not None}")

    def getAvailability(self):
        """
        Get availability, checking calendar meeting status if a calendar is linked.

        Returns:
        -------
        str
            "Busy" if currently in a scheduled meeting, otherwise base availability.
        """
        if self._calendar is not None:
            return self._calendar.checkAvailability()
        return self.availability

    def getDisplayPages(self):
        """Generate LCD display pages including calendar meeting info."""
        page0 = (self.name[:16], f"{self.title[:8]} {self.department[:7]}"[:16])
        page1 = (f"Status: {self.getAvailability()}"[:16], f"Em: {self.email}"[:16])
        cal_status = self._calendar.currentStatus if self._calendar else "None"
        page2 = (f"Ph: {self.phone}"[:16], f"Cal: {cal_status}"[:16])
        return [page0, page1, page2]


if __name__ == "__main__":
    Log.i("Starting self-test for Employee.py...")

    # 1. Base Employee test
    emp = Employee("Test Person", "Role", "Dept", "test@univ.edu", "555-0000")
    assert emp.getAvailability() == Employee.STATUS_AVAILABLE
    emp.cycleAvailability()
    assert emp.getAvailability() == Employee.STATUS_AWAY
    emp.cycleAvailability()
    assert emp.getAvailability() == Employee.STATUS_BUSY
    emp.cycleAvailability()
    assert emp.getAvailability() == Employee.STATUS_AVAILABLE

    # 2. Faculty test
    prof = Faculty("Dr. Turing", "Professor", "CS", "turing@univ.edu", "555-0101", courses=["CS100", "CS200"], officeHours="M/W 2-4PM")
    prof_pages = prof.getDisplayPages()
    assert len(prof_pages) == 3
    assert "Dr. Turing" in prof_pages[0][0]

    # 3. Staff test
    staff = Staff("Sara Connor", "Manager", "Operations", "sara@univ.edu", "555-0102", workSchedule="8AM-5PM")
    staff_pages = staff.getDisplayPages()
    assert len(staff_pages) == 3
    assert "Sara Connor" in staff_pages[0][0]

    # 4. StudentWorker test
    student = StudentWorker("Bob Smith", "Lab Tech", "Robotics", "bob@univ.edu", "555-0103", shiftHours="Fri 9AM-1PM")
    student_pages = student.getDisplayPages()
    assert len(student_pages) == 3
    assert "Bob Smith" in student_pages[0][0]

    # 5. Administrator with Calendar test
    cal = Calendar(meetingTimes=[("08:00", "12:00")], currentStatus="Available")
    admin = Administrator("Dr. Hopper", "Dean", "Computing", "hopper@univ.edu", "555-0104", calendar=cal)
    # Cal has meeting from 08:00 to 12:00; test checkAvailability
    assert cal.checkAvailability("09:00") == "Busy"
    assert cal.checkAvailability("13:00") == "Available"

    Log.i("Testing complete - Employee.py checks passed successfully.")
