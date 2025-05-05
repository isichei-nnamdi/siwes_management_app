import streamlit as st
import re
import time
from sqlalchemy import or_
from sqlalchemy import and_
from sqlalchemy.orm import Session
from database.models import SessionLocal, User
import hashlib
import base64
from pathlib import Path
import random
import string
import smtplib
from sqlalchemy import func
from email.message import EmailMessage
import hashlib
from dashboards import admin_dashboard, student_dashboard
from supervisor_dashboard import supervisor_assessment_form
from database.models import Student, Supervisor, SessionLocal, StudentSupervisorMapping

# Set Streamlit page configuration
st.set_page_config(
    page_title="SIWES Portal",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Set background with overlay
def set_background_with_overlay(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
            .stApp {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                                url("data:image/png;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}

            .main .block-container {{
                display: flex;
                justify-content: center;
                align-items: center;
                padding-top: 4rem;
            }}

            /* 🌟 FORM BACKGROUND */
            .stForm {{
                background-color: rgba(255, 255, 255, 0.5); /* Solid white background */
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                color: #d32f2f;  /* Set text color in the form */
            }}

            /* Global text color if needed */
            body, h1, h2, h3, h4 {{
                color: #ffffff;
            }}

            .stheader, .stsubheader {{
                color: #ffffff;
            }}

            input, .stTextInput input, .stButton button {{
                background-color: rgba(255, 255, 255, 0.7);
                color: #d32f2f;
                border: 1px solid rgba(0, 0, 0, 0.2);
            }}

            input::placeholder {{
                color: #555;
            }}

            .stSelectbox div[data-baseweb="select"] {{
                background-color: rgba(255, 255, 255, 0.7);
                color: #000;
            }}

            .stButton button {{
            background-color: rgba(255, 255, 255, 0.5);
            color: white;
            padding: 0.6rem 1.2rem;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s ease;
            }}

            .stButton button:hover {{
                background-color: #b71c1c;
                color: white;
            }}

            hr {{
                    border: none;
                    border-top: 2px solid white;  /* Change color and thickness of horizontal line */
                    margin-top: 1rem;
                    margin-bottom: 1rem;
                }}
        </style>
        """,
        unsafe_allow_html=True
    )


# Apply the background
set_background_with_overlay(r"C:\Users\hp\Documents\Datafied Files\VS Code\siwes_manager_\images\miva_picture.png")


# Utility to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Verify user credentials
def verify_user(username_or_email, password, db: Session):
    user = db.query(User).filter(
        or_(User.username == username_or_email, User.email == username_or_email)
    ).first()
    if user and user.password == hash_password(password):
        return user
    return None


# Sign-up form
def is_valid_email(email):
    # Regular expression to check if the email is valid
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def check_email_domain(role, email):
    # Extract the domain from the email address
    domain = email.split('@')[-1]

    # Role-specific email domain checks
    if role == "student" and domain != "miva.edu.ng":
        return False, "Please sign up with your student's email"
    elif role == "supervisor" and domain not in ["miva.university", "miva.edu.ng"]:
        return False, "Supervisors must use a miva.university or miva.edu.ng email"
    
    return True, ""


def assign_least_loaded_supervisor(session: Session):
    # This query gets the supervisor with the fewest assigned students
    supervisor = (
        session.query(Supervisor)
        .outerjoin(Student, Supervisor.id == Student.supervisor_id)
        .group_by(Supervisor.id)
        .order_by(func.count(Student.id))  # Least assigned first
        .first()
    )
    return supervisor



# Email notification to supervisor
def send_email_to_supervisor(supervisor_email, student_name, student_email):
    msg = EmailMessage()
    msg["Subject"] = "New SIWES Student Assigned to You"
    msg["From"] = "noreply@miva.edu.ng"
    msg["To"] = supervisor_email
    msg.set_content(f"""
Dear Supervisor,

You have been assigned a new SIWES student for supervision.

Student Name: {student_name}
Student Email: {student_email}

Please log in to your dashboard to begin assessment tasks.

Thank you.
""")

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "isichei.nnamdi@gmail.com"
    sender_password = "yjmkwwrokhxlbske"

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


# Handle student signup and supervisor assignment
def student_signup(session: Session, name, email):
    supervisor = assign_least_loaded_supervisor(session)
    if not supervisor:
        return "No supervisors available right now."

    new_student = Student(name=name, email=email, supervisor_id=supervisor.id)
    session.add(new_student)
    session.commit()

    # Create StudentSupervisorMapping record
    mapping = StudentSupervisorMapping(
        student_email=email,
        supervisor_email=supervisor.email
    )
    session.add(mapping)
    session.commit()


    send_email_to_supervisor(supervisor.email, name, email)
    return f"{name} has been assigned to Supervisor {supervisor.name} ({supervisor.email})"


def signup(db):
    # List of approved supervisor emails
    approved_supervisor_emails = [
        "timothy@miva.university",
        'chinonso@miva.university',
        "jaachi@miva.university",
        "samuel@miva.university",
        "emeka@miva.university",
        "augustus@miva.university", 
        "abetianbe@miva.university",
        "sultana@miva.university",
        "ebuka.eluzai@miva.university",
        "aworinde@miva.university",
        "timothy.jideofor@miva.edu.ng",  
        "isiekwene.chioma@miva.edu.ng",  
        "emmanuel.balogun1@miva.edu.ng",
        "abigail@miva.universit",
        "adedayo@miva.university", 
        "chioma.obiajulu@miva.university",
        "isaac@miva.university", 
        "morolake.lawrence@miva.university"
    ]

    left, center, right = st.columns([1, 3, 1])
    with center:
        st.markdown(
            """
            <h3 style='color: white; text-align: left;'>Create a New Account</h3>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("signup_form"):
            username = st.text_input("Username", label_visibility="hidden", placeholder="Username")
            email = st.text_input("Email", label_visibility="hidden", placeholder="Email")
            password = st.text_input("Password", label_visibility="hidden", type="password", placeholder="Password")
            role = st.selectbox("Registering as:", ["student", "supervisor", "admin"], label_visibility="hidden", placeholder="Select your Role")
            submitted = st.form_submit_button("Sign Up")
            
            if submitted:
                # Check if any field is empty
                if not username or not email or not password:
                    st.markdown(
                        """
                        <p style='color: white; background-color: #d32f2f; padding: 0.3rem; text-align: left;'>All fields are required.</p>
                        """,
                        unsafe_allow_html=True
                    )
                elif not is_valid_email(email):
                    st.markdown(
                        """
                        <p style='color: white; background-color: #d32f2f; padding: 0.3rem; text-align: left;'>Invalid email format.</p>
                        """,
                        unsafe_allow_html=True
                    )
                elif role == "supervisor" and email not in approved_supervisor_emails:
                    st.markdown(
                        """
                        <p style='color: white; background-color: #d32f2f; padding: 0.3rem; text-align: left;'>You are not qualified to sign up as a supervisor.</p>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    # Role-specific email domain validation
                    valid, message = check_email_domain(role, email)
                    if not valid:
                        st.markdown(
                            f"""
                            <p style='color: white; background-color: #d32f2f; padding: 0.3rem; text-align: left;'>{message}</p>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        # Check if the username or email already exists
                        existing_user = db.query(User).filter(
                            or_(User.username == username, User.email == email)
                        ).first()
                        if existing_user:
                            st.markdown(
                                """
                                <p style='color: white; background-color: #d32f2f; padding: 0.3rem; text-align: left;'>User already exists.</p>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            # Create new user
                            new_user = User(
                                username=username,
                                email=email,
                                password=hash_password(password),
                                role=role
                            )
                            db.add(new_user)
                            db.commit()
                            db.refresh(new_user)

                            # Add entry to Supervisor table only if the user is a supervisor
                            if role == "supervisor":
                                new_supervisor = Supervisor(
                                    name=username,
                                    email=email,
                                    user_id=new_user.id  # <-- Proper foreign key reference
                                )
                                db.add(new_supervisor)
                                db.commit()

                                st.markdown(
                                    f"""
                                    <p style='color: white; background-color: #388e3c; padding: 0.3rem; text-align: left;'>Account created as {role.title()}! Please log in.</p>
                                    """,
                                    unsafe_allow_html=True
                                )

                                time.sleep(5)
                                st.session_state.page = "login"
                                st.rerun()

                            elif role == "student":
                                assignment_result = student_signup(db, username, email)
                                st.markdown(
                                    f"""
                                    <p style='color: white; background-color: #388e3c; padding: 0.3rem; text-align: left;'>{assignment_result}</p>
                                    """,
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    f"""
                                    <p style='color: white; background-color: #388e3c; padding: 0.3rem; text-align: left;'>Account created as {role.title()}! Please log in.</p>
                                    """,
                                    unsafe_allow_html=True
                                )

                            time.sleep(5)
                            st.session_state.page = "login"
                            st.rerun()



# Login form
# --- Helper Functions ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def send_reset_email(to_email, reset_code):
    sender_email = "isichei.nnamdi@gmail.com"
    sender_name = "Miva Support"
    app_password = "yjmkwwrokhxlbske"

    msg = EmailMessage()
    msg['Subject'] = "Password Reset Request"
    msg['From'] = f"{sender_name} <{sender_email}>"
    msg['To'] = to_email
    msg.set_content(f"""
Dear User,

You requested to reset your password. Please use the code below:

Reset Code: {reset_code}

If you did not request this, please ignore this message.

Best regards,  
{sender_name}
""")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email sending failed: {e}")
        return False

# --- Login and Reset Flow ---
def login(db):
    left, center, right = st.columns([1, 2, 1])
    with center:                
        st.markdown("<h3 style='color: white; text-align: left;'>Login</h3>", unsafe_allow_html=True)

        # Login Form
        if 'reset_phase' not in st.session_state:
            st.session_state.reset_phase = None

        if st.session_state.reset_phase is None:
            with st.form("login_form"):
                username_or_email = st.text_input("Username", label_visibility="hidden", placeholder="Username")
                password = st.text_input("Password", label_visibility="hidden", type="password", placeholder="Password")
                submitted = st.form_submit_button("Login")

            if submitted:
                user = verify_user(username_or_email, password, db)
                if user:
                    st.success(f"Welcome, {user.username}!")
                    st.session_state.user = user.username
                    st.session_state.role = user.role
                    st.session_state.email = user.email

                    # Redirect based on role
                    if user.role == "admin":
                        st.session_state.page = "admin_dashboard"
                    elif user.role == "supervisor":
                        st.session_state.page = "supervisor_dashboard"
                    elif user.role == "student":
                        st.session_state.page = "student_dashboard"
                    else:
                        st.error("Unknown role. Please contact support.")
                        return

                    st.rerun()

                else:
                    st.error("Invalid credentials.")

            # Forgot password link
            if st.button("Forgot Password?"):
                st.session_state.reset_phase = "email"
                st.rerun()

            st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

        # Phase 1: Enter Email
        elif st.session_state.reset_phase == "email":
            st.markdown("<p style='color: white; text-align: left;'>Reset Password</p>", unsafe_allow_html=True)
            email = st.text_input("Enter your registered email", label_visibility="hidden", placeholder="Enter your registered email")
            if st.button("Send Reset Code"):
                user = db.query(User).filter_by(email=email).first()
                if not user:
                    st.error("Email not found.")
                else:
                    code = ''.join(random.choices(string.digits, k=6))
                    st.session_state.reset_code = code
                    st.session_state.reset_email = email
                    if send_reset_email(email, code):
                        st.success("Reset code sent! Check your email.")
                        st.session_state.reset_phase = "code"
                        time.sleep(2)
                        st.rerun()

        # Phase 2: Enter Code and New Password
        elif st.session_state.reset_phase == "code":
            st.markdown(
                """
                <p style='color: white; text-align: left;'>Enter Reset Code and New Password</p>
                """,
                unsafe_allow_html=True
            )
            input_code = st.text_input("Reset Code", label_visibility="hidden", placeholder="Reset Code")
            new_password = st.text_input("New Password", label_visibility="hidden", placeholder="New Password", type="password")
            if st.button("Reset Password"):
                if input_code == st.session_state.get("reset_code"):
                    user = db.query(User).filter_by(email=st.session_state.reset_email).first()
                    if user:
                        user.password = hash_password(new_password)
                        db.commit()
                        st.success("Password reset successful!")
                        for k in ['reset_phase', 'reset_email', 'reset_code']:
                            st.session_state.pop(k, None)
                        time.sleep(2)
                        st.rerun()
                else:
                    st.error("Incorrect reset code.")

        # Option to go back
        if st.session_state.reset_phase is not None:
            if st.button("Back to Login"):
                for k in ['reset_phase', 'reset_email', 'reset_code']:
                    st.session_state.pop(k, None)
                st.rerun()


        
        st.markdown(
                """
                <p style='color: white; text-align: left;'>Don't have an account?</p>
                """,
                unsafe_allow_html=True
            )
        if st.button("Create an account"):
            st.session_state.page = "signup"
            st.rerun()

# Main app
def main():
    db = SessionLocal()

    # Routing logic
    if 'page' not in st.session_state:
        st.session_state.page = "login"

    if st.session_state.page == "login":
        # db = SessionLocal()
        login(db)
    elif st.session_state.page == "signup":
        # db = SessionLocal()
        signup(db)
    elif st.session_state.page == "admin_dashboard":
        admin_dashboard()
        
        left, center, right = st.columns([1, 5, 1])
        with center:
            if st.button("Logout"):
                st.session_state.clear()
                st.rerun()

    elif st.session_state.page == "supervisor_dashboard":
        # supervisor_dashboard()
        supervisor_assessment_form(db)

        left, center, right = st.columns([1, 5, 1])
        with center:
            if st.button("Logout"):
                st.session_state.clear()
                st.rerun()

    elif st.session_state.page == "student_dashboard":
        student_dashboard()
        left, center, right = st.columns([1, 5, 1])
        with center:
            if st.button("Logout"):
                st.session_state.clear()
                st.rerun()

if __name__ == "__main__":
    main()
