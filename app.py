import streamlit as st
import pandas as pd
import numpy as np
import hashlib

st.set_page_config(page_title="DA Automation Engine", layout="wide")

st.title("📊 DA Automation Engine")
st.markdown("End-to-End DA Pool Processing | KiCredit")

# -------------------------
# Helper Functions
# -------------------------

def preprocess_file(df):

    # Rename based on Dar DA file
    df = df.rename(columns={
        "PartnerApplicationID": "partner_loan_id",
        "PAN NO": "pan",
        "Mobile No.": "mobile",
        "Loan Amount applied for (INR)": "loan_amount",
        "State": "state",
        "Bank Account No": "bank_account_no",
        "KCPL Share": "kcpl_share_pct",
        "Partner Share": "partner_share_pct"
    })

    # Create borrower name if split
    if "Applicant First Name" in df.columns:
        df["borrower_name"] = (
            df["Applicant First Name"].fillna("") + " " +
            df.get("Applicant Last Name", "").fillna("")
        )

    return df


def validate_flat_file(df):

    required_columns = [
        "partner_loan_id",
        "pan",
        "mobile",
        "loan_amount",
        "state"
    ]

    df["error_remark"] = ""

    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        st.error(f"Missing Required Columns: {missing_cols}")
        return pd.DataFrame(), df

    for i, row in df.iterrows():

        if pd.isna(row["partner_loan_id"]):
            df.at[i, "error_remark"] += "Missing Partner Loan ID | "

        if pd.isna(row["loan_amount"]):
            df.at[i, "error_remark"] += "Missing Loan Amount | "

        if pd.isna(row["pan"]):
            df.at[i, "error_remark"] += "Missing PAN | "

    error_df = df[df["error_remark"] != ""]
    valid_df = df[df["error_remark"] == ""]

    return valid_df, error_df


def assign_region(df):

    south = ["Tamil Nadu", "Karnataka", "Kerala", "Andhra Pradesh"]
    north = ["Delhi", "Punjab", "Haryana"]
    west = ["Maharashtra", "Gujarat"]
    east = ["West Bengal", "Odisha"]

    def region_map(state):
        if pd.isna(state):
            return "Unknown"
        if state in south:
            return "South"
        elif state in north:
            return "North"
        elif state in west:
            return "West"
        elif state in east:
            return "East"
        else:
            return "Other"

    df["region"] = df["state"].apply(region_map)
    return df


def run_dedupe(df):

    df["dedupe_status"] = "No Match"

    duplicated_pan = df[df.duplicated("pan", keep=False)]
    df.loc[df["pan"].isin(duplicated_pan["pan"]), "dedupe_status"] = "Potential Match"

    return df


def generate_scrub_file(df):

    scrub_df = df.copy()
    scrub_df["Equifax_ID"] = scrub_df["pan"].apply(
        lambda x: hashlib.md5(str(x).encode()).hexdigest()
    )

    scrub_df = scrub_df[
        ["partner_loan_id", "borrower_name", "pan", "mobile", "loan_amount"]
    ]

    return scrub_df


def simulate_kiscore(df):

    df["KiScore"] = np.random.randint(550, 800, len(df))
    df["KiScore_Band"] = np.where(df["KiScore"] >= 650, "Accept", "Reject")

    return df


# -------------------------
# Navigation
# -------------------------

menu = st.sidebar.radio(
    "Navigation",
    ["Upload Flat File", "Dedupe", "Scrub Generation", "KiScore", "Business Dashboard"]
)

if "data" not in st.session_state:
    st.session_state.data = None


# -------------------------
# Upload Section
# -------------------------

if menu == "Upload Flat File":

    st.header("📂 Upload DA Flat File")

    uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])

    if uploaded_file:

        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        df = preprocess_file(df)
        df = assign_region(df)

        valid_df, error_df = validate_flat_file(df)

        st.session_state.data = valid_df

        st.success(f"Valid Records: {len(valid_df)}")
        st.error(f"Error Records: {len(error_df)}")

        if len(error_df) > 0:
            st.download_button(
                "Download Error File",
                error_df.to_csv(index=False),
                file_name="error_file.csv"
            )

        st.dataframe(valid_df.head())


# -------------------------
# Dedupe
# -------------------------

elif menu == "Dedupe":

    if st.session_state.data is not None:

        df = run_dedupe(st.session_state.data)
        st.session_state.data = df

        st.subheader("Dedupe Summary")
        st.write(df["dedupe_status"].value_counts())

        st.download_button(
            "Download Dedupe Report",
            df.to_csv(index=False),
            file_name="dedupe_report.csv"
        )

    else:
        st.warning("Upload file first.")


# -------------------------
# Scrub Generation
# -------------------------

elif menu == "Scrub Generation":

    if st.session_state.data is not None:

        scrub_df = generate_scrub_file(st.session_state.data)

        st.dataframe(scrub_df.head())

        st.download_button(
            "Download Equifax Scrub File",
            scrub_df.to_csv(index=False),
            file_name="equifax_scrub.csv"
        )

    else:
        st.warning("Upload file first.")


# -------------------------
# KiScore
# -------------------------

elif menu == "KiScore":

    if st.session_state.data is not None:

        df = simulate_kiscore(st.session_state.data)
        st.session_state.data = df

        st.write(df["KiScore_Band"].value_counts())

        st.download_button(
            "Download KiScore Results",
            df.to_csv(index=False),
            file_name="kiscore_results.csv"
        )

    else:
        st.warning("Upload file first.")


# -------------------------
# Business Dashboard
# -------------------------

elif menu == "Business Dashboard":

    if st.session_state.data is not None:

        df = st.session_state.data

        region_filter = st.multiselect("Region", df["region"].unique())
        kiscore_filter = st.multiselect(
            "KiScore Band",
            df.get("KiScore_Band", pd.Series()).unique()
        )

        filtered_df = df.copy()

        if region_filter:
            filtered_df = filtered_df[filtered_df["region"].isin(region_filter)]

        if "KiScore_Band" in df.columns and kiscore_filter:
            filtered_df = filtered_df[filtered_df["KiScore_Band"].isin(kiscore_filter)]

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Loans", len(filtered_df))
        col2.metric("Total Loan Amount", round(filtered_df["loan_amount"].sum(), 2))

        if "kcpl_share_pct" in df.columns:
            col3.metric(
                "Avg KCPL Share %",
                round(filtered_df["kcpl_share_pct"].mean(), 2)
            )

        st.bar_chart(filtered_df["region"].value_counts())

        st.dataframe(filtered_df.head())

    else:
        st.warning("Upload file first.")
