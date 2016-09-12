import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Shelter(Base):
    __tablename__ = 'shelter'
    name = Column(String(80), nullable=False)
    address = Column(String(240))
    city = Column(String(40))
    state = Column(String(20))
    zipCode = Column(String(5))
    website = Column(String(240))
    id = Column(Integer, primary_key=True)


class Puppy(Base):
    __tablename__ = 'puppy'
    name = Column(String(80), nullable=False)
    dateOfBirth = Column(Date, nullable=False)
    gender = Column(String(6))
    weight = Column(Float())
    picture = Column(String(240))
    id = Column(Integer, primary_key=True)
    shelter_id = Column(Integer, ForeignKey('shelter.id'))
    shelter = relationship(Shelter)


engine = create_engine('sqlite:///puppyshelter.db')

Base.metadata.create_all(engine)
