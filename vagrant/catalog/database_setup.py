from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy import UniqueConstraint

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return user data for verification purposes"""
        return {
                'id' : self.id,
                'name' : self.name,
                'email' : self.email
                }


class ProductCategory(Base):
    __tablename__ = 'product_category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name' : self.name,
           'id' : self.id,
       }


class CategoryItem(Base):
    __tablename__ = 'category_item'

    name =Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(999))
    price = Column(String(8))
    subcategory = Column(String(250))
    image_filename = Column(String(30))
    product_category_id = Column(Integer, ForeignKey('product_category.id'))
    product_category = relationship(ProductCategory)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    __table_args__ = ( UniqueConstraint('product_category_id', 'name'),)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'id' : self.id,
           'name' : self.name,
           'description' : self.description,
           'price' : self.price,
           'category_id': self.product_category_id,
           'subcategory' : self.subcategory,
           'image_filename' : self.image_filename,
       }

engine = create_engine('sqlite:///productcatalog.db')

Base.metadata.create_all(engine)
