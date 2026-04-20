import re
from typing import Dict, List, Tuple, Optional

# Each rule: (category, sub_category, [keywords to match])
KEYWORD_RULES: List[Tuple[str, str, List[str]]] = [
    ("Food & Dining", "Food Delivery",   ["swiggy", "zomato", "dunzo food"]),
    ("Food & Dining", "Restaurant",      ["restaurant", "cafe", "bistro", "dhaba",
                                          "pizza", "burger", "kfc", "mcdonalds",
                                          "subway", "dominos", "starbucks", "chaayos"]),
    ("Groceries",     "Supermarket",     ["dmart", "bigbasket", "blinkit", "zepto",
                                          "jiomart", "reliance fresh", "grofers"]),
    ("Groceries",     "Local Store",     ["grocery", "kirana", "provision", "general store"]),
    ("Transport",     "Cab",             ["uber", "ola", "rapido", "meru"]),
    ("Transport",     "Metro/Bus",       ["metro", "dmrc", "bmtc", "msrtc", "redbus"]),
    ("Transport",     "Fuel",            ["petrol", "fuel", "hpcl", "bpcl", "iocl",
                                          "indian oil", "reliance petrol", "shell"]),
    ("Shopping",      "E-commerce",      ["amazon", "flipkart", "myntra", "ajio",
                                          "nykaa", "meesho", "tatacliq"]),
    ("Shopping",      "Electronics",     ["croma", "vijay sales", "reliance digital"]),
    ("Shopping",      "General",         ["mall", "plaza", "market", "bazaar"]),
    ("Entertainment", "OTT",             ["netflix", "hotstar", "disney+", "prime video",
                                          "amazon prime", "sony liv", "zee5", "voot",
                                          "jiocinema"]),
    ("Entertainment", "Music",           ["spotify", "gaana", "wynk", "jiosaavn"]),
    ("Entertainment", "Cinema",          ["bookmyshow", "pvr", "inox", "cinepolis"]),
    ("Travel",        "Flights",         ["makemytrip", "goibibo", "cleartrip", "ixigo",
                                          "indigo", "air india", "spicejet", "vistara"]),
    ("Travel",        "Hotels",          ["oyo", "treebo", "airbnb", "taj hotels"]),
    ("Travel",        "Train",           ["irctc", "indian railways", "railway"]),
    ("Health",        "Pharmacy",        ["pharmacy", "medical", "medplus", "apollo pharmacy",
                                          "1mg", "pharmeasy", "netmeds", "chemist"]),
    ("Health",        "Hospital/Clinic", ["hospital", "clinic", "diagnostic", "doctor",
                                          "nursing home", "fortis", "max hospital"]),
    ("Health",        "Fitness",         ["gym", "cult.fit", "cure.fit", "yoga", "crossfit"]),
    ("Utilities",     "Electricity",     ["bescom", "tsspdcl", "mseb", "tneb", "cesc",
                                          "electricity", "power bill"]),
    ("Utilities",     "Water",           ["water bill", "bwssb", "jal board"]),
    ("Utilities",     "Gas",             ["gas bill", "mahanagar gas", "piped gas", "lpg"]),
    ("Utilities",     "Internet",        ["jio fiber", "airtel broadband", "act fibernet",
                                          "broadband", "internet bill"]),
    ("Telecom",       "Mobile Recharge", ["jio recharge", "airtel recharge", "vi recharge",
                                          "mobile recharge", "prepaid recharge"]),
    ("Telecom",       "Postpaid",        ["jio postpaid", "airtel postpaid", "mobile bill"]),
    ("Insurance",     "Life",            ["lic", "hdfc life", "sbi life", "icici prudential",
                                          "life insurance", "tata aia"]),
    ("Insurance",     "General",         ["car insurance", "vehicle insurance", "motor insurance",
                                          "bajaj allianz", "new india assurance"]),
    ("Investment",    "Mutual Fund",     ["sip", "mutual fund", "groww mf", "kuvera",
                                          "etmoney", "mirae asset", "zerodha coin"]),
    ("Investment",    "Stocks",          ["zerodha", "upstox", "angel broking", "5paisa"]),
    ("Investment",    "Fixed Deposit",   ["fixed deposit", "fd booking", "recurring deposit"]),
    ("Loan EMI",      "Home Loan",       ["home loan emi", "housing loan", "hdfc home loan"]),
    ("Loan EMI",      "Personal Loan",   ["personal loan", "pl emi", "bajaj finserv"]),
    ("Loan EMI",      "EMI (Generic)",   ["emi", "nach debit", "ecs debit", "mandate debit"]),
    ("Credit Card",   "Payment",         ["credit card payment", "cc payment", "hdfc cc",
                                          "icici cc", "sbi cc", "axis cc", "amex"]),
    ("Personal Care", "Salon/Spa",       ["salon", "spa", "parlour", "haircut", "grooming"]),
    ("Household",     "Rent",            ["house rent", "flat rent", "pg rent", "rental"]),
    ("Household",     "Maintenance",     ["plumber", "electrician", "carpenter",
                                          "pest control", "repair"]),
    ("Services",      "Education",       ["byju", "unacademy", "vedantu", "coursera",
                                          "udemy", "school fees", "tuition"]),
    ("Services",      "Subscription",    ["subscription", "membership", "plan renewal"]),
    ("Income",        "Salary",          ["salary", "sal credit", "payroll", "wage", "stipend"]),
    ("Income",        "Freelance",       ["freelance", "consulting income", "client payment"]),
    ("Income",        "Interest",        ["interest credit", "fd interest", "dividend"]),
    ("Income",        "Refund",          ["refund", "cashback received", "reversal", "money back"]),
    ("Cash Withdrawal", "ATM",           ["atm", "cash withdrawal", "atm withdrawal", "atw", "atm wdl"]),
    ("Wallet",        "Load",            ["wallet load", "wallet topup", "add money",
                                          "paytm wallet", "phonepe wallet"]),
]

