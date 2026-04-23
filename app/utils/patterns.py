import re
from typing import Dict, List, Tuple, Optional

# Each rule: (category, sub_category, [keywords to match])
KEYWORD_RULES: List[Tuple[str, str, List[str]]] = [

    # ── Food & Dining ─────────────────────────────────────────────────────────
    ("Food & Dining", "Food Delivery",
     ["swiggy", "zomato", "dunzo food", "magicpin food", "eatsure"]),
    ("Food & Dining", "Restaurant",
     ["restaurant", "cafe", "bistro", "dhaba", "hotel food",
      "pizza", "burger", "kfc", "mcdonalds", "mcdonald",
      "subway", "dominos", "domino", "starbucks", "chaayos",
      "chai point", "biryani", "chinese", "punjabi dhaba",
      "idli", "dosa", "udupi", "saravana bhavan", "haldiram",
      "barbeque nation", "bbq nation", "paradise biryani",
      "behrouz biryani", "box8", "freshmenu", "faasos",
      "oven story", "la pinoz", "burger king", "taco bell",
      "wendy", "pizza hut"]),
    ("Food & Dining", "Bakery",
     ["bakery", "cake shop", "confectionery", "sweet shop",
      "mithai", "halwai", "cookie", "donut", "dunkin"]),
    ("Food & Dining", "Tea/Coffee",
     ["tea", "chai", "coffee", "barista", "cafe coffee day",
      "third wave coffee", "blue tokai"]),

    # ── Groceries ────────────────────────────────────────────────────────────
    ("Groceries", "Supermarket",
     ["dmart", "bigbasket", "blinkit", "zepto", "grofers",
      "jiomart", "reliance fresh", "reliance smart",
      "more supermarket", "star bazaar", "hypercity",
      "nature basket", "spencers", "lulu hypermarket",
      "spar hypermarket", "big bazaar", "heritage fresh",
      "nilgiris", "foodhall", "smart bazaar"]),
    ("Groceries", "Local Store",
     ["grocery", "kirana", "provision", "general store",
      "supermarket", "mart", "vegetables", "fruits",
      "sabzi", "mandi", "fresh market", "daily needs",
      "sharma store", "patel store", "gupta store",
      "singh store", "verma store"]),
    ("Groceries", "Online Grocery",
     ["milkbasket", "country delight", "supr daily",
      "licious", "freshtohome", "ninjacart", "meatigo"]),

    # ── Transport ────────────────────────────────────────────────────────────
    ("Transport", "Cab",
     ["uber", "ola", "rapido", "meru", "savaari",
      "blu smart", "blusmart", "indriver"]),
    ("Transport", "Metro/Bus",
     ["metro", "dmrc", "bmtc", "nmmc", "msrtc", "ksrtc",
      "tsrtc", "apsrtc", "best bus", "redbus", "abhibus",
      "operator bus", "intercity", "shuttle"]),
    ("Transport", "Toll",                                      # FASTag fix
     ["fastag", "fas tag", "fas-tag", "toll", "nhai",
      "plaza toll", "highway toll", "nh44", "nh48",
      "nh8", "nh1", "toll plaza", "ihmcl", "netc fastag",
      "paytm fastag", "hdfc fastag", "axis fastag",
      "icici fastag", "sbi fastag"]),
    ("Transport", "Fuel",
     ["petrol", "fuel", "hpcl", "bpcl", "iocl",
      "hp petrol", "indian oil", "reliance petrol",
      "shell", "essar fuel", "nayara", "diesel"]),
    ("Transport", "Auto/Rickshaw",
     ["auto", "autorickshaw", "tuk tuk", "e-rickshaw"]),
    ("Transport", "Train",
     ["irctc", "indian railways", "railway", "train ticket",
      "pnr", "tatkal"]),
    ("Transport", "Flight",
     ["indigo", "air india", "spicejet", "vistara",
      "go air", "goair", "akasa", "air asia",
      "alliance air", "star air"]),
    ("Transport", "Parking",
     ["parking", "park smart", "fastag parking"]),

    # ── Shopping ─────────────────────────────────────────────────────────────
    ("Shopping", "E-commerce",
     ["amazon", "flipkart", "myntra", "ajio", "nykaa",
      "meesho", "snapdeal", "shopclues", "tatacliq",
      "tata cliq", "firstcry", "hopscotch", "limeroad",
      "jabong", "koovs", "purplle"]),
    ("Shopping", "Clothing",
     ["zara", "h&m", "hm", "westside", "pantaloons",
      "max fashion", "lifestyle", "shoppers stop",
      "central", "reliance trends",                          # Reliance Trends fix
      "trends", "fbb", "brand factory",
      "peter england", "raymond", "mufti", "arrow",
      "van heusen", "louis philippe", "allen solly",
      "wills lifestyle", "biba", "w for woman",
      "global desi", "anita dongre", "fabindia",
      "handloom", "khadi", "cotton world",
      "cantabil", "monte carlo", "us polo",
      "jack jones", "only", "vero moda",
      "forever 21", "marks spencer", "uniqlo"]),
    ("Shopping", "Electronics",
     ["croma", "vijay sales", "reliance digital",
      "apple store", "samsung store", "boat",
      "oneplus store", "mi store", "xiaomi",
      "lenovo", "hp store", "dell", "asus store",
      "lg store", "sony center"]),
    ("Shopping", "General",
     ["mall", "plaza", "market", "bazaar", "emporium",
      "forum mall", "phoenix mall", "nexus mall",
      "lulu mall", "express avenue", "select citywalk",
      "dlf mall", "ambience mall", "inorbit mall",
      "vr mall", "mantri mall", "orion mall",
      "gt world mall", "garuda mall"]),
    ("Shopping", "Jewellery",
     ["tanishq", "malabar gold", "kalyan jewellers",
      "joyalukkas", "pc jeweller", "tribhovandas",
      "senco gold", "orra jewellery", "caratlane"]),
    ("Shopping", "Footwear",
     ["bata", "metro shoes", "liberty shoes",
      "woodland", "puma store", "nike store",
      "adidas store", "reebok", "red tape",
      "mochi shoes", "naturalizer", "crocs"]),

    # ── Entertainment ────────────────────────────────────────────────────────
    ("Entertainment", "OTT",
     ["netflix", "hotstar", "disney+", "disney plus",
      "prime video", "amazon prime", "sony liv", "sonyliv",
      "zee5", "voot", "jiocinema", "alt balaji",
      "manorama max", "sun nxt", "aha video",
      "shemaroo", "erosnow", "hungama play",
      "apple tv", "lionsgate"]),
    ("Entertainment", "Music",
     ["spotify", "gaana", "wynk", "jiosaavn",
      "apple music", "youtube music", "hungama music",
      "amazon music"]),
    ("Entertainment", "Gaming",
     ["steam", "google play games", "xbox",
      "playstation", "gaming", "dream11", "mpl",
      "winzo", "fantasy cricket", "my11circle",
      "gameskraft", "zupee"]),
    ("Entertainment", "Cinema",
     ["bookmyshow", "pvr", "inox", "cinepolis",
      "carnival cinemas", "miraj cinemas",
      "moviemax", "national amusements"]),
    ("Entertainment", "DTH",
     ["tata sky", "tatasky", "dish tv", "airtel dth",
      "sun direct", "videocon d2h", "dd free dish",
      "tata play"]),
    ("Entertainment", "Events",
     ["district app", "paytm insider", "zomato live",
      "ticketmaster", "eventbrite", "livesite"]),

    # ── Travel ───────────────────────────────────────────────────────────────
    ("Travel", "Flights",
     ["makemytrip", "goibibo", "cleartrip", "ixigo",
      "yatra", "ease my trip", "easemytrip",
      "via.com", "travel guru"]),
    ("Travel", "Hotels",
     ["oyo", "treebo", "fabhotels", "airbnb",
      "trivago", "agoda", "booking.com",
      "taj hotels", "oberoi", "itc hotels",
      "hyatt", "marriott", "holiday inn",
      "radisson", "novotel", "ibis hotel",
      "lemon tree", "ginger hotel", "keys hotel",
      "zostel", "backpacker panda", "hotel"]),
    ("Travel", "Train",
     ["irctc", "indian railways"]),
    ("Travel", "Bus",
     ["redbus", "abhibus", "kallada", "parveen",
      "orange tours", "neeta tours", "vrl travels",
      "royal travels", "chartered bus"]),
    ("Travel", "Cab Intercity",
     ["zoomcar", "zoom car", "drivezy", "revv",
      "myles car", "savaari outstation"]),

    # ── Health ───────────────────────────────────────────────────────────────
    ("Health", "Pharmacy",
     ["pharmacy", "medical", "medplus", "apollo pharmacy",
      "1mg", "pharmeasy", "netmeds", "chemist",
      "wellness forever", "frank ross",
      "guardian pharmacy", "health & glow",
      "medicine", "drug store", "dispensary"]),
    ("Health", "Hospital/Clinic",
     ["hospital", "clinic", "diagnostic", "pathology",
      "doctor", "dr.", "nursing home", "health centre",
      "fortis", "apollo hospital", "max hospital",
      "narayana health", "manipal hospital",
      "aster", "columbia asia", "rainbow hospital",
      "cloudnine", "motherhood", "nhc health",
      "thyrocare", "dr lal path", "metropolis",
      "srl diagnostics", "healthians"]),
    ("Health", "Insurance",
     ["star health", "niva bupa", "hdfc ergo health",
      "care health", "aditya birla health",
      "max bupa", "religare health"]),
    ("Health", "Fitness",
     ["gym", "cult.fit", "cure.fit", "yoga",
      "fitness", "crossfit", "gold gym",
      "anytime fitness", "talwalkars",
      "snap fitness", "f45", "powerhouse gym"]),
    ("Health", "Optical",
     ["lenskart", "vision express", "lawrence mayo",
      "titan eye", "optical", "spectacles", "glasses"]),
    ("Health", "Dental",
     ["dental", "dentist", "tooth", "orthodontist",
      "smile dental", "dental clinic"]),

    # ── Utilities ────────────────────────────────────────────────────────────
    ("Utilities", "Electricity",
     ["bescom", "tsspdcl", "mseb", "msedcl", "tneb",
      "cesc", "adani electric", "bses", "tpddl",
      "electricity", "power bill", "bijlee",
      "wbsedcl", "kseb", "kesco", "dhbvn",
      "uhbvn", "jvvnl", "avvnl"]),
    ("Utilities", "Water",
     ["water bill", "bwssb", "jal board", "nmmc water",
      "water supply", "municipal water", "cwss"]),
    ("Utilities", "Gas",
     ["gas bill", "mahanagar gas", "mgl", "igl",
      "indraprastha gas", "gujarat gas", "adani gas",
      "piped gas", "lpg", "hp gas", "bharat gas",
      "indane gas", "cooking gas"]),
    ("Utilities", "Internet",
     ["jio fiber", "jiofiber", "airtel broadband",
      "act fibernet", "hathway", "you broadband",
      "tataplay broadband", "broadband", "internet bill",
      "tikona", "spectranet", "alliance broadband",
      "excitel", "den networks"]),

    # ── Telecom ───────────────────────────────────────────────────────────────
    ("Telecom", "Mobile Recharge",
     ["jio recharge", "airtel recharge", "vi recharge",
      "vodafone recharge", "bsnl recharge",
      "mobile recharge", "prepaid recharge",
      "phonepe recharge", "talk time"]),
    ("Telecom", "Postpaid",
     ["jio postpaid", "airtel postpaid", "vi postpaid",
      "vodafone postpaid", "bsnl postpaid", "mobile bill"]),

    # ── Insurance ────────────────────────────────────────────────────────────
    ("Insurance", "Life",
     ["lic", "hdfc life", "max life", "sbi life",
      "icici prudential", "bajaj allianz life",
      "tata aia", "birla sun life", "kotak life",
      "life insurance", "term insurance", "ulip"]),
    ("Insurance", "General",
     ["new india assurance", "national insurance",
      "reliance general", "bajaj allianz general",
      "car insurance", "vehicle insurance",
      "motor insurance", "two wheeler insurance",
      "go digit", "acko", "tata aig",
      "hdfc ergo", "iffco tokio", "oriental insurance"]),
    ("Insurance", "Health",
     ["health insurance", "mediclaim", "family floater"]),

    # ── Investment ───────────────────────────────────────────────────────────
    ("Investment", "Mutual Fund",
     ["sip", "mutual fund", "zerodha coin", "groww mf",
      "paytm money", "kuvera", "etmoney",
      "mirae asset", "axis mutual", "sbi mutual",
      "hdfc mutual", "icici pru mf", "nippon india",
      "dsp mutual", "franklin templeton",
      "kotak mutual", "uti mutual", "aditya birla mf"]),
    ("Investment", "Stocks",
     ["zerodha", "upstox", "angel broking", "angel one",
      "iifl securities", "motilal oswal",
      "sharekhan", "5paisa", "kotak securities",
      "hdfc securities", "icici direct", "sbicap",
      "geojit", "ventura securities"]),
    ("Investment", "Fixed Deposit",
     ["fixed deposit", "fd booking", "fd creation",
      "recurring deposit", "rd", "nsc", "post office"]),
    ("Investment", "Gold",
     ["sovereign gold bond", "sgb", "digital gold",
      "mmtc-pamp", "safe gold"]),
    ("Investment", "NPS",
     ["nps", "national pension", "atal pension",
      "apy contribution"]),

    # ── Loan EMI ─────────────────────────────────────────────────────────────
    ("Loan EMI", "Home Loan",
     ["home loan emi", "housing loan", "hdfc home loan",
      "sbi home loan", "lic home loan", "mortgage"]),
    ("Loan EMI", "Personal Loan",
     ["personal loan", "pl emi", "bajaj finserv",
      "fullerton", "muthoot finance", "manappuram",
      "iifl loan", "poonawalla", "early salary",
      "money tap", "kreditbee", "lazypay", "cashe"]),
    ("Loan EMI", "Vehicle Loan",
     ["auto loan", "car loan", "vehicle emi",
      "bike loan", "two wheeler loan",
      "hdfc car loan", "sbi car loan"]),
    ("Loan EMI", "Education Loan",
     ["education loan", "student loan", "vidya lakshmi"]),
    ("Loan EMI", "EMI Generic",
     ["emi", "nach debit", "ecs debit", "mandate debit",
      "nach", "ecs", "auto debit emi", "loan emi"]),

    # ── Credit Card ───────────────────────────────────────────────────────────
    ("Credit Card", "Payment",
     ["credit card payment", "cc payment", "cc pmt",
      "hdfc cc", "icici cc", "sbi cc", "axis cc",
      "kotak cc", "amex", "citibank cc",
      "standard chartered cc", "rbl cc",
      "indusind cc", "yes bank cc",
      "credit card bill"]),

    # ── Personal Care ─────────────────────────────────────────────────────────
    ("Personal Care", "Salon/Spa",
     ["salon", "spa", "parlour", "parlor", "haircut",
      "grooming", "waxing", "facial", "loreal",
      "lakme salon", "naturals salon", "jawed habib",
      "toni guy", "green trends", "enrich salon",
      "bbkumar", "barber"]),
    ("Personal Care", "Personal Items",
     ["personal care", "hygiene", "cosmetics",
      "perfume", "deodorant", "sanitary",
      "beauty products", "mamaearth", "wow skin",
      "plum beauty", "biotique"]),

    # ── Household ────────────────────────────────────────────────────────────
    ("Household", "Rent",
     ["house rent", "flat rent", "pg rent",
      "rental", "rent payment", "accommodation rent",
      "room rent", "paying guest"]),
    ("Household", "Maintenance",
     ["plumber", "electrician", "carpenter",
      "pest control", "housekeeping", "maid",
      "cook", "repair", "maintenance",
      "society maintenance", "apartment maintenance",
      "housing society", "rwa", "urban company",
      "sanitization", "deep cleaning"]),
    ("Household", "Furniture",
     ["ikea", "urban ladder", "pepperfry",
      "godrej furniture", "durian", "wooden street",
      "furniture", "sofa", "mattress",
      "wakefit", "sleepyhead", "sunday mattress"]),
    ("Household", "Appliances",
     ["lg", "samsung appliance", "bosch",
      "whirlpool", "voltas", "daikin", "havells",
      "philips", "bajaj electricals", "crompton",
      "usha", "orient electric", "v-guard",
      "butterfly", "prestige"]),
    ("Household", "Water",
     ["water can", "water delivery", "bisleri",
      "aquaguard service", "kent service",
      "purifier service"]),

    # ── Services ─────────────────────────────────────────────────────────────
    ("Services", "Education",
     ["byju", "unacademy", "vedantu", "coursera",
      "udemy", "udacity", "school fees",
      "college fees", "tuition", "coaching",
      "whitehat jr", "toppr", "testbook",
      "gradeup", "adda247", "career launcher",
      "time institute", "ims learning"]),
    ("Services", "Government",
     ["challan", "passport", "visa fee",
      "court fee", "registration fee",
      "government", "municipal", "traffic fine",
      "mca", "irda", "sebi", "income tax",
      "gst payment", "tds", "property tax"]),
    ("Services", "Subscription",
     ["subscription", "membership", "plan renewal",
      "annual plan", "yearly plan"]),
    ("Services", "Professional",
     ["consulting", "freelance payment",
      "professional fee", "ca fee",
      "lawyer fee", "advocate", "notary",
      "auditor", "architect fee"]),
    ("Services", "Laundry",
     ["laundry", "dry clean", "wash and fold",
      "uclean", "dobiee", "cleanokart",
      "fabclean", "laundry service"]),
    ("Services", "Courier",
     ["dtdc", "bluedart", "delhivery", "ekart",
      "xpressbees", "ecom express", "speed post",
      "india post", "professional courier",
      "shree tirupati courier"]),

    # ── Income ───────────────────────────────────────────────────────────────
    ("Income", "Salary",
     ["salary", "sal credit", "payroll", "wage",
      "stipend", "monthly pay", "remuneration"]),
    ("Income", "Freelance",
     ["freelance", "consulting income",
      "project payment", "client payment",
      "contract payment"]),
    ("Income", "Interest",
     ["interest credit", "fd interest",
      "savings interest", "dividend",
      "int credit", "rd interest"]),
    ("Income", "Refund",
     ["refund", "cashback received",
      "reversal", "money back", "returned"]),
    ("Income", "Rental",
     ["rental income", "rent received",
      "tenant payment"]),

    # ── Cash Withdrawal ───────────────────────────────────────────────────────
    ("Cash Withdrawal", "ATM",
     ["atm", "cash withdrawal", "atm withdrawal",
      "atw", "atm wdl", "cash@pos",
      "withdrawn from atm"]),

    # ── Wallet ───────────────────────────────────────────────────────────────
    ("Wallet", "Load",
     ["wallet load", "wallet topup", "add money",
      "paytm wallet", "phonepe wallet",
      "amazon pay wallet", "mobikwik",
      "freecharge wallet", "airtel money"]),

    # ── Fuel (separate from Transport for clearer charts) ────────────────────
    ("Fuel", "Petrol/Diesel",
     ["petrol pump", "fuel station", "filling station"]),

    # ── Education ────────────────────────────────────────────────────────────
    ("Services", "Childcare",
     ["creche", "daycare", "playschool",
      "nursery fees", "kindergarten",
      "montessori fees"]),
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