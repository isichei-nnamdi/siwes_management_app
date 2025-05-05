from sqlalchemy import create_engine
from database.models import Base  # import your Base from the file where models are defined

engine = create_engine('sqlite:///./data/siwes.db') 
Base.metadata.create_all(engine)