VPA_CATEGORY_PATTERNS: Dict[str, Optional[str]] = {
    r"swiggy@\w+":     "Food & Dining",
    r"zomato@\w+":     "Food & Dining",
    r"uberindia@\w+":  "Transport",
    r"olacabs@\w+":    "Transport",
    r"amazon@\w+":     "Shopping",
    r"flipkart@\w+":   "Shopping",
    r"netflix@\w+":    "Entertainment",
    r"spotify@\w+":    "Entertainment",
    r"irctc@\w+":      "Travel",
    r"makemytrip@\w+": "Travel",
    r"pharmeasy@\w+":  "Health",
    r"1mg@\w+":        "Health",
    r"zerodha@\w+":    "Investment",
    r"groww@\w+":      "Investment",
    # These are P2P bank VPAs - return None = unknown
    r"\w+@okaxis":     None,
    r"\w+@oksbi":      None,
    r"\w+@okicici":    None,
    r"\w+@okhdfcbank": None,
    r"\w+@paytm":      None,
    r"\w+@ybl":        None,
    r"\w+@ibl":        None,
}

SMS_TEMPLATES = [
    {
        "bank": "HDFC",
        "pattern": r"(?:Rs\.|INR|₹)\s*(?P<amount>[\d,]+\.?\d*)\s+(?:debited|credited).*?"
                   r"(?:VPA|UPI)?\s*(?P<vpa>[a-z0-9.\-_]+@[a-z]+)?",
        "type_keywords": {"debited": "debit", "credited": "credit"},
    },
    {
        "bank": "ICICI",
        "pattern": r"(?:INR|Rs\.?)\s*(?P<amount>[\d,]+\.?\d*)\s+(?:debited|credited).*?"
                   r"(?:UPI|VPA)\s*(?P<vpa>[a-z0-9.\-_]+@[a-z]+)?",
        "type_keywords": {"debited": "debit", "credited": "credit"},
    },
    {
        "bank": "SBI",
        "pattern": r"A/c\s+(?P<account>[X\d]+).*?(?P<type>debited|credited)\s+by\s+"
                   r"(?:Rs\.?|INR)\s*(?P<amount>[\d,]+\.?\d*)",
        "type_keywords": {"debited": "debit", "credited": "credit"},
    },
    {
        "bank": "Generic",
        "pattern": r"(?:Rs\.?|INR|₹)\s*(?P<amount>[\d,]+\.?\d*).*?"
                   r"(?P<type>debited|credited|paid|received)"
                   r".*?(?:VPA\s*(?P<vpa>[a-z0-9.\-_]+@[a-z]+))?",
        "type_keywords": {
            "debited": "debit", "paid": "debit",
            "credited": "credit", "received": "credit",
        },
    },
]

RECURRING_KEYWORDS = [
    "BBPS", "ECS", "NACH", "MANDATE", "AUTO DEBIT",
    "STANDING INSTRUCTION", "RECURRING", "SUBSCRIPTION",
]
REFUND_KEYWORDS = [
    "REFUND", "REVERSAL", "CASHBACK", "MONEY BACK",
    "CANCELLED ORDER", "ORDER CANCELLED", "REIMBURSED",
]
INCOME_KEYWORDS = [
    "SALARY", "SAL CREDIT", "PAYROLL", "STIPEND", "WAGE",
    "DIVIDEND", "INTEREST CREDIT", "FD MATURITY", "FREELANCE",
]
ATM_KEYWORDS = ["ATM", "ATM WITHDRAWAL", "CASH WITHDRAWAL", "ATW", "ATM WDL"]


def match_keyword(text: str, keywords: List[str]) -> bool:
    t = text.upper()
    return any(kw.upper() in t for kw in keywords)

