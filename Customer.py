"""
# Customer.py
# Represents a customer entity in the IoT CRM application.
# Holds customer attributes (id, customer_name, category, category_description,
# geography_name, type) and maintains associations to Contact and Activity entities.
# Architecturally supports both Option A (eager bulk loading) and Option B (lazy loading).
# Author: xdeve001
"""

from Log import *
from Contact import Contact
from Activity import Activity


class Customer:
    """
    Data model representing a business client / customer.

    Parameters:
    ----------
    id : int, optional
        Unique customer ID (default: 0).
    customer_name : str, optional
        Name of the customer or organization (default: "").
    category : str, optional
        Business classification category, e.g. 'Tech', 'Retail' (default: "").
    category_description : str, optional
        Extended description of the customer category (default: "").
    geography_name : str, optional
        Geographic territory or region, e.g. 'North America' (default: "").
    type : str, optional
        Customer account type, e.g. 'Enterprise', 'SMB' (default: "").

    Examples:
    ---------
    1. cust = Customer(1, "Acme Inc", "Tech", "Software", "North America", "Enterprise")
    2. cust = Customer.from_json({"id": 1, "customer_name": "Acme Inc", "type": "Enterprise"})
    """

    def __init__(self, id=0, customer_name="", category="", category_description="",
                 geography_name="", type=""):
        self._id = int(id) if id is not None else 0
        self._customer_name = str(customer_name) if customer_name is not None else ""
        self._category = str(category) if category is not None else ""
        self._category_description = str(category_description) if category_description is not None else ""
        self._geography_name = str(geography_name) if geography_name is not None else ""
        self._type = str(type) if type is not None else ""

        # Associated entity collections (0..*)
        self._contacts = []
        self._activities = []

        # Tracking flag for Option B lazy-loading (and Option A upfront population)
        self._details_loaded = False

    @property
    def id(self):
        """Get the unique customer identifier."""
        return self._id

    @property
    def customer_name(self):
        """Get the customer company or account name."""
        return self._customer_name

    @property
    def category(self):
        """Get the short category name."""
        return self._category

    @property
    def category_description(self):
        """Get the category description."""
        return self._category_description

    @property
    def geography_name(self):
        """Get the geographic location / region name."""
        return self._geography_name

    @property
    def type(self):
        """Get the customer type / tier."""
        return self._type

    def has_details_loaded(self):
        """
        Check whether contacts and activities have been loaded for this customer.

        Returns:
        -------
        bool
            True if details have been fetched and populated; False otherwise.

        Examples:
        ---------
        1. if not customer.has_details_loaded():
               controller.fetch_customer_details(customer)
        """
        return self._details_loaded

    def set_details_loaded(self, loaded=True):
        """
        Set the details loaded status.

        Parameters:
        ----------
        loaded : bool, optional
            Whether details are considered loaded (default: True).
        """
        self._details_loaded = bool(loaded)

    def add_contact(self, contact):
        """
        Associate a Contact entity with this customer.

        Parameters:
        ----------
        contact : Contact
            Contact instance to add.

        Examples:
        ---------
        1. customer.add_contact(Contact(1, "Alice", "VP"))
        """
        if isinstance(contact, Contact):
            self._contacts.append(contact)
        else:
            Log.w("Customer.add_contact: argument is not an instance of Contact")

    def set_contacts(self, contacts):
        """
        Replace the contacts list for this customer.

        Parameters:
        ----------
        contacts : list of Contact
            List of Contact instances.
        """
        self._contacts = [c for c in contacts if isinstance(c, Contact)]

    def get_contacts(self):
        """
        Retrieve the list of associated contacts.

        Returns:
        -------
        list of Contact
            List of contacts associated with this customer.
        """
        return self._contacts

    def add_activity(self, activity):
        """
        Associate an Activity record with this customer.

        Parameters:
        ----------
        activity : Activity
            Activity instance to add.

        Examples:
        ---------
        1. customer.add_activity(Activity(1, "Call", "Intro"))
        """
        if isinstance(activity, Activity):
            self._activities.append(activity)
        else:
            Log.w("Customer.add_activity: argument is not an instance of Activity")

    def set_activities(self, activities):
        """
        Replace the activities list for this customer.

        Parameters:
        ----------
        activities : list of Activity
            List of Activity instances.
        """
        self._activities = [a for a in activities if isinstance(a, Activity)]

    def get_activities(self):
        """
        Retrieve the list of associated activity records.

        Returns:
        -------
        list of Activity
            List of activities associated with this customer.
        """
        return self._activities

    def clear_details(self):
        """Clear contacts and activities and reset loaded flag."""
        self._contacts = []
        self._activities = []
        self._details_loaded = False

    def format_line_1(self, index=None, total=None, max_len=16):
        """
        Format the first line of text for a 16-character LCD display.

        Parameters:
        ----------
        index : int, optional
            Current item index (1-based) to show position in list (default: None).
        total : int, optional
            Total count of customers (default: None).
        max_len : int, optional
            Maximum characters allowed (default: 16).

        Returns:
        -------
        str
            A 16-character formatted string for LCD row 0.

        Examples:
        ---------
        1. cust.format_line_1(1, 5) -> "[1/5] Acme Corp"
        """
        if index is not None and total is not None:
            prefix = f"[{index}/{total}] "
            available = max_len - len(prefix)
            name_part = self._customer_name[:available]
            return f"{prefix}{name_part}"[:max_len]
        return self._customer_name[:max_len]

    def format_line_2(self, max_len=16):
        """
        Format the second line of text for a 16-character LCD display.
        Shows category and customer type.

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
        1. cust.format_line_2() -> "Tech | Enterprise"
        """
        cat = self._category[:7].strip()
        cust_type = self._type[:7].strip()
        if cat and cust_type:
            line = f"{cat} | {cust_type}"
        elif cat:
            line = cat
        elif cust_type:
            line = cust_type
        else:
            line = self._geography_name[:max_len]
        return line[:max_len]

    @classmethod
    def from_json(cls, data):
        """
        Instantiate a Customer instance from a JSON dictionary returned by
        the REST API endpoint `/customer/get_customers`.

        Parameters:
        ----------
        data : dict
            Dictionary representing customer record from API.

        Returns:
        -------
        Customer
            Initialized Customer instance.

        Examples:
        ---------
        1. cust = Customer.from_json({"id": 1, "customer_name": "Globex", "category": "Tech"})
        """
        if not isinstance(data, dict):
            Log.e(f"Customer.from_json: expected dict, got {type(data).__name__}")
            return cls()

        cust = cls(
            id=data.get("id", 0),
            customer_name=data.get("customer_name") or data.get("name") or "",
            category=data.get("category") or "",
            category_description=data.get("category_description") or data.get("description") or "",
            geography_name=data.get("geography_name") or data.get("geography") or "",
            type=data.get("type") or data.get("customer_type") or ""
        )

        # Support Option A if nested records are already present in JSON
        if "contacts" in data and isinstance(data["contacts"], list):
            for c_dict in data["contacts"]:
                cust.add_contact(Contact.from_json(c_dict))
        if "activities" in data and isinstance(data["activities"], list):
            for a_dict in data["activities"]:
                cust.add_activity(Activity.from_json(a_dict))

        if cust._contacts or cust._activities:
            cust.set_details_loaded(True)

        return cust

    def __repr__(self):
        return (f"Customer(id={self._id}, name='{self._customer_name}', "
                f"category='{self._category}', contacts={len(self._contacts)}, "
                f"activities={len(self._activities)}, loaded={self._details_loaded})")


