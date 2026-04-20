import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.sms_parser import SMSParser
from app.core.classifier import HybridClassifier

parser = SMSParser()
clf = HybridClassifier()

def parse_classify(sms):
    return clf.classify(parser.parse(sms))

def test_swiggy():
    r = parse_classify("Rs.350 debited. UPI: swiggy@icici. Ref: 123456")
    assert r.category == "Food & Dining"

def test_uber():
    r = parse_classify("Rs.180 debited. Paid to uberindia@hdfcbank.")
    assert r.category == "Transport"

def test_atm():
    r = parse_classify("ATM WDL Rs.5000 from XX1234. Date 14/04/2024")
    assert r.category == "Cash Withdrawal"
    assert r.is_atm is True

def test_salary():
    r = parse_classify("INR 75000 credited. Remarks: SALARY APR 2024")
    assert r.category == "Income"
    assert r.is_income is True

def test_refund():
    r = parse_classify("REFUND of Rs.350 credited. Swiggy order cancelled.")
    assert r.category == "Refund"
    assert r.is_refund is True

def test_merchant_override():
    custom_clf = HybridClassifier(merchant_mappings={"amazon": ("Shopping", "E-commerce")})
    parsed = parser.parse("Rs.999 debited. Paid to Amazon.")
    parsed.merchant = "Amazon"
    r = custom_clf.classify(parsed)
    assert r.category == "Shopping" and r.confidence == 0.99

def test_netflix():
    r = parse_classify("Rs.499 debited for Netflix subscription.")
    assert r.category == "Entertainment"

def test_split_engine():
    from datetime import datetime, timedelta
    from app.core.split_engine import RawTransaction, SplitEngine
    base = datetime(2024, 4, 1)
    txs = [
        RawTransaction(id=1, amount=2500, tx_type="debit",  tx_date=base),
        RawTransaction(id=2, amount=833,  tx_type="credit", tx_date=base + timedelta(days=1)),
        RawTransaction(id=3, amount=833,  tx_type="credit", tx_date=base + timedelta(days=2)),
    ]
    results = SplitEngine().detect_splits(txs)
    assert len(results) == 1
    assert results[0].net_expense < 2500

def test_recurring():
    from datetime import datetime, timedelta
    from app.core.recurring_detector import RecurringDetector
    base = datetime(2024, 1, 1)
    txs = [
        {"merchant": "Netflix", "category": "Entertainment", "sub_category": "OTT",
         "amount": 499, "tx_type": "debit",
         "tx_date": base + timedelta(days=30 * i), "raw_text": "Netflix subscription"}
        for i in range(3)
    ]
    results = RecurringDetector().detect(txs)
    assert any("netflix" in c.merchant.lower() for c in results)