import streamlit as st
import re
from uuid import uuid4
import os
from datetime import datetime
from database.models import SessionLocal, User, SIWESDetail
from logbook import show_logbook
import time


def admin_dashboard():
    st.title("Admin Dashboard")
    st.write("Welcome to the admin dashboard!")

def supervisor_dashboard():
    st.title("Supervisor Dashboard")
    st.write("Welcome to the supervisor dashboard!")
from datetime import datetime


def generate_cohorts_until_now(start_month: str, start_year: int):
    months = ["January", "May", "September"]
    cohorts = []

    # Validate and find index of the starting month
    if start_month not in months:
        raise ValueError("Start month must be one of: January, May, September")

    start_index = months.index(start_month)
    year = start_year

    # Get current date
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # Define a mapping from month names to numbers
    month_to_number = {"January": 1, "May": 5, "September": 9}

    # Loop until current date is reached or passed
    while True:
        month_name = months[start_index % 3]
        cohort_date = datetime(year, month_to_number[month_name], 1)

        if cohort_date > now:
            break

        cohorts.append(f"{month_name} {year}")

        # Advance to the next cycle
        start_index += 1
        if start_index % 3 == 0:
            year += 1

    return cohorts

cohorts = generate_cohorts_until_now("September", 2023)
cohorts.insert(0, "Cohort")


def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_matric(matric):
    return re.match(r"^\d{4}/[A-Z]/[A-Z]+/\d{4}$", matric)

def is_valid_reg(reg):
    return re.match(r"^\d{8}$", reg)

def is_valid_account_number(account):
    return account.isdigit() and len(account) == 10


def styled_label(label_text, color="black", font_size="8px", font_weight="normal"):
    """
    Displays a custom-styled label with tighter spacing before input widgets.
    """
    st.markdown(f"""
        <style>
        .custom-label {{
            color: {color};
            font-size: {font_size};
            font-weight: {font_weight};
            margin-bottom: -10px;
        }}
        div[data-testid="stMarkdownContainer"] > .custom-label + div {{
            margin-top: -20px !important;
        }}
            /* Remove top margin above all input widgets */
        div[data-testid="stSelectbox"] > div {{
            margin-top: -20px !important;
        }}

        div[data-testid="stTextInput"] > div {{
            margin-top: -20px !important;
        }}

        div[data-testid="stNumberInput"] > div {{
            margin-top: -20px !important;
        }}

        div[data-testid="stRadio"] > div {{
            margin-top: -20px !important;
        }}

        div[data-testid="stTextArea"] > div {{
            margin-top: -20px !important;
        }}
        </style>
        <p class="custom-label">{label_text}</p>
    """, unsafe_allow_html=True)


