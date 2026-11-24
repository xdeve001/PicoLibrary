"""
# Contact.py
# Represents a customer contact entity in the IoT CRM application.
# Holds contact attributes (id, name, title, company, phone, contact_type)
# and provides formatting helpers for 16x2 LCD display.
# Author: xdeve001
"""

from Log import *


class Contact:
    """
    Data model representing an individual customer contact.

    Parameters:
    ----------
    id : int, optional
        Unique identifier for the contact (default: 0).
    name : str, optional
        Full name of the contact person (default: "").
    title : str, optional
        Professional job title (default: "").
    company : str, optional
        Company or organization name (default: "").
    phone : str, optional
        Contact telephone number (default: "").
    contact_type : str, optional
        Classification or role of the contact, e.g., Primary, Billing (default: "").

    Examples:
    ---------
    1. contact = Contact(101, "Alice Smith", "VP Sales", "Acme Corp", "555-0199", "Primary")
    2. contact = Contact.from_json({"id": 102, "name": "Bob Jones", "phone": "555-0122"})
    """

    def __init__(self, id=0, name="", title="", company="", phone="", contact_type=""):
        self._id = int(id) if id is not None else 0
        self._name = str(name) if name is not None else ""
        self._title = str(title) if title is not None else ""
        self._company = str(company) if company is not None else ""
        self._phone = str(phone) if phone is not None else ""
        self._contact_type = str(contact_type) if contact_type is not None else ""

    @property
    def id(self):
        """Get the unique contact ID."""
        return self._id

    @property
    def name(self):
        """Get the contact's full name."""
        return self._name

    @property
    def title(self):
        """Get the contact's title."""
        return self._title

    @property
    def company(self):
        """Get the company name."""
        return self._company

    @property
    def phone(self):
        """Get the contact's phone number."""
        return self._phone

    @property
    def contact_type(self):
        """Get the contact classification type."""
        return self._contact_type

    def format_line_1(self, index=None, total=None, max_len=16):
        """
        Format the first line of text for a 16-character LCD display.

        Parameters:
        ----------
        index : int, optional
            Current item index (1-based) to show position in list (default: None).
        total : int, optional
            Total count of contacts (default: None).
        max_len : int, optional
            Maximum characters allowed (default: 16).

        Returns:
        -------
        str
            A 16-character formatted string for LCD row 0.

        Examples:
        ---------
        1. contact.format_line_1(1, 3) -> "C[1/3] Alice S."
        2. contact.format_line_1() -> "Alice Smith"
        """
        if index is not None and total is not None:
            prefix = f"C[{index}/{total}] "
            available = max_len - len(prefix)
            name_part = self._name[:available]
            return f"{prefix}{name_part}"[:max_len]
        return self._name[:max_len]

    def format_line_2(self, max_len=16):
        """
        Format the second line of text for a 16-character LCD display.
        Displays title and phone number compactly.

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
        1. contact.format_line_2() -> "VP Sales 555-0199"
        """
        title_part = self._title[:7].strip()
        phone_part = self._phone[:8].strip()
        if title_part and phone_part:
            line = f"{title_part} {phone_part}"
        elif title_part:
            line = title_part
        elif phone_part:
            line = phone_part
        else:
            line = self._contact_type[:max_len]
        return line[:max_len]

    @classmethod
    def from_json(cls, data):
        """
        Instantiate a Contact instance from a JSON dictionary response.

        Parameters:
        ----------
        data : dict
            Dictionary returned by REST API endpoint `/customer/get_contacts/{id}`.

        Returns:
        -------
        Contact
            Initialized Contact instance.

        Examples:
        ---------
        1. c = Contact.from_json({"id": 1, "name": "Jane", "title": "Dir", "phone": "555-1111"})
        """
        if not isinstance(data, dict):
            Log.e(f"Contact.from_json: expected dict, got {type(data).__name__}")
            return cls()

        return cls(
            id=data.get("id", 0),
            name=data.get("name") or data.get("contact_name") or "",
            title=data.get("title") or "",
            company=data.get("company") or "",
            phone=data.get("phone") or data.get("phone_number") or "",
            contact_type=data.get("contact_type") or data.get("type") or ""
        )

    def __repr__(self):
        return f"Contact(id={self._id}, name='{self._name}', title='{self._title}', phone='{self._phone}')"


if __name__ == "__main__":
    Log.i("Starting Contact verification...")

    # 1. Instantiate Contact with direct parameters
    c1 = Contact(
        id=101,
        name="Alice Wonderland",
        title="VP Marketing",
        company="Acme Corp",
        phone="555-0142",
        contact_type="Primary"
    )
    assert c1.id == 101, "ID mismatch"
    assert c1.name == "Alice Wonderland", "Name mismatch"
    assert c1.title == "VP Marketing", "Title mismatch"
    assert c1.company == "Acme Corp", "Company mismatch"
    assert c1.phone == "555-0142", "Phone mismatch"
    assert c1.contact_type == "Primary", "Contact type mismatch"

    # 2. Verify LCD line formatting
    l1 = c1.format_line_1(1, 4)
    l2 = c1.format_line_2()
    assert len(l1) <= 16, f"Line 1 length exceeded: {l1}"
    assert len(l2) <= 16, f"Line 2 length exceeded: {l2}"
    Log.i(f"LCD Line 1: '{l1}'")
    Log.i(f"LCD Line 2: '{l2}'")

    # 3. Test from_json parser
    json_data = {
        "id": 202,
        "name": "Bob Builder",
        "title": "Engineer",
        "company": "BuildCo",
        "phone": "555-9876",
        "contact_type": "Technical"
    }
    c2 = Contact.from_json(json_data)
    assert c2.id == 202
    assert c2.name == "Bob Builder"
    assert c2.title == "Engineer"
    assert c2.phone == "555-9876"

    # 4. Test empty JSON fallback
    c_empty = Contact.from_json(None)
    assert c_empty.id == 0
    assert c_empty.name == ""

    Log.i("Testing complete - all checks passed")

