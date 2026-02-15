import streamlit as st
import pandas as pd
import numpy as np
import hashlib

st.set_page_config(page_title="DA Automation Engine", layout="wide")

st.title("📊 DA Automation Engine")
st.markdown("End-to-End DA Pool Processing | KiCredit")

# -----------------------------
# Utility Functions
# -----------------------------

def validate_flat_file(df):
    required_columns = [
        "Partner_Loan_ID",
        "Borrower_Name",
        "PAN",
        "Mobile",
        "Loan_Amount",
        "Outstanding_Principal",
        "State",
        "KCPL_Share_Pct",
        "Partner_Share_Pct"
    ]

    errors = []

    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing column: {col}")

    df["Error_Remark"] = ""

    for index, row in df.iterrows():
        if pd.isna(row["Loan_Amount"]):
            df.at[index, "Error_Remark"] = "Loan Amount Missing"

    error_df = df[df["Error_Remark"] != ""]
    valid_df = df[df["Error_Remark"] == ""]

    return valid_df, error_df


def run_dedupe(df):
    df["Dedupe_Status"] = "No Match"

    # Simple dedupe simulation based on PAN duplicates
    duplicated_pan = df[df.duplicated("PAN", keep=False)]

    df.loc[df["PAN"].isin(duplicated_pan["PAN"]), "Dedupe_Status"] = "Potential Match"

    return df


def generate_scrub_file(df):
    scrub_df = df.copy()
    scrub_df["Equifax_ID"] = scrub_df["PAN"].apply(
        lambda x: hashlib.md5(str(x).encode()).hexdigest()
    )
    scrub_df = scrub_df[["Partner_Loan_ID", "Borrower_Name", "Equifax_ID", "Loan_Amount"]]
    return scrub_df


def simulate_kiscore(df):
    df["KiScore"] = np.random.randint(500, 800, size=len(df))
    df["KiScore_Band"] = np.where(df["KiScore"] >= 650, "Accept", "Reject")
    return df


def assign_region(df):
    south = ["Tamil Nadu", "Karnataka", "Kerala", "Andhra Pradesh"]
    north = ["Delhi", "Punjab", "Haryana"]
    west = ["Maharashtra", "Gujarat"]
    east = ["West Bengal", "Odisha"]

    def region_map(state):
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

    df["Region"] = df["State"].apply(region_map)
    return df


# -----------------------------
# Sidebar Navigation
# -----------------------------

menu = st.sidebar.radio(
    "Navigation",
    ["Upload Flat File", "Dedupe", "Scrub Generation", "KiScore", "Business Dashboard"]
)

if "data" not in st.session_state:
    st.session_state.data = None

# -----------------------------
# 1. Upload Flat File
# -----------------------------

if menu == "Upload Flat File":
    st.header("📂 Upload DA Flat File")

    uploaded_file = st.file_uploader("Upload Excel/CSV File", type=["xlsx", "csv"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

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


# -----------------------------
# 2. Dedupe
# -----------------------------

elif menu == "Dedupe":
    st.header("🔍 Pool-Level Dedupe")

    if st.session_state.data is not None:
        df = run_dedupe(st.session_state.data)
        st.session_state.data = df

        st.write("Dedupe Summary")
        st.write(df["Dedupe_Status"].value_counts())

        st.dataframe(df[df["Dedupe_Status"] == "Potential Match"])

        st.download_button(
            "Download Dedupe Report",
            df.to_csv(index=False),
            file_name="dedupe_report.csv"
        )
    else:
        st.warning("Upload flat file first.")


# -----------------------------
# 3. Scrub Generation
# -----------------------------

elif menu == "Scrub Generation":
    st.header("📤 Generate Equifax Scrub File")

    if st.session_state.data is not None:
        scrub_df = generate_scrub_file(st.session_state.data)

        st.dataframe(scrub_df.head())

        st.download_button(
            "Download Equifax Scrub File",
            scrub_df.to_csv(index=False),
            file_name="equifax_scrub.csv"
        )
    else:
        st.warning("Upload flat file first.")


# -----------------------------
# 4. KiScore
# -----------------------------

elif menu == "KiScore":
    st.header("📈 KiScore Execution")

    if st.session_state.data is not None:
        df = simulate_kiscore(st.session_state.data)
        st.session_state.data = df

        st.write("KiScore Summary")
        st.write(df["KiScore_Band"].value_counts())

        st.dataframe(df.head())

        st.download_button(
            "Download KiScore Results",
            df.to_csv(index=False),
            file_name="kiscore_results.csv"
        )
    else:
        st.warning("Upload flat file first.")


# -----------------------------
# 5. Business Dashboard
# -----------------------------

elif menu == "Business Dashboard":
    st.header("📊 DA Pool Business Insights")

    if st.session_state.data is not None:
        df = st.session_state.data

        # Filters
        region_filter = st.multiselect("Select Region", df["Region"].unique())
        kiscore_filter = st.multiselect("Select KiScore Band", df.get("KiScore_Band", []).unique())

        filtered_df = df.copy()

        if region_filter:
            filtered_df = filtered_df[filtered_df["Region"].isin(region_filter)]

        if "KiScore_Band" in df.columns and kiscore_filter:
            filtered_df = filtered_df[filtered_df["KiScore_Band"].isin(kiscore_filter)]

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Loans", len(filtered_df))
        col2.metric("Total Outstanding", round(filtered_df["Outstanding_Principal"].sum(), 2))
        col3.metric("Avg KCPL Share %", round(filtered_df["KCPL_Share_Pct"].mean(), 2))

        st.subheader("Region-wise Distribution")
        st.bar_chart(filtered_df["Region"].value_counts())

        st.subheader("KCPL vs Partner Exposure")

        filtered_df["KCPL_Exposure"] = (
            filtered_df["Outstanding_Principal"] * filtered_df["KCPL_Share_Pct"] / 100
        )
        filtered_df["Partner_Exposure"] = (
            filtered_df["Outstanding_Principal"] * filtered_df["Partner_Share_Pct"] / 100
        )

        exposure_df = pd.DataFrame({
            "KCPL Exposure": [filtered_df["KCPL_Exposure"].sum()],
            "Partner Exposure": [filtered_df["Partner_Exposure"].sum()]
        })

        st.bar_chart(exposure_df)

        st.dataframe(filtered_df.head())

    else:
        st.warning("Upload and process data first.")
