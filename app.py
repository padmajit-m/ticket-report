import streamlit as st
from docx import Document
import re
import io

st.title("Demand Table Expander")
st.write("Upload your DOCX file, and this app will extend demand entries up to 365.")

# File upload
uploaded_file = st.file_uploader("Upload DOCX template", type=["docx"])

if uploaded_file is not None:
    # Load document
    doc = Document(uploaded_file)

    # Find existing max demand number
    numbers = []
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                matches = re.findall(r"\$DEMANDS-(\d+)-", cell.text)
                numbers.extend([int(m) for m in matches])

    max_number = max(numbers) if numbers else 0
    st.write(f"Existing entries till: {max_number}")

    # Demand fields pattern
    field_labels = [
        "Demand Number",
        "Demand Date",
        "Outstanding Balance",
        "Principal Amount",
        "Interest Amount",
        "Emi Amount"
    ]

    demand_fields = [
        "DEMAND-NUMBER",
        "DEMAND-DATE",
        "OUTSTANDING-BALANCE",
        "PRINCIPAL-AMOUNT",
        "INTEREST-AMOUNT",
        "EMI-AMOUNT"
    ]

    # Extend demands till 365
    table = doc.tables[0]
    for i in range(max_number + 1, 366):
        # Add label row
        label_row = table.add_row()
        for j, label in enumerate(field_labels):
            label_row.cells[j].text = label

        # Add placeholder row
        placeholder_row = table.add_row()
        for j, field in enumerate(demand_fields):
            placeholder_row.cells[j].text = f"$DEMANDS-{i}-{field}$"

    # Save into memory buffer
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    # Download button
    st.download_button(
        label="Download Revised DOCX",
        data=buffer,
        file_name="demand_table_revised.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
