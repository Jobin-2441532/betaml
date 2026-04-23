"""
Train or retrain the ML classifier.
Run directly: python scripts/train_model.py
Or via API:   POST /api/feedback/retrain-model
"""
import os
import sys
import asyncio

# Make sure project root is in path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

# ── Seed training data ────────────────────────────────────────────────────────
SEED_DATA = [
    # Food & Dining
    ("swiggy food order delivery", "Food & Dining"),
    ("zomato restaurant delivery", "Food & Dining"),
    ("dominos pizza order", "Food & Dining"),
    ("kfc burger meal chicken", "Food & Dining"),
    ("starbucks coffee cafe", "Food & Dining"),
    ("restaurant dinner lunch food", "Food & Dining"),
    ("haldiram sweets snacks", "Food & Dining"),
    ("paradise biryani restaurant", "Food & Dining"),
    ("behrouz biryani delivery", "Food & Dining"),
    ("box8 meal delivery", "Food & Dining"),
    ("faasos wrap delivery", "Food & Dining"),
    ("burger king fast food", "Food & Dining"),
    ("pizza hut order", "Food & Dining"),
    ("saravana bhavan restaurant", "Food & Dining"),
    ("udupi restaurant south indian", "Food & Dining"),
    ("chai point tea coffee", "Food & Dining"),
    ("bakery cake shop sweet", "Food & Dining"),
    ("mcdonalds mcdonald fast food", "Food & Dining"),
    ("subway sandwich", "Food & Dining"),
    ("taco bell mexican food", "Food & Dining"),

    # Transport
    ("uber ride booking cab", "Transport"),
    ("ola cab booking ride", "Transport"),
    ("rapido bike taxi", "Transport"),
    ("metro card dmrc recharge", "Transport"),
    ("redbus bus ticket booking", "Transport"),
    ("fastag toll nhai highway", "Transport"),
    ("fas tag toll plaza nh44", "Transport"),
    ("ihmcl netc fastag payment", "Transport"),
    ("toll collection highway fastag", "Transport"),
    ("nh toll plaza payment", "Transport"),
    ("nh44 toll fastag", "Transport"),
    ("national highway toll", "Transport"),
    ("parking charges fee", "Transport"),
    ("indigo flight ticket air", "Transport"),
    ("irctc train ticket railway booking", "Transport"),
    ("blusmart electric cab", "Transport"),
    ("ola electric scooter", "Transport"),

    # Fuel
    ("petrol pump bpcl hpcl fuel", "Fuel"),
    ("hp petrol pump fuel station", "Fuel"),
    ("indian oil petrol diesel", "Fuel"),
    ("reliance petrol fuel", "Fuel"),
    ("shell petrol fuel station", "Fuel"),
    ("nayara fuel petrol", "Fuel"),
    ("filling station petrol diesel", "Fuel"),

    # Shopping
    ("amazon shopping purchase order", "Shopping"),
    ("flipkart order delivery", "Shopping"),
    ("myntra clothing fashion", "Shopping"),
    ("ajio fashion online", "Shopping"),
    ("lifestyle stores mall pos", "Shopping"),
    ("reliance trends clothing fashion", "Shopping"),
    ("trends fashion store reliance retail", "Shopping"),
    ("westside clothing apparel tata", "Shopping"),
    ("pantaloons fashion retail", "Shopping"),
    ("max fashion lifestyle store", "Shopping"),
    ("shoppers stop retail", "Shopping"),
    ("tanishq jewellery gold", "Shopping"),
    ("malabar gold jewellery", "Shopping"),
    ("bata shoes footwear", "Shopping"),
    ("croma electronics store", "Shopping"),
    ("forum mall shopping", "Shopping"),
    ("phoenix mall retail", "Shopping"),
    ("fabindia clothing handloom", "Shopping"),
    ("peter england shirt", "Shopping"),
    ("van heusen clothing", "Shopping"),
    ("allen solly fashion", "Shopping"),
    ("nykaa beauty cosmetics", "Shopping"),
    ("meesho online shopping", "Shopping"),
    ("firstcry baby kids", "Shopping"),

    # Groceries
    ("bigbasket grocery delivery", "Groceries"),
    ("dmart supermarket grocery", "Groceries"),
    ("blinkit quick grocery", "Groceries"),
    ("zepto instant delivery grocery", "Groceries"),
    ("kirana store general provision", "Groceries"),
    ("reliance fresh grocery", "Groceries"),
    ("more supermarket grocery", "Groceries"),
    ("fresh vegetables fruits vendor", "Groceries"),
    ("milk delivery morning dairy", "Groceries"),
    ("country delight milk dairy", "Groceries"),
    ("jiomart grocery online", "Groceries"),
    ("spencers grocery retail", "Groceries"),
    ("sharma general store kirana", "Groceries"),
    ("patel provision store", "Groceries"),
    ("licious meat fish", "Groceries"),
    ("freshtohome fish meat", "Groceries"),

    # Entertainment
    ("netflix subscription ott streaming", "Entertainment"),
    ("hotstar disney premium", "Entertainment"),
    ("spotify music premium subscription", "Entertainment"),
    ("bookmyshow movie ticket pvr", "Entertainment"),
    ("amazon prime video subscription", "Entertainment"),
    ("sony liv subscription streaming", "Entertainment"),
    ("zee5 ott streaming", "Entertainment"),
    ("tata sky dth recharge", "Entertainment"),
    ("tata play dth subscription", "Entertainment"),
    ("dish tv dth subscription", "Entertainment"),
    ("airtel dth recharge", "Entertainment"),
    ("dream11 fantasy cricket gaming", "Entertainment"),
    ("inox cinema movie ticket", "Entertainment"),
    ("pvr cinema movie", "Entertainment"),
    ("mpl gaming mobile premier", "Entertainment"),

    # Health
    ("apollo pharmacy medicine", "Health"),
    ("medplus medical store", "Health"),
    ("1mg online pharmacy medicine", "Health"),
    ("pharmeasy medicine delivery", "Health"),
    ("netmeds pharmacy", "Health"),
    ("hospital clinic doctor fees", "Health"),
    ("gym fitness membership cult", "Health"),
    ("dr lal path labs diagnostic", "Health"),
    ("thyrocare blood test diagnostic", "Health"),
    ("metropolis labs diagnostic", "Health"),
    ("lenskart glasses spectacles optical", "Health"),
    ("dental clinic tooth treatment", "Health"),
    ("fortis hospital", "Health"),
    ("apollo hospital clinic", "Health"),
    ("max hospital health", "Health"),
    ("medical store chemist", "Health"),
    ("wellness forever pharmacy", "Health"),

    # Utilities
    ("electricity bill bescom payment", "Utilities"),
    ("bescom electricity board bbps", "Utilities"),
    ("msedcl electricity maharashtra", "Utilities"),
    ("tneb electricity tamilnadu", "Utilities"),
    ("bses electricity delhi", "Utilities"),
    ("water bill municipal payment", "Utilities"),
    ("gas bill mahanagar piped mgl", "Utilities"),
    ("igl indraprastha gas bill", "Utilities"),
    ("broadband internet bill act fibernet", "Utilities"),
    ("jio fiber broadband internet", "Utilities"),
    ("airtel broadband internet bill", "Utilities"),
    ("hathway broadband cable", "Utilities"),
    ("lpg gas cylinder booking", "Utilities"),
    ("hp gas cylinder", "Utilities"),
    ("bharat gas lpg", "Utilities"),
    ("indane gas cylinder", "Utilities"),

    # Telecom
    ("jio recharge mobile prepaid", "Telecom"),
    ("airtel postpaid mobile bill", "Telecom"),
    ("vi vodafone recharge mobile", "Telecom"),
    ("bsnl recharge mobile", "Telecom"),
    ("mobile recharge prepaid plan", "Telecom"),

    # Insurance
    ("lic insurance premium annual", "Insurance"),
    ("hdfc life insurance premium", "Insurance"),
    ("star health insurance premium", "Insurance"),
    ("bajaj allianz insurance premium", "Insurance"),
    ("term insurance premium payment", "Insurance"),
    ("car insurance vehicle premium", "Insurance"),
    ("go digit insurance", "Insurance"),
    ("acko car insurance", "Insurance"),

    # Investment
    ("zerodha stock purchase investment", "Investment"),
    ("groww sip mutual fund", "Investment"),
    ("upstox share trading", "Investment"),
    ("sbi mutual fund sip", "Investment"),
    ("nps contribution national pension", "Investment"),
    ("atal pension yojana apy", "Investment"),
    ("fixed deposit fd booking creation", "Investment"),
    ("sovereign gold bond sgb digital", "Investment"),
    ("paytm money mutual fund", "Investment"),
    ("kuvera mutual fund investment", "Investment"),
    ("recurring deposit rd bank", "Investment"),

    # Loan EMI
    ("nach debit emi loan repayment", "Loan EMI"),
    ("hdfc home loan emi payment", "Loan EMI"),
    ("bajaj finance personal loan emi", "Loan EMI"),
    ("ecs debit mandate loan", "Loan EMI"),
    ("car loan auto emi vehicle", "Loan EMI"),
    ("education loan student emi", "Loan EMI"),
    ("home loan housing emi", "Loan EMI"),
    ("two wheeler bike loan emi", "Loan EMI"),

    # Credit Card
    ("credit card bill payment hdfc", "Credit Card"),
    ("cc payment credit card", "Credit Card"),
    ("icici credit card bill", "Credit Card"),
    ("axis credit card payment", "Credit Card"),
    ("sbi credit card bill", "Credit Card"),
    ("kotak credit card payment", "Credit Card"),
    ("amex american express card", "Credit Card"),

    # Income
    ("salary credit monthly payroll neft", "Income"),
    ("freelance payment client received", "Income"),
    ("fd interest credit savings bank", "Income"),
    ("dividend credit shares", "Income"),
    ("rental income received", "Income"),

    # Refund
    ("refund order cancelled reversal", "Refund"),
    ("cashback received reversal", "Refund"),
    ("money back refund credited", "Refund"),
    ("return refund amount credited", "Refund"),

    # Cash Withdrawal
    ("atm cash withdrawal", "Cash Withdrawal"),
    ("atm wdl withdrawn cash bank", "Cash Withdrawal"),
    ("cash withdrawal atm machine", "Cash Withdrawal"),

    # Wallet
    ("wallet load paytm topup add money", "Wallet"),
    ("phonepe wallet add money load", "Wallet"),
    ("amazon pay wallet load", "Wallet"),
    ("mobikwik wallet topup", "Wallet"),

    # Personal Transfer
    ("self transfer own account neft", "Personal Transfer"),
    ("rahul kumar payment upi transfer", "Personal Transfer"),
    ("priya sharma transfer upi personal", "Personal Transfer"),
    ("amit singh upi payment friend", "Personal Transfer"),
    ("sunita devi transfer money", "Personal Transfer"),
    ("rajesh gupta payment personal", "Personal Transfer"),
    ("pooja verma upi transfer", "Personal Transfer"),
    ("suresh patel transfer friend", "Personal Transfer"),
    ("vijay nair upi personal", "Personal Transfer"),
    ("lakshmi iyer transfer personal", "Personal Transfer"),
    ("arjun menon payment friend", "Personal Transfer"),
    ("deepa krishnan upi personal", "Personal Transfer"),
    ("ravi kumar transfer", "Personal Transfer"),
    ("anita desai payment", "Personal Transfer"),
    ("mohan lal transfer upi", "Personal Transfer"),
    ("sanjay verma payment", "Personal Transfer"),

    # Personal Care
    ("salon haircut grooming spa", "Personal Care"),
    ("lakme salon beauty parlour", "Personal Care"),
    ("naturals salon haircut", "Personal Care"),
    ("jawed habib hair salon", "Personal Care"),
    ("green trends salon", "Personal Care"),
    ("enrich salon spa", "Personal Care"),
    ("barber shop haircut", "Personal Care"),

    # Household
    ("house rent flat monthly payment", "Household"),
    ("plumber electrician repair service", "Household"),
    ("society maintenance apartment rwa", "Household"),
    ("water can delivery bisleri", "Household"),
    ("urban company home service", "Household"),
    ("pest control housekeeping", "Household"),
    ("maid cook salary", "Household"),
    ("furniture ikea urban ladder", "Household"),
    ("mattress wakefit sleepyhead", "Household"),

    # Services
    ("school fees tuition education", "Services"),
    ("laundry service dry clean uclean", "Services"),
    ("dtdc courier delivery shipping", "Services"),
    ("coaching class fees institute", "Services"),
    ("ca professional fee consulting", "Services"),
    ("ss water supply laundry", "Services"),
    ("dobiee laundry wash fold", "Services"),
    ("property tax municipal government", "Services"),
    ("passport visa fee government", "Services"),
    ("traffic challan fine police", "Services"),
    ("byju unacademy vedantu online learning", "Services"),
    ("coursera udemy online course", "Services"),
]