def student_dashboard():
    left, center, right = st.columns([1, 5, 1])
    with center:
        st.markdown(
            f"""
            <h5 style='
                color: white; 
                background-color: #d32f2f; 
                padding: 0.3rem; 
                text-align: center; 
                border-radius: 10px;
            '>
            Hello {st.session_state.user}, welcome to your SIWES dashboard!🤗
            </h5> 
            """,
            unsafe_allow_html=True
        )
        st.write("")

        db = SessionLocal()

        user = db.query(User).filter(User.username == st.session_state.user).first()

        if user is None:
            st.error("User not found.")
            return

        # Check if student has already submitted SIWES details
        existing_details = db.query(SIWESDetail).filter(SIWESDetail.student_id == user.id).first()
        if existing_details:
            show_logbook(existing_details)

            return

        # Check if user has already submitted for the selected category
        existing_details = db.query(SIWESDetail).filter(
            SIWESDetail.student_id == user.id
        ).all()

        # Extract submitted categories
        submitted_categories = [detail.siwes_category for detail in existing_details]

        if len(submitted_categories) == 2:
            st.success("You have already submitted details for both SIWES 1 and SIWES 2.")
            show_logbook(existing_details)
            return

        # Dropdown allows only unsubmitted categories
        available_categories = ["SIWES 1", "SIWES 2"]
        remaining_categories = [cat for cat in available_categories if cat not in submitted_categories]

        if not remaining_categories:
            st.warning("No available SIWES categories left to submit.")
            return

        # --- Show Form ---
        st.markdown("<h4 style='color: white;'>Submit Your SIWES Details</h4>", unsafe_allow_html=True)

        with st.form("siwes_form", clear_on_submit=True):
            # Constant fields (unchanging across SIWES 1/2)
            styled_label("Matric Number", color="white", font_size="12px", font_weight="bold")
            matric_number = st.text_input("Matric Number", label_visibility="hidden", placeholder="Matric Number")
            reg_number = st.text_input("Registration Number", label_visibility="hidden", placeholder="Registration Number")
            first_name = st.text_input("First Name", label_visibility="hidden", placeholder="First Name")
            last_name = st.text_input("Last Name", label_visibility="hidden", placeholder="Last Name")
            department = st.selectbox("Department", ["Department", "Computer Science", "Cybersecurity", "Data Science", "Software Engineering", "Information Technology"], label_visibility="hidden")
            cohort = st.selectbox("Cohort", ["Cohort"] + cohorts, label_visibility="hidden", index=0)
            
            # Fields specific to SIWES 1 or 2
            establishment_name = st.text_input("Establishment Name", label_visibility="hidden", placeholder="Establishment Name")
            establishment_contact = st.text_input("Establishment Contact", label_visibility="hidden", placeholder="Establishment Contact")
            establishment_address = st.text_area("Establishment Address", label_visibility="hidden", placeholder="Establishment Address")
            acceptance_letter = st.file_uploader("Upload Acceptance Letter (PDF)", type=["pdf"])

            # Constant bank fields
            bank_name = st.text_input("Bank Name", label_visibility="hidden", placeholder="Bank Name")
            bank_account_number = st.text_input("Bank Account Number", label_visibility="hidden", placeholder="Bank Account Number")
            bank_account_name = st.text_input("Bank Account Name", label_visibility="hidden", placeholder="Bank Account Name")
            bank_sort_code = st.text_input("Bank Sort Code", label_visibility="hidden", placeholder="Bank Sort Code")
            passport_photo = st.file_uploader("Upload Passport Photograph (JPG/PNG)", type=["jpg", "jpeg", "png"])

            # Only unsubmitted SIWES categories shown
            siwes_category = st.selectbox("SIWES Category", ["SIWES Category"] + remaining_categories, label_visibility="hidden")

            submitted = st.form_submit_button("Submit")
            if submitted:
                errors = []

                required_fields = [
                    matric_number, reg_number, first_name, last_name, department,
                    establishment_name, establishment_contact, establishment_address,
                    bank_name, bank_account_number, bank_account_name, bank_sort_code
                ]

                if not all(required_fields):
                    errors.append("All fields must be filled.")

                if not passport_photo:
                    errors.append("Please upload your passport photograph.")

                if not acceptance_letter:
                    errors.append("Please upload your acceptance letter.")

                if cohort == "Cohort":
                    errors.append("Please select a valid cohort.")

                if department == "Department":
                    errors.append("Please select a valid Department.")

                if siwes_category == "SIWES Category":
                    errors.append("Please select a valid SIWES category.")

                if not is_valid_matric(matric_number):
                    errors.append("Matric Number format is invalid (e.g., 2023/I/SENG/0097).")

                if not is_valid_reg(reg_number):
                    errors.append("Registration Number format is invalid (e.g., 30008309).")

                if not is_valid_email(user.email):
                    errors.append("Email address is not valid.")

                if not is_valid_account_number(bank_account_number):
                    errors.append("Bank account number must be 10 digits.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    folder = "uploaded_letters"
                    os.makedirs(folder, exist_ok=True)
                    file_path = os.path.join(folder, f"{uuid4()}.pdf")
                    with open(file_path, "wb") as f:
                        f.write(acceptance_letter.read())

                    passport_folder = "uploaded_passports"
                    os.makedirs(passport_folder, exist_ok=True)
                    passport_path = os.path.join(passport_folder, f"{uuid4()}.jpg")
                    with open(passport_path, "wb") as f:
                        f.write(passport_photo.read())

                    new_entry = SIWESDetail(
                        student_id=user.id,
                        matric_number=matric_number,
                        reg_number=reg_number,
                        email=user.email,
                        first_name=first_name,
                        last_name=last_name,
                        department=department,
                        cohort=cohort,
                        establishment_name=establishment_name,
                        establishment_contact=establishment_contact,
                        establishment_address=establishment_address,
                        acceptance_letter_path=file_path,
                        passport_url=passport_path,
                        bank_name=bank_name,
                        bank_account_number=bank_account_number,
                        bank_account_name=bank_account_name,
                        bank_sort_code=bank_sort_code,
                        siwes_category=siwes_category,
                        timestamp=datetime.utcnow()
                    )

                    db.add(new_entry)
                    db.commit()
                    st.success("SIWES details submitted successfully.")
                    time.sleep(5)
                    st.rerun()

