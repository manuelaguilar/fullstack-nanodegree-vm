from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, ProductCategory, CategoryItem, User
import json

engine = create_engine('sqlite:///productcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Admin user

adminuser = User(name='Admin', email='manuel.aguilar.alvarez@gmail.com',
                 picture='https://pbs.twimg.com/profile_images/2671170543/'
                 '18debd694829ed78203a5a36dd364160_400x400.png')
session.add(adminuser)
session.commit()

# reload admin user
adminuser = session.query(User).filter_by(name='Admin').one()

# Load catalog json data and populate categories and items

catalog_file = open('data/productdata/product_catalog.json', 'r')
catalog_data = catalog_file.read()
product_catalog_json = json.loads(catalog_data)
catalog_file.close()


for item in product_catalog_json:
    # check if category exists
    category = session.query(ProductCategory).filter_by(
            name=item['category']).first()
    if not category:
        newCategory = ProductCategory(name=item['category'],
                                      user_id=adminuser.id)
        session.add(newCategory)
        session.commit()
    category = session.query(ProductCategory).filter_by(
                            name=item['category']).one()
    name = item['name']
    image_filename = item['image_url'].rsplit('/', 1)[1]
    price = item['price']
    subcategory = item['subcategory']
    description = item['description']

    newitem = CategoryItem(name=name, price=price, subcategory=subcategory,
                           description=description,
                           product_category_id=category.id,
                           user_id=adminuser.id,
                           image_filename=image_filename)

    session.add(newitem)
    session.commit()
