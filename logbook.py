import streamlit as st
from datetime import date, datetime
from database.models import SessionLocal, SIWESDetail, SIWESLog, User
import pandas as pd
import plotly.express as px
from collections import Counter
from sqlalchemy.orm import joinedload

db = SessionLocal()

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

        div[data-testid="stDateInput"] > div {{
            margin-top: -20px !important;
        }}
        </style>
        <p class="custom-label">{label_text}</p>
    """, unsafe_allow_html=True)

def show_logbook(user):
    
    menu = st.sidebar.radio("Menu", ["Log Entry", "Dashboard"])

    if menu == "Log Entry":
        st.markdown(
            """
            <h6 style='color: white; text-align: left;'>Fill in your daily SIWES activity below:</h6>
            <h7 style='color: #d32f2f; background-color: white; padding: 0.3rem; border-radius: 10px; text-align: left;'>Daily Log Entry</h7>
            """,
            unsafe_allow_html=True
        )
        st.write("")


        with st.form("log_form", clear_on_submit=True):
            styled_label("Date", color="white", font_size="12px", font_weight="bold")
            log_date = st.date_input("Date", value=date.today(), label_visibility="hidden")

            # Weekly-level details
            weekly_summary = st.text_area("General Description of Work Done", label_visibility="hidden", placeholder="General Description of Work Done")
            dept_section = st.text_input("Department/Section", label_visibility="hidden", placeholder="Department/Section")
            project_title = st.text_input("Project/Job Title for the Week", label_visibility="hidden", placeholder="Project/Job Title for the Week")

            # Core daily reflections
            activities = st.text_area("Activities for the Day", label_visibility="hidden", placeholder="What did you do today?")
            learning_outcome = st.text_area("What did you learn?", label_visibility="hidden", placeholder="New skills or knowledge gained")
            styled_label("Any Challenges Faced?", color="white", font_size="12px", font_weight="bold")
            challenges = st.text_area("Any Challenges Faced?", label_visibility="hidden", placeholder="Optional")

            submitted = st.form_submit_button("Submit Log")

            if submitted:
                if not activities or not learning_outcome:
                    st.warning("Please fill in all required fields.")
                else:
                    new_log = SIWESLog(
                        student_id=user.id,
                        log_date=log_date,
                        weekly_summary=weekly_summary,
                        dept_section=dept_section,
                        project_title=project_title,
                        activities=activities.strip(),
                        learning_outcome=learning_outcome.strip(),
                        challenges=challenges.strip(),
                    )
                    db.add(new_log)
                    db.commit()
                    st.success("Log submitted successfully!")

    elif menu == "Dashboard":
        # Fetch user object (assuming you're already logged in and have `user.id`)
        student = (
            db.query(User)
            .options(
                joinedload(User.siwes_details),
                joinedload(User.logs)
            )
            .filter(User.id == user.id)
            .first()
        )
        
        if student:
            col1, col2 = st.columns(2)
            with col1:
                if user.passport_url:
                    st.image(user.passport_url, width=150)
            with col2:
                st.markdown(
                    f"""
                    <p style='color: #d32f2f; background-color: white; padding: 0.3rem; border-radius: 10px; width: 100%; text-align: left;'>👤 Full Name: {user.first_name} {user.last_name}</p>
                    <p style='color: #d32f2f; background-color: white; padding: 0.3rem; border-radius: 10px; width: 100%; text-align: left;'>📧 Email: {user.email}</p>
                    <p style='color: #d32f2f; background-color: white; padding: 0.3rem; border-radius: 10px; width: 100%; text-align: left;'>🆔 Matric No: {user.matric_number}</p>
                    <p style='color: #d32f2f; background-color: white; padding: 0.3rem; border-radius: 10px; width: 100%; text-align: left;'>🏛️ Department: {user.department}</p>
                    <p style='color: #d32f2f; background-color: white; padding: 0.3rem; border-radius: 10px; width: 100%; text-align: left;'>🧾 Cohort: {user.cohort}</p>
                    """,
                    unsafe_allow_html=True
                )
    
            st.markdown("<hr style='border: 0.6px solid white;'>", unsafe_allow_html=True)
            # st.subheader("📝 Recent Logs")

        # Fetch logs
        logs = db.query(SIWESLog).filter_by(student_id=user.id).order_by(SIWESLog.log_date.desc()).all()

        # Convert logs to DataFrame
        if logs:
            df = pd.DataFrame([{
                "Date": log.log_date,
                "Project Title": log.project_title,
                "Department": log.dept_section,
                "Activities": log.activities,
                "Learning Outcome": log.learning_outcome,
                "Challenges": log.challenges
            } for log in logs])

            # ===== Key Metrics =====
            st.markdown(
                """
                <h5 style='color: #d32f2f; background-color: white; padding: 0.3rem; border-radius: 10px; text-align: left;'>📊 SIWES Summary Metrics</h5>
                """,
                unsafe_allow_html=True
            )

            # Date Last Seen
            last_seen = df["Date"].max() if not df.empty else "N/A"
            formatted_last_seen_human = last_seen.strftime("%B %d, %Y")
            

            st.write("")
            # Streamlit layout for white cards
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="background-color:white; padding:10px; border-radius:8px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);">
                    <p>Total Logs</p>
                    <p style="font-size:30px; font-weight:bold;">{len(df)}</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="background-color:white; padding:10px; border-radius:8px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);">
                    <p>Unique Departments</p>
                    <p style="font-size:30px; font-weight:bold;">{df["Department"].nunique()}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.write("")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="background-color:white; padding:10px; border-radius:8px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);">
                    <p>Most Frequent Dept</p>
                    <p style="font-size:30px; font-weight:bold;">{df["Department"].mode()[0] if not df["Department"].mode().empty else "N/A"}</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="background-color:white; padding:10px; border-radius:8px; box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);">
                    <p>Last Seen</p>
                    <p style="font-size:30px; font-weight:bold;">{formatted_last_seen_human}</p>
                </div>
                """, unsafe_allow_html=True)
            st.write("")
            
            # ===== Recent Logs =====
            st.markdown(
                """
                <h5 style='color: #d32f2f; background-color: white; padding: 0.3rem; border-radius: 10px; text-align: left;'>🗓️ Recent Weekly Activities</h5>
                """,
                unsafe_allow_html=True
            )
            st.write("")
            st.write(df)

        else:
            st.warning("No logs submitted yet. Please start logging your weekly activities.")


