from core.storage.database import engine
from core.storage.models import Base

def init_database():
    Base.metadata.create_all(bind=engine)
