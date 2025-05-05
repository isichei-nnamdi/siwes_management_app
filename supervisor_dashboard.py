import streamlit as st
import random
# import smtplib
from sqlalchemy.orm import Session
from email.message import EmailMessage
from sqlalchemy.orm import Session
from sqlalchemy import text
from database.models import Student, Supervisor, SessionLocal, User, SupervisorAssessment, StudentSupervisorMapping
from datetime import datetime
from database.models import SIWESDetail, SIWESLog
from sqlalchemy.orm import joinedload



# Function to fetch assigned students using SQLAlchemy session
def fetch_assigned_students(supervisor_id):
    with SessionLocal() as session:
        result = session.execute(
            text("""
                SELECT matric_number FROM student_supervisor_mapping
                WHERE supervisor_code = :supervisor_code
            """),
            {"supervisor_code": supervisor_id}
        ).fetchall()
        return [row[0] for row in result]

# Function to get supervised students using SQLAlchemy
def get_supervised_students(session: Session, supervisor_id):
    return session.query(Student).filter(Student.supervisor_id == supervisor_id).all()

def get_numeric_input(label, min_val, max_val):
        """Helper function to get numeric input with validation."""
        value = st.text_input(label, value="", key=label, label_visibility="hidden", placeholder=label)
        if value:
            try:
                value = int(value)
                if min_val <= value <= max_val:
                    return value
                else:
                    st.error(f"Please enter a number between {min_val} and {max_val}.")
                    return None
            except ValueError:
                st.error("Please enter a valid number.")
                return None
        return None


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


