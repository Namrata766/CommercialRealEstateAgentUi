import streamlit as st
import json
from agent_client import create_session, query_agent

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="Commercial Real Estate Credit Memo",
    layout="wide"
)

st.title("Commercial Real Estate Credit Memo Generator")

# ----------------------------
# Supported currencies
# ----------------------------
CURRENCIES = ["INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD"]

# ----------------------------
# Utility: split concatenated JSON
# ----------------------------
def split_concatenated_json(raw: str):
    objects = []
    decoder = json.JSONDecoder()
    idx = 0
    raw = raw.strip()

    while idx < len(raw):
        obj, offset = decoder.raw_decode(raw[idx:])
        objects.append(obj)
        idx += offset
        while idx < len(raw) and raw[idx].isspace():
            idx += 1

    return objects


# ----------------------------
# Extract credit memo text
# ----------------------------
def extract_credit_memo(response):
    if isinstance(response, str):
        responses = split_concatenated_json(response)
    elif isinstance(response, list):
        responses = response
    else:
        responses = [response]

    memo_parts = []

    for resp in responses:
        parts = resp.get("content", {}).get("parts", [])
        for p in parts:
            text = p.get("text", "")
            if text.strip():
                memo_parts.append(text.strip())

    return "\n\n".join(memo_parts)


# ----------------------------
# Loan Application Form
# ----------------------------
with st.form("loan_application_form"):
    st.subheader("Banker Details")
    user_id = st.text_input("Banker User ID")

    st.subheader("Property Details")
    col1, col2 = st.columns(2)

    with col1:
        property_name = st.text_input("Property Name")
        property_type = st.selectbox(
            "Property Type",
            ["Office", "Retail", "Residential", "Industrial", "Mixed Use"]
        )
        location = st.text_input("Location (City / Region)")
        area_sqft = st.number_input("Area (sq ft)", min_value=0.0, step=100.0)

    with col2:
        borrower_name = st.text_input("Borrower / Builder Name")

        currency = st.selectbox(
            "Currency",
            options=CURRENCIES,
            key="currency"
        )

        annual_income = st.number_input(
            "Annual Income",
            min_value=0.0,
            step=1000.0,
            key="annual_income"
        )

        loan_amount = st.number_input(
            "Requested Loan Amount",
            min_value=0.0,
            step=1000.0,
            key="loan_amount"
        )

        tenure_years = st.number_input(
            "Loan Tenure (Years)",
            min_value=0,
            step=1
        )

    st.subheader("Additional Banker Notes")
    banker_notes = st.text_area(
        "Qualitative notes, risks, mitigants, or assumptions",
        height=120
    )

    submitted = st.form_submit_button("Generate Credit Memo")


# ----------------------------
# Submission handling
# ----------------------------
if submitted:
    if not user_id:
        st.error("Banker User ID is required.")
        st.stop()

    if "session_id" not in st.session_state:
        st.session_state.session_id = create_session(user_id)

    # ---- Currency values as STRING (explicit) ----
    annual_income_str = f"{currency} {annual_income:,.2f}"
    loan_amount_str = f"{currency} {loan_amount:,.2f}"

    prompt = f"""
Generate a professional commercial real estate credit memo based on the following loan application.

Property Details:
- Property Name: {property_name}
- Property Type: {property_type}
- Location: {location}
- Area: {area_sqft} sq ft

Borrower & Financials:
- Borrower / Builder: {borrower_name}
- Annual Income: {annual_income_str}
- Requested Loan Amount: {loan_amount_str}
- Loan Tenure: {tenure_years} years

Additional Banker Notes:
{banker_notes if banker_notes else "None provided"}

Important Instructions:
- Do NOT convert currencies
- Use the currency and amounts exactly as provided
- Treat monetary values as strings, not numeric conversions

The credit memo must include:
1. Executive Summary
2. Property & Market Assessment
3. Borrower & Financial Strength Analysis
4. Risk Factors
5. Overall Credit Risk Assessment
6. Lending Recommendation
"""

    print(f"prompt is: {prompt}")

    # Optional debug
    print("Prompt sent to agent:\n", prompt)

    with st.spinner("Generating credit memo..."):
        response = query_agent(
            user_id=user_id,
            session_id=st.session_state.session_id,
            message=prompt
        )

    credit_memo = extract_credit_memo(response)

    if not credit_memo:
        st.error("No credit memo was generated. Please check agent output.")
    else:
        st.subheader("Generated Credit Memo")
        st.markdown(credit_memo)