def get_category_from_keywords(text: str) -> Tuple[Optional[str], Optional[str], float]:
    tl = text.lower()
    for category, sub_category, keywords in KEYWORD_RULES:
        for kw in keywords:
            if kw.lower() in tl:
                conf = 0.92 if tl.strip().startswith(kw.lower()) else 0.78
                return category, sub_category, conf
    return None, None, 0.0

def get_category_from_vpa(vpa: str) -> Optional[str]:
    if not vpa:
        return None
    for pattern, category in VPA_CATEGORY_PATTERNS.items():
        if re.match(pattern, vpa.lower()):
            return category
    return None
# ── Mixed basket merchants ───────────────────────────────────────────────────
MIXED_BASKET_MERCHANTS = [
    # Online
    "amazon", "flipkart", "myntra", "meesho", "jiomart", "nykaa",
    "tatacliq", "ajio", "snapdeal", "firstcry",
    # Physical retail
    "dmart", "big bazaar", "reliance fresh", "more supermarket",
    "spencers", "hypercity", "star bazaar", "spar",
    # Malls
    "forum mall", "phoenix", "select citywalk", "lulu mall",
    "inorbit", "nexus", "mall of india", "express avenue",
    "mantri square", "orion mall", "vr mall", "dlf mall",
    # General POS patterns
    "mall", "hypermarket", "superstore", "wholesale",
    "supermarket", "retail mart", "bazaar",
]

# ── Cashback source VPA patterns ─────────────────────────────────────────────
CASHBACK_VPA_PATTERNS = [
    "hdfcbankltd@", "icicibank@", "sbicard@",
    "phonepe.rewards@", "amazonpay.refund@",
    "paytmcashback@", "gpay.cashback@",
]

CASHBACK_KEYWORDS = [
    "CASHBACK", "CASH BACK", "REWARD CREDITED", "LOYALTY POINTS",
    "OFFER CREDIT", "PROMO CREDIT", "REFERRAL BONUS", "SCRATCH CARD",
]

# ── Deposit keywords ─────────────────────────────────────────────────────────
DEPOSIT_KEYWORDS = [
    "SECURITY DEPOSIT", "ADVANCE DEPOSIT", "ADVANCE PAYMENT",
    "SECURITY ADVANCE", "CAUTION DEPOSIT", "TOKEN ADVANCE",
]

# ── P2P VPA pattern (bare mobile number = likely person) ─────────────────────
import re as _re
P2P_VPA_PATTERN = _re.compile(r"^\d{10}@(ybl|okaxis|oksbi|okicici|okhdfcbank|paytm|upi|ibl)$")

# ── Festival calendar ────────────────────────────────────────────────────────
from datetime import date
FESTIVAL_WINDOWS_2025_2026 = [
    {"name": "Diwali",          "start": date(2025, 10, 15), "end": date(2025, 10, 25)},
    {"name": "Holi",            "start": date(2026, 3, 10),  "end": date(2026, 3, 18)},
    {"name": "Eid ul-Fitr",     "start": date(2026, 3, 28),  "end": date(2026, 4, 4)},
    {"name": "Navratri",        "start": date(2026, 3, 22),  "end": date(2026, 4, 1)},
    {"name": "Christmas",       "start": date(2025, 12, 20), "end": date(2025, 12, 28)},
    {"name": "Onam",            "start": date(2025, 8, 28),  "end": date(2025, 9, 5)},
    {"name": "Pongal",          "start": date(2026, 1, 13),  "end": date(2026, 1, 18)},
    {"name": "Raksha Bandhan",  "start": date(2025, 8, 9),   "end": date(2025, 8, 14)},
    {"name": "Wedding Season",  "start": date(2025, 11, 15), "end": date(2026, 2, 28)},
    {"name": "Back to School",  "start": date(2026, 6, 1),   "end": date(2026, 7, 15)},
]

def get_active_festival(check_date: date = None) -> dict | None:
    from datetime import date as d
    check_date = check_date or d.today()
    for f in FESTIVAL_WINDOWS_2025_2026:
        if f["start"] <= check_date <= f["end"]:
            return f
    return None

def is_mixed_basket_merchant(merchant: str, amount: float) -> bool:
    if not merchant:
        return False
    ml = merchant.lower()
    is_mixed = any(m in ml for m in MIXED_BASKET_MERCHANTS)
    if not is_mixed:
        return False
    if amount < 300:
        return False
    return True

def is_p2p_vpa(vpa: str) -> bool:
    if not vpa:
        return False
    return bool(P2P_VPA_PATTERN.match(vpa.lower()))

def is_cashback_transaction(text: str, vpa: str = None) -> bool:
    if match_keyword(text, CASHBACK_KEYWORDS):
        return True
    if vpa:
        return any(vpa.lower().startswith(p) for p in CASHBACK_VPA_PATTERNS)
    return False

def is_deposit_transaction(text: str) -> bool:
    return match_keyword(text, DEPOSIT_KEYWORDS)