async def load_user_corrections():
    """Load user corrections from database as extra training data."""
    try:
        from app.utils.db import AsyncSessionLocal
        from app.models.learning import MerchantMapping
        from sqlalchemy import select

        corrections = []
        async with AsyncSessionLocal() as db:
            stmt = select(MerchantMapping)
            result = await db.execute(stmt)
            mappings = result.scalars().all()

            for m in mappings:
                if m.merchant_key and m.category:
                    for _ in range(3):
                        corrections.append((m.merchant_key, m.category))

            print("  Loaded " + str(len(mappings)) + " merchant corrections from database")

        return corrections

    except Exception as e:
        print("  Could not load user corrections: " + str(e))
        return []


def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_features=15000,
            sublinear_tf=True,
            analyzer="word",
        )),
        ("clf", LogisticRegression(
            max_iter=2000,
            C=5.0,
            class_weight="balanced",
            solver="lbfgs",
            
        )),
    ])


async def train_async(output_path=None):
    if output_path is None:
        output_path = os.path.join(ROOT, "data", "classifier.joblib")

    print("")
    print("FinanceAI Model Training")
    print("=" * 40)
    print("  Root directory : " + ROOT)
    print("  Output path    : " + output_path)

    all_data = list(SEED_DATA)
    print("")
    print("Seed examples     : " + str(len(all_data)))
    print("Loading user corrections from database...")

    corrections = await load_user_corrections()
    all_data.extend(corrections)
    print("User corrections  : " + str(len(corrections)))
    print("Total samples     : " + str(len(all_data)))

    if len(all_data) < 5:
        print("ERROR: Not enough training data!")
        return None

    texts, labels = zip(*all_data)

    print("")
    print("Training model...")
    pipeline = build_pipeline()
    pipeline.fit(texts, labels)

    # Quick check
    preds = pipeline.predict(list(texts[:20]))
    correct = sum(p == l for p, l in zip(preds, list(labels[:20])))
    print("Training check    : " + str(correct) + "/20 correct")

    # Make sure output directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    joblib.dump(pipeline, output_path)

    categories = sorted(set(labels))
    print("")
    print("Model saved successfully!")
    print("  Path       : " + output_path)
    print("  Categories : " + str(len(categories)))
    print("  Samples    : " + str(len(all_data)))
    print("")
    print("Categories trained:")
    for cat in categories:
        count = list(labels).count(cat)
        print("  " + cat.ljust(25) + str(count) + " samples")

    return pipeline


def train(output_path=None):
    asyncio.run(train_async(output_path))
    return True


if __name__ == "__main__":
    train()