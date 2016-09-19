from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, ProductCategory, CategoryItem, User
import json

engine = create_engine('sqlite:///productcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

users = session.query(User).all()
for i in users:
    print i.serialize

