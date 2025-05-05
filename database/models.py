from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime


DATABASE_URL = "sqlite:///./data/siwes.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="student")

    # Relationships
    siwes_details = relationship("SIWESDetail", back_populates="student", uselist=False)
    logs = relationship("SIWESLog", back_populates="student", uselist=False)

    # Mappings
    supervisor_mappings = relationship(
        "StudentSupervisorMapping",
        foreign_keys="[StudentSupervisorMapping.student_email]",
        back_populates="student"
    )

    student_mappings = relationship(
        "StudentSupervisorMapping",
        foreign_keys="[StudentSupervisorMapping.supervisor_email]",
        back_populates="supervisor"
    )



class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    supervisor_id = Column(Integer, ForeignKey('supervisors.id'))

    supervisor = relationship("Supervisor", back_populates="students")


class Supervisor(Base):
    __tablename__ = 'supervisors'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    name = Column(String)
    email = Column(String)

    students = relationship("Student", back_populates="supervisor")
    assessments = relationship("SupervisorAssessment", back_populates="supervisor")

    user = relationship("User")



class StudentSupervisorMapping(Base):
    __tablename__ = 'student_supervisor_mapping'

    id = Column(Integer, primary_key=True, index=True)
    student_email = Column(String, ForeignKey('users.email'), nullable=False)
    supervisor_email = Column(String, ForeignKey('users.email'), nullable=False)

    # Relationships
    student = relationship(
        "User",
        foreign_keys=[student_email],
        back_populates="supervisor_mappings"
    )
    supervisor = relationship(
        "User",
        foreign_keys=[supervisor_email],
        back_populates="student_mappings"
    )



class SIWESDetail(Base):
    __tablename__ = "siwes_details"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    matric_number = Column(String, nullable=False)
    reg_number = Column(String, nullable=False)
    email = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    cohort = Column(String, nullable=False)
    establishment_name = Column(String, nullable=False)
    establishment_contact = Column(String, nullable=False)
    acceptance_letter_path = Column(String, nullable=False)
    establishment_address = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)
    bank_account_number = Column(String, nullable=False)
    bank_account_name = Column(String, nullable=False)
    bank_sort_code = Column(String, nullable=False)
    siwes_category = Column(String, nullable=False)
    passport_url = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationship to User
    student = relationship("User", back_populates="siwes_details")


class SIWESLog(Base):
    __tablename__ = "siwes_logs"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date = Column(DateTime, nullable=False)

    # Weekly summary fields
    weekly_summary = Column(String)
    dept_section = Column(String)
    project_title = Column(String)

    # Original fields
    activities = Column(String, nullable=False)
    learning_outcome = Column(String, nullable=False)
    challenges = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="logs")

# Relationship in User model
User.logs = relationship("SIWESLog", back_populates="student", uselist=True)


class SupervisorAssessment(Base):
    __tablename__ = 'supervisor_assessments'

    id = Column(Integer, primary_key=True)
    supervisor_id = Column(Integer, ForeignKey('supervisors.id'), nullable=False)
    student_matric = Column(String, nullable=False)
    siwes_category = Column(String, nullable=False)
    assessment_type = Column(String, nullable=False)
    
    # Scores (max values in comments)
    attendance = Column(Integer)               # Max: 2
    punctuality = Column(Integer)              # Max: 2
    work_regulation = Column(Integer)          # Max: 1
    safety = Column(Integer)                   # Max: 1
    logbook = Column(Integer)                  # Max: 1
    endorsement = Column(Integer)              # Max: 2
    itf_form = Column(Integer)                 # Max: 1
    understanding = Column(Integer)            # Max: 5
    participation = Column(Integer)            # Max: 3
    industry_assessment = Column(Integer)      # Max: 5
    total_score = Column(Integer)
    num_visits = Column(Integer)
    facilities_feedback = Column(String)
    student_involvement = Column(Text)
    additional_comment = Column(Text)
    # Add fields for Oral Presentation criteria
    student_appearance = Column(Integer)         # Max: 3
    introductory_remarks = Column(Integer)       # Max: 3
    composure_confidence = Column(Integer)       # Max: 3
    work_relevance = Column(Integer)             # Max: 10
    clarity_expression_oral = Column(Integer)    # Max: 4
    concluding_remark = Column(Integer)          # Max: 3
    response_to_questions = Column(Integer)      # Max: 4
    logbook_neatness = Column(Integer)           # Max: 1
    identity_particulars = Column(Integer)       # Max: 1
    appropriate_info_page = Column(Integer)      # Max: 2
    logbook_update = Column(Integer)             # Max: 3
    diagrams_tables = Column(Integer)            # Max: 3
    terminology_arrangement = Column(Integer)    # Max: 2
    clarity_expression_logbook = Column(Integer) # Max: 3
    technical_report = Column(Integer)           # Max: 4
    logical_arrangement = Column(Integer)        # Max: 4
    historical_background = Column(Integer)      # Max: 5
    siwes_activities = Column(Integer)           # Max: 15
    summary_conclusion = Column(Integer)         # Max: 2

    submitted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    supervisor = relationship("Supervisor", back_populates="assessments")

def init_db():
    Base.metadata.create_all(bind=engine)
