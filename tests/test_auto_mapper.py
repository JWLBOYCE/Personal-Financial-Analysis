import types
import sys

sys.modules.setdefault("pandas", types.ModuleType("pandas"))
sys.modules.setdefault("pdfplumber", types.ModuleType("pdfplumber"))

from parser.auto_mapper import guess_column_mapping


def test_chase_mapping():
    header = ["Transaction Date", "Description", "Amount"]
    sample = ["01/01/2023", "Coffee", "-3.50"]
    mapping = guess_column_mapping(header, sample)
    assert mapping["date"] == "transaction date"
    assert mapping["description"] == "description"
    assert mapping["amount"] == "amount"


def test_starling_mapping():
    header = ["Date", "Merchant", "Reference", "Amount", "Balance"]
    sample = ["01/01/2023", "Tesco", "", "-10.00", "100"]
    mapping = guess_column_mapping(header, sample)
    assert mapping["date"] == "date"
    assert mapping["description"] == "merchant"
    assert mapping["amount"] == "amount"


def test_santander_mapping():
    header = ["Date", "Type", "Description", "Debit", "Credit", "Balance"]
    sample = ["01/01/2023", "POS", "Shop", "20.00", "", "1000"]
    mapping = guess_column_mapping(header, sample)
    assert mapping["date"] == "date"
    assert mapping["description"] == "description"
    assert mapping["amount"] in {"debit", "credit"}


def test_amex_mapping():
    header = ["Date", "Details", "Value"]
    sample = ["01/01/2023", "Restaurant", "-50.00"]
    mapping = guess_column_mapping(header, sample)
    assert mapping["date"] == "date"
    assert mapping["description"] == "details"
    assert mapping["amount"] == "value"
