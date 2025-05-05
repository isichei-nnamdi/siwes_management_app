from sqlalchemy import create_engine
from database.models import Base  # import your Base from the file where models are defined

engine = create_engine('sqlite:///C:/Users/hp/Documents/Datafied Files/VS Code/siwes_manager_/database/data/siwes.db') 
Base.metadata.create_all(engine)