if __name__ == "__main__":
    Log.i("Starting Customer verification...")

    # 1. Instantiate Customer with direct parameters
    cust = Customer(
        id=1,
        customer_name="Acme Corporation",
        category="Tech",
        category_description="High-tech enterprise solutions",
        geography_name="North America",
        type="Enterprise"
    )
    assert cust.id == 1, "ID mismatch"
    assert cust.customer_name == "Acme Corporation", "Name mismatch"
    assert cust.category == "Tech", "Category mismatch"
    assert cust.category_description == "High-tech enterprise solutions", "Description mismatch"
    assert cust.geography_name == "North America", "Geography mismatch"
    assert cust.type == "Enterprise", "Type mismatch"
    assert not cust.has_details_loaded(), "Details should initially be False"

    # 2. Add Contact and Activity
    c = Contact(10, "Alice Smith", "VP", "Acme", "555-1234", "Primary")
    a = Activity(20, "Call", "Intro", "Kickoff meeting", "2026-11-20", "Bob", "Zoom")
    cust.add_contact(c)
    cust.add_activity(a)
    assert len(cust.get_contacts()) == 1, "Contacts count mismatch"
    assert len(cust.get_activities()) == 1, "Activities count mismatch"

    cust.set_details_loaded(True)
    assert cust.has_details_loaded(), "Details should be loaded"

    # 3. Verify LCD line formatting
    l1 = cust.format_line_1(1, 10)
    l2 = cust.format_line_2()
    assert len(l1) <= 16, f"Line 1 length exceeded: {l1}"
    assert len(l2) <= 16, f"Line 2 length exceeded: {l2}"
    Log.i(f"LCD Line 1: '{l1}'")
    Log.i(f"LCD Line 2: '{l2}'")

    # 4. Test from_json parser (without nested details - typical Option B startup)
    json_data = {
        "id": 5,
        "customer_name": "Initech",
        "category": "Finance",
        "category_description": "Banking services",
        "geography_name": "Europe",
        "type": "Mid-Market"
    }
    cust2 = Customer.from_json(json_data)
    assert cust2.id == 5
    assert cust2.customer_name == "Initech"
    assert cust2.category == "Finance"
    assert not cust2.has_details_loaded()

    # 5. Test from_json parser with nested details (Option A support)
    json_data_full = {
        "id": 6,
        "customer_name": "Umbrella Corp",
        "category": "BioTech",
        "type": "Global",
        "contacts": [{"id": 601, "name": "Albert", "title": "Lead"}],
        "activities": [{"id": 701, "activity_type": "Briefing", "name": "Secret Lab"}]
    }
    cust3 = Customer.from_json(json_data_full)
    assert cust3.id == 6
    assert len(cust3.get_contacts()) == 1
    assert len(cust3.get_activities()) == 1
    assert cust3.has_details_loaded()

    Log.i("Testing complete - all checks passed")