def supervisor_assessment_form(db):
    # Define sidebar options
    sidebar = st.sidebar.selectbox(
        "Select Option", 
        ["Supervisor Assessment Form", "Student's Dashboard"]
    )

    if sidebar == "Supervisor Assessment Form":
        left, center, right = st.columns([1, 5, 1])
        with center:
            st.markdown(
                f"""
                <h3 style='
                    color: white; 
                    background-color: #d32f2f; 
                    padding: 0.3rem; 
                    text-align: center; 
                    border-radius: 10px;
                '>
                    SIWES Student Assessment Form
                </h3> 
                """,
                unsafe_allow_html=True
            )

        logged_in_email = st.session_state.get("email")
        if not logged_in_email:
            st.warning("You must be logged in to access this form.")
            return

        user = db.query(User).filter_by(email=logged_in_email).first()
        if not user or user.role != "supervisor":
            st.warning("Access denied. Only supervisors can fill this form.")
            return

        supervisor = db.query(Supervisor).filter_by(user_id=user.id).first()
        if not supervisor:
            st.warning("Supervisor record not found.")
            return

        
        supervisor_email = user.email  

        assigned_students = (
            db.query(Student.email)
            .join(StudentSupervisorMapping, Student.email == StudentSupervisorMapping.student_email)
            .filter(StudentSupervisorMapping.supervisor_email == supervisor_email)  # Match supervisor's email
            .all()
        )

        assigned_students = [row[0] for row in assigned_students]  # Extracting email addresses

        if not assigned_students:
            st.warning("No students have been assigned to you.")
            return

        left, center, right = st.columns([1, 5, 1])
        with center:
            st.write("")
            styled_label("Select Student Matric Number", color="white", font_size="12px", font_weight="bold")
            student_matric = st.selectbox("Select Student Matric Number", assigned_students, label_visibility="hidden")
            styled_label("Choose the type of assessment", color="white", font_size="12px", font_weight="bold")
            assessment_type = st.selectbox("Choose the type of assessment", ["On-visit/Call", "Oral Presentation"], label_visibility="hidden")
            styled_label("SIWES Category", color="white", font_size="12px", font_weight="bold")
            siwes_category = st.selectbox("SIWES Category", ["SIWES 1", "SIWES 2"], label_visibility="hidden")

        assessment_key = f"{student_matric}_{siwes_category}"

        if "submitted_records" not in st.session_state:
            st.session_state.submitted_records = set()

        if assessment_key in st.session_state.submitted_records:
            st.error(f"You've already submitted an assessment for {student_matric} - {siwes_category}")
            return

        if assessment_type == "On-visit/Call":
            left, center, right = st.columns([1, 5, 1])
            with center:
                with st.form("on_visit_assessment"):
                    st.subheader("Assessment Questions")

                    attendance = get_numeric_input("Attendance (2 Marks)", 0, 2)
                    punctuality = get_numeric_input("Punctuality (2 Marks)", 0, 2)
                    work_regulation = get_numeric_input("Compliance with general work regulation (1 Mark)", 0, 1)
                    safety = get_numeric_input("Observation of safety rules (1 Mark)", 0, 1)
                    logbook = get_numeric_input("Availability of student’s logbook (1 Mark)", 0, 1)
                    endorsement = get_numeric_input("Industrial-based supervisor’s endorsement (2 Marks)", 0, 2)
                    itf_form = get_numeric_input("Submission of ITF SPEI form to ITF Area Office (1 Mark)", 0, 1)
                    understanding = get_numeric_input("Understanding of the work (5 Marks)", 0, 5)
                    participation = get_numeric_input("Level of participation at visits (3 Marks)", 0, 3)
                    industry_assessment = get_numeric_input("General assessment of the student by industry-based supervisor (5 Marks)", 0, 5)
                    
                    styled_label("Indicate number of visits/calls", color="white", font_size="12px", font_weight="bold")
                    num_visits = st.number_input("Indicate number of visits/calls", min_value=1, max_value=2, step=1,label_visibility="hidden")

                    styled_label("Assessment of the facilities provided by company during visit(s)/call(s)", color="white", font_size="10px", font_weight="bold")
                    facilities_feedback = st.radio(
                        "Assessment of the facilities provided by company during visit(s)/call(s)",
                        ["Excellent", "Good", "Fair", "Poor"], label_visibility="hidden"
                    )
                    facilities_score_map = {
                        "Excellent": 4,
                        "Good": 3,
                        "Fair": 2,
                        "Poor": 1
                    }
                    facilities_score = facilities_score_map.get(facilities_feedback, 0)

                    styled_label("Give your impression of the Student's involvement in training", color="white", font_size="10px", font_weight="bold")
                    student_involvement = st.selectbox("Give your impression of the Student's involvement in training", 
                                            ["Choose an appropriate option..."] + ["Fully", "Partially"], label_visibility="hidden", index=0)
                    involvement_score_map = {
                        "Fully": 3,
                        "Partially": 1
                    }
                    involvement_score = involvement_score_map.get(student_involvement, 0)

                    styled_label("Additional Comment", color="white", font_size="10px", font_weight="bold")
                    additional_comment = st.text_area("Additional Comment", label_visibility="hidden")

                    submitted = st.form_submit_button("Submit Assessment")
                    if submitted:
                        if not student_involvement.strip():
                            st.error("Please provide your impression of the student's involvement in training.")
                        elif not facilities_feedback:
                            st.error("Please select a facilities assessment.")
                        else:
                            # Compute total score including new components
                            total_score = (
                                attendance + punctuality + work_regulation + safety + logbook +
                                endorsement + itf_form + understanding + participation + industry_assessment +
                                facilities_score + involvement_score
                            )

                            # ✅ Save to database
                            new_assessment = SupervisorAssessment(
                                supervisor_id=supervisor_email,
                                student_matric=student_matric,
                                siwes_category=siwes_category,
                                assessment_type=assessment_type,
                                total_score=total_score,
                                attendance=attendance,
                                punctuality=punctuality,
                                work_regulation=work_regulation,
                                safety=safety,
                                logbook=logbook,
                                endorsement=endorsement,
                                itf_form=itf_form,
                                understanding=understanding,
                                participation=participation,
                                industry_assessment=industry_assessment,
                                num_visits=num_visits,
                                facilities_feedback=facilities_feedback,
                                student_involvement=student_involvement,
                                additional_comment=additional_comment
                            )

                            db.add(new_assessment)
                            db.commit()

                            max_score = 23 + 4 + 3  # original 23 + max for facilities (4) + involvement (3)
                            st.success(f"Assessment submitted successfully! Total Score: {total_score}/{max_score}")
                            st.session_state.submitted_records.add(assessment_key)


        else:
            left, center, right = st.columns([1, 5, 1])
            with center:
                with st.form("on_oral_presentation_form"):
                    st.subheader("Oral Presentation Assessment")

                    student_appearance = get_numeric_input("Student's Appearance (0-3 Marks)", 0, 3)
                    introductory_remarks = get_numeric_input("Student's Introductory Remarks (0-3 Marks)", 0, 3)
                    composure_confidence = get_numeric_input("Composure/Confidence (0-3 Marks)", 0, 3)
                    work_relevance = get_numeric_input("Relevance of Work to Field of Study (0-10 Marks)", 0, 10)
                    clarity_expression_oral = get_numeric_input("Clarity of Expression (0-4 Marks)", 0, 4)
                    concluding_remark = get_numeric_input("Concluding Remark (0-3 Marks)", 0, 3)
                    response_to_questions = get_numeric_input("Response to Questions (0-4 Marks)", 0, 4)
                    logbook_neatness = get_numeric_input("Neatness of Logbook (0-1 Mark)", 0, 1)
                    identity_particulars = get_numeric_input("Clarity of Identity and Particulars Page (0-1 Mark)", 0, 1)
                    appropriate_info_page = get_numeric_input("Use of Appropriate Information Page (0-2 Marks)", 0, 2)
                    logbook_update = get_numeric_input("Level of Update (0-3 Marks)", 0, 3)
                    diagrams_tables = get_numeric_input("Use of Relevant Diagrams, Tables, and Charts (0-3 Marks)", 0, 3)
                    terminology_arrangement = get_numeric_input("Logical Arrangement of Terminologies (0-2 Marks)", 0, 2)
                    clarity_expression_logbook = get_numeric_input("Clarity of Expression in Logbook (0-3 Marks)", 0, 3)
                    technical_report = get_numeric_input("Technical Report (0-4 Marks)", 0, 4)
                    logical_arrangement = get_numeric_input("Logical Arrangement (0-4 Marks)", 0, 4)
                    historical_background = get_numeric_input("Historical Background with Organogram (0-5 Marks)", 0, 5)
                    siwes_activities = get_numeric_input("Activities During SIWES (0-15 Marks)", 0, 15)
                    summary_conclusion = get_numeric_input("Summary and Conclusion (0-2 Marks)", 0, 2)

                    styled_label("Additional Comment", color="white", font_size="10px", font_weight="bold")
                    additional_comment = st.text_area("Additional Comment", label_visibility="hidden")

                    submitted = st.form_submit_button("Submit Oral Assessment")

                    if submitted:
                        total_score = (
                            student_appearance + introductory_remarks + composure_confidence + work_relevance +
                            clarity_expression_oral + concluding_remark + response_to_questions + logbook_neatness +
                            identity_particulars + appropriate_info_page + logbook_update + diagrams_tables +
                            terminology_arrangement + clarity_expression_logbook + technical_report +
                            logical_arrangement + historical_background + siwes_activities + summary_conclusion
                        )

                        # ✅ Save oral assessment to database
                        new_assessment = SupervisorAssessment(
                            supervisor_id=supervisor_email,
                            student_matric=student_matric,
                            siwes_category=siwes_category,
                            assessment_type=assessment_type,
                            total_score=total_score,
                            student_appearance=student_appearance,
                            introductory_remarks=introductory_remarks,
                            composure_confidence=composure_confidence,
                            work_relevance=work_relevance,
                            clarity_expression_oral=clarity_expression_oral,
                            concluding_remark=concluding_remark,
                            response_to_questions=response_to_questions,
                            logbook_neatness=logbook_neatness,
                            identity_particulars=identity_particulars,
                            appropriate_info_page=appropriate_info_page,
                            logbook_update=logbook_update,
                            diagrams_tables=diagrams_tables,
                            terminology_arrangement=terminology_arrangement,
                            clarity_expression_logbook=clarity_expression_logbook,
                            technical_report=technical_report,
                            logical_arrangement=logical_arrangement,
                            historical_background=historical_background,
                            siwes_activities=siwes_activities,
                            summary_conclusion=summary_conclusion,
                            additional_comment=additional_comment
                        )

                        db.add(new_assessment)
                        db.commit()

                        st.success(f"Oral Presentation Assessment submitted successfully! Total Score: {total_score}/75")
                        st.session_state.submitted_records.add(assessment_key)
    
    elif sidebar == "Student's Dashboard":
        # Fetch user object (assuming you're already logged in and have `user.id`)
        logged_in_email = st.session_state.get("email")
        if not logged_in_email:
            st.warning("You must be logged in to access this form.")
            return

        user = db.query(User).filter_by(email=logged_in_email).first()
        if not user or user.role != "supervisor":
            st.warning("Access denied. Only supervisors can fill this form.")
            return

        supervisor = db.query(Supervisor).filter_by(user_id=user.id).first()
        if not supervisor:
            st.warning("Supervisor record not found.")
            return

        
        supervisor_email = user.email  


        # Step 1: Query assigned students with their SIWES details and logs
        assigned_students = (
            db.query(User)
            .join(StudentSupervisorMapping, User.email == StudentSupervisorMapping.student_email)
            .filter(StudentSupervisorMapping.supervisor_email == supervisor_email)
            .options(
                joinedload(User.siwes_details),
                joinedload(User.logs)
            )
            .all()
        )
    
        if not assigned_students:
            st.warning("No students have been assigned to you.")
        else:
            # Step 2: Create dropdown of matric numbers (only those with siwes_details)
            student_options = {
                student.siwes_details.matric_number: student
                for student in assigned_students
                if student.siwes_details  # Ensure SIWES details exist
            }

            if not student_options:

                st.warning("Your assigned students are yet to fill out their SIWES details.")
                return

            selected_matric = st.selectbox("Select a student by Matric Number", list(student_options.keys()))

            # Step 3: Display student details for selected matric
            selected_student = student_options[selected_matric]
            siwes_details = selected_student.siwes_details
            logs = selected_student.logs

            # # Display SIWES Details
            col1, col2 = st.columns(2)
            with col1:
                if siwes_details.passport_url:
                    st.image(siwes_details.passport_url, width=150)
            with col2:
                st.markdown(f"**👤 Full Name:** {siwes_details.first_name} {siwes_details.last_name}")
                st.markdown(f"**📧 Email:** {selected_student.email}")
                st.markdown(f"**🆔 Matric No:** {siwes_details.matric_number}")
                st.markdown(f"**🏛️ Department:** {siwes_details.department}")
                st.markdown(f"**🧾 Cohort:** {siwes_details.cohort}")
                st.markdown(f"**🏢 Establishment:** {siwes_details.establishment_name}")

            st.markdown("### 📘 Logs")
            # Logs with invalid or missing student_id

            # Display Logs
            if logs:
                for log in logs:
                    st.markdown(f"**📅 Date:** {log.log_date.strftime('%Y-%m-%d')}")
                    st.markdown(f"**📝 Project Title:** {log.project_title}")
                    st.markdown(f"**💼 Department/Section:** {log.dept_section}")
                    st.markdown(f"**📋 Activities:** {log.activities}")
                    st.markdown(f"**🎯 Learning Outcome:** {log.learning_outcome}")
                    st.markdown(f"**⚠️ Challenges:** {log.challenges}")
                    st.markdown("---")
            else:
                st.info("No logs submitted yet.")