import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Expand this list with real data for better accuracy
TRAINING_DATA = [
    ("swiggy food order delivery", "Food & Dining"),
    ("zomato restaurant delivery", "Food & Dining"),
    ("dominos pizza order", "Food & Dining"),
    ("kfc burger meal", "Food & Dining"),
    ("uber ride booking", "Transport"),
    ("ola cab booking", "Transport"),
    ("rapido bike taxi", "Transport"),
    ("petrol pump bpcl fuel", "Transport"),
    ("amazon shopping purchase", "Shopping"),
    ("flipkart order delivery", "Shopping"),
    ("myntra clothing fashion", "Shopping"),
    ("bigbasket grocery delivery", "Groceries"),
    ("dmart supermarket grocery", "Groceries"),
    ("blinkit quick grocery", "Groceries"),
    ("netflix subscription ott", "Entertainment"),
    ("hotstar disney premium", "Entertainment"),
    ("spotify music premium", "Entertainment"),
    ("bookmyshow movie ticket", "Entertainment"),
    ("indigo flight ticket booking", "Travel"),
    ("makemytrip hotel flight", "Travel"),
    ("irctc train ticket", "Travel"),
    ("apollo pharmacy medicine", "Health"),
    ("medplus medical store", "Health"),
    ("hospital clinic doctor fees", "Health"),
    ("electricity bill bescom payment", "Utilities"),
    ("water bill payment jal board", "Utilities"),
    ("gas bill mahanagar", "Utilities"),
    ("broadband internet bill act", "Utilities"),
    ("jio recharge mobile prepaid", "Telecom"),
    ("airtel postpaid mobile bill", "Telecom"),
    ("lic insurance premium annual", "Insurance"),
    ("zerodha stock purchase investment", "Investment"),
    ("groww sip mutual fund", "Investment"),
    ("nach debit emi loan repayment", "Loan EMI"),
    ("credit card bill payment hdfc", "Credit Card"),
    ("salary credit monthly payroll", "Income"),
    ("freelance payment client received", "Income"),
    ("fd interest credit savings", "Income"),
    ("refund order cancelled reversal", "Refund"),
    ("atm cash withdrawal", "Cash Withdrawal"),
    ("wallet load paytm topup", "Wallet"),
    ("self transfer own account", "Personal Transfer"),
    ("gym membership fitness", "Health"),
    ("salon haircut grooming", "Personal Care"),
    ("school fees tuition education", "Services"),
    ("house rent flat monthly payment", "Household"),
]

def train(output_path="data/classifier.joblib"):
    texts, labels = zip(*TRAINING_DATA)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1,
                                   max_features=10000, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, C=5.0,
                                    class_weight="balanced", solver="lbfgs")),
    ])
    pipeline.fit(X_train, y_train)
    print(classification_report(y_test, pipeline.predict(X_test), zero_division=0))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(pipeline, output_path)
    print(f"Model saved → {output_path}")

if __name__ == "__main__":
    train()