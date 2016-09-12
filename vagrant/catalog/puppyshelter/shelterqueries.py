from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from sqlalchemy import asc
from sqlalchemy import func

from datetime import date
from datetime import timedelta
 
from puppies import Base, Shelter, Puppy

engine = create_engine('sqlite:///puppyshelter.db')

Base.metadata.bind = engine
  
DBSession = sessionmaker(bind=engine)

session = DBSession()

puppies = session.query(Puppy).order_by('dateOfBirth')

print "Query 1: All Puppies!"
for puppy in puppies:
    print puppy.name + "\t\t" + str(puppy.dateOfBirth)

print "Query 2: 6 month and younger puppies!"
mytimedelta = timedelta(days=-180)
#print "debug: ", date.today() + mytimedelta
young_puppies = session.query(Puppy).filter(Puppy.dateOfBirth>=date.today() + mytimedelta).order_by(desc(Puppy.dateOfBirth))

for puppy in young_puppies:
    print puppy.name + "\t\t" + str(puppy.dateOfBirth)

print "Query 3: all puppies from tiny to big!" 
weighed_puppies = session.query(Puppy).order_by(asc(Puppy.weight))

for puppy in weighed_puppies:
    print puppy.name + "\t\t" + str(puppy.weight)

print "Query 4: puppies grouped by shelter!" 
total_puppies = session.query(func.count(Puppy.id).label('nr_puppies'))
grouped_puppies = session.query(func.count(Puppy.shelter_id).label('nr_of_puppies'),Shelter.name).join(Shelter).group_by(Shelter.id) 

print "For a total of " + str(total_puppies[0].nr_puppies) + " puppies:"

for shelter in grouped_puppies:
    print shelter.name + " has " + str(shelter.nr_of_puppies) + " puppies!" 

session.close()

