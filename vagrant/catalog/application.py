from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, ProductCategory, CategoryItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import os

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Product Catalog Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///productcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Helper functions to use a local table for tracking users authorization


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# Maintenance page to test styles


@app.route('/test')
def testStyles():
    return render_template('teststyles.html')


# Landing page in case exceptions are caught


@app.route('/error')
def showErrorPage():
    return render_template('error.html')


@app.route('/login')
def showLogin():
    """ This function renders the login page and passes the current page
    to be forwarded to after successful login"""

    # Create anti-forgery state token
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    if request.referrer == "/login" or request.referrer == '/':
        next_url = "/catalog"
    else:
        next_url = request.referrer
    return render_template('login.html',
                           STATE=state,
                           next_url=next_url)


@app.route('/logout')
def doLogout():
    """This function handles the return code from gdisconnect
    and redirects back to the current page"""

    next_url = request.referrer
    if next_url == '/logout':
        next_url = "/catalog"
    else:
        next_url = request.referrer
    result = gdisconnect()
    if result.status_code == 200:
        flash('Successfully logged out.')
        return redirect(next_url)
    else:
        return render_template('error.html')

# Handle Google oauth authentication


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Google oauth authentication"""

    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    print "Current access token: ", stored_access_token
    stored_gplus_id = login_session.get('gplus_id')
    print "Current gplus id is: ", gplus_id
    print "Stored gplus id is: ", stored_gplus_id

    if stored_access_token is not None and gplus_id == stored_gplus_id:
        print "Current user is already connected."
        response = make_response(json.dumps('Current user is already \
            connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Adding user to local database (if necessary)
    dbuser_id = getUserID(login_session['email'])
    if dbuser_id is None:
        dbuser_id = createUser(login_session)
    login_session['user_id'] = dbuser_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 150px; height: 150px;border-radius: 150px;\
        -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """Logout by revoking Google oauth token and resetting user login_session
    object"""

    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # check token status
    print 'Verifying token', login_session['access_token']
    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % \
        login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')
    if (result[0]['status'] == '400' and
            json.loads(result[1])["error"] == 'invalid_token'):
        invalid_token = True

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200' or invalid_token:
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given'
                                            ' user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON end points to visualize product catalog information

@app.route('/catalog/JSON/')
def catalogJSON():
    """ Prints json data for all items in catalog.
    Query fields explicitly added to include product
    category in join query """
    catalog_items = session.query(
            CategoryItem.id,
            CategoryItem.name,
            CategoryItem.price,
            CategoryItem.description,
            CategoryItem.subcategory,
            CategoryItem.image_filename,
            ProductCategory.name.label('product_category')).\
        join(ProductCategory).order_by(asc(CategoryItem.id)).all()
    return jsonify(CatalogItems=catalog_items)


@app.route('/catalog/<int:product_category_id>/JSON')
def productCategoryIdJSON(product_category_id):
    """ Finds category name and forwards to json data generating
    function """
    try:
        product_category = session.query(ProductCategory).filter_by(
                id=product_category_id).one()
    except:
        return('No categories match such id')
    return redirect(url_for('productCategoryJSON',
                    product_category_name=product_category.name))


@app.route('/catalog/<path:product_category_name>/JSON')
def productCategoryJSON(product_category_name):
    """ Prints json data for all itms in a category """
    try:
        product_category = session.query(ProductCategory).filter_by(
            name=product_category_name).one()
    except:
        return ('No categories exist in database.')
    category_items = session.query(CategoryItem).filter_by(
        product_category_id=product_category.id).all()
    return jsonify(CategoryItems=[i.serialize for i in category_items])


@app.route('/catalog/<int:product_category_id>/<int:category_item_id>/JSON')
def categoryItemIdJSON(product_category_id, category_item_id):
    """ Finds category and items names from ids provided and forwards to
    to json data generating function """
    try:
        product_category = session.query(ProductCategory).filter_by(
            id=product_category_id).one()
        category_item = session.query(CategoryItem).filter_by(
            id=category_item_id, product_category_id=product_category_id).one()
    except:
        return('No categories match such id')
    return redirect(url_for('categoryItemJSON',
                            product_category_name=product_category.name,
                            category_item_name=category_item.name))


@app.route(
        '/catalog/<path:product_category_name>/<path:category_item_name>/JSON')
def categoryItemJSON(product_category_name, category_item_name):
    """ Prints json data for an item name in a category """
    try:
        product_category = session.query(
                              ProductCategory).filter_by(
                                      name=product_category_name).one()
        product_category_id = product_category.id
        print 'Category id ', product_category_id
        category_item = session.query(CategoryItem).filter_by(
                name=category_item_name,
                product_category_id=product_category_id).one()
    except:
        return ('No items found for such category')
    return jsonify(CategoryItem=category_item.serialize)


# Authentication and authorization helper functions

def isUserAuthenticated():
    return login_session.get('user_id') is not None


def isUserAuthorized(product_category_name, category_item_name):
    """ Verifies that the user in session has permissions to perform
    update or delete operations on an item, i.e. user in session is
    the owner of the item """
    item = session.query(CategoryItem).\
        filter_by(name=category_item_name,
                  product_category_id=session.query(
                                            ProductCategory.id).filter_by(
                                            name=product_category_name)).one()
    return login_session.get('user_id') == item.user_id


# READ routing


@app.route('/')
@app.route('/catalog/')
def showCatalog():
    """ Retrieves and invokes rendering of catalog product categories """
    categories = session.query(ProductCategory).\
        order_by(asc(ProductCategory.name)).all()
    return render_template('catalog.html', categories=categories)


@app.route('/catalog/<path:product_category_name>/')
def showCategory(product_category_name):
    """ Retrieves and invokes rendering of a catalog product category """
    try:
        category = session.query(ProductCategory).\
               filter_by(name=product_category_name).one()
        print 'product category ', category.name
        items = session.query(CategoryItem).\
            filter_by(product_category_id=category.id).all()
        return render_template('products.html', items=items, category=category)
    except Exception, e:
        print str(e)
        return ('Category requested not found')


@app.route('/catalog/<int:product_category_id>/')
def showCategoryId(product_category_id):
    """ Finds category name and forwards to function for retrieval
    and rendering of product category """
    try:
        category = session.query(ProductCategory).\
               filter_by(id=product_category_id).one()
        return redirect(url_for('showCategory',
                                product_category_name=category.name))
    except:
        return ('No items or category found for this request')


@app.route('/catalog/<path:product_category_name>/'
           '<path:category_item_name>')
def showCategoryItem(product_category_name, category_item_name):
    """ Retrieves and invokes rendering of a product item within a
    category """
    try:
        category = session.query(ProductCategory).\
               filter_by(name=product_category_name).one()
        print "Category id ", category.id
        item = session.query(CategoryItem).\
            filter_by(name=category_item_name,
                      product_category_id=category.id).one()
        if isUserAuthenticated() and isUserAuthorized(product_category_name,
                                                      category_item_name):
            return render_template('item.html', item=item, category=category)
        return render_template('publicitem.html', item=item, category=category)
    except Exception, e:
        print str(e)
        return ('No item for this category has been found')


@app.route('/catalog/<int:product_category_id>/<int:category_item_id>/')
def showCategoryItemId(product_category_id, category_item_id):
    """ Finds category and product names and forwards to function
    for retrieval and rendering of product item within a category"""
    try:
        category = session.query(ProductCategory).\
                filter_by(id=product_category_id).one()
        item = session.query(
            CategoryItem).filter_by(id=category_item_id,
                                    product_category_id=category.id).one()
        print 'Item id ', item.id
        return redirect(url_for('showCategoryItem',
                        product_category_name=category.name,
                        category_item_name=item.name))
    except Exception, e:
        print "Exception ", str(e)
        return ('No item matching this category found')


# CREATE / UPDATE routing

@app.route('/catalog/<path:product_category_name>/new/',
           methods=['GET', 'POST'])
def newCategoryItem(product_category_name):
    """ Create a new item in a category """
    try:

        if not isUserAuthenticated():
            flash("You're not authorized to add items!")
            return redirect(url_for('showCategory',
                            product_category_name=product_category_name))
        if request.method == 'POST':
            # check if item name exists already in category
            print "Name: ", request.form['name']
            product_category = session.query(ProductCategory).filter_by(
                                            name=product_category_name).one()
            print "Product id: ", product_category.id
            checkitem = session.query(CategoryItem).\
                filter_by(name=request.form['name'],
                          product_category_id=product_category.id).first()
            if checkitem:
                flash('Item with that name already exists in database'
                      ' and cannot be added.')
                return redirect(url_for('newCategoryItem',
                                product_category_name=product_category_name))
            newItem = CategoryItem(name=request.form['name'],
                                   user_id=login_session['user_id'],
                                   price=request.form['price'],
                                   description=request.form['description'],
                                   subcategory=request.form['subcategory'],
                                   product_category_id=product_category.id)
            session.add(newItem)
            session.commit()
            flash('New item has been added to category')
            return redirect(url_for('showCategoryId',
                            product_category_id=product_category.id))
        else:
            category = session.query(ProductCategory).\
                    filter_by(name=product_category_name).one()
            return render_template('newitem.html', category=category)
    except Exception, e:
        print 'Exception ', str(e)
        return ('No category can be found to add item.')


@app.route('/catalog/<int:product_category_id>/<int:category_item_id>/edit/')
def editCategoryItemId(product_category_id, category_item_id):
    """ Finds category and item name then forwards to function for
    item edit and update """
    try:
        print 'Is user logged in:', login_session.get('user_id')
        if not isUserAuthenticated():
            flash("You're not authorized to edit this item!")
            return redirect(url_for('showCategoryItemId',
                            product_category_id=product_category_id,
                            category_item_id=category_item_id))
        category = session.query(ProductCategory).\
            filter_by(id=product_category_id).one()
        item = session.query(CategoryItem).\
            filter_by(id=category_item_id,
                      product_category_id=category.id).one()
        return redirect(url_for('editCategoryItem',
                        product_category_name=category.name,
                        category_item_name=item.name))
    except Exception, e:
        print "Exception ", str(e)
        return ('No item matching this category found')


@app.route('/catalog/<path:product_category_name>/'
           '<path:category_item_name>/edit/', methods=['GET', 'POST'])
def editCategoryItem(product_category_name, category_item_name):
    """ Edit an item belonging to a category """
    try:
        # check if user is authenticated
        if not isUserAuthenticated():
            flash("You're not logged in to edit items!")
            return redirect(url_for('showCategoryItem',
                            product_category_name=product_category_name,
                            category_item_name=category_item_name))

        # check if user is authorized
        if not isUserAuthorized(product_category_name, category_item_name):
            flash("You're not allowed to edit this item.")
            return redirect(url_for('showCategoryItem',
                            product_category_name=product_category_name,
                            category_item_name=category_item_name))

        # process form
        if request.method == 'POST':
            product_category = session.query(ProductCategory).filter_by(
                                            name=product_category_name).one()
            if (request.form['name'] and
                    category_item_name != request.form['name']):
                checkitem = session.query(CategoryItem).\
                        filter_by(
                            name=request.form['name'],
                            product_category_id=product_category.id).first()
                if checkitem:
                    flash('Item with that name already'
                          ' exists in database and cannot be added')
                    return render_template(
                            'edititem.html',
                            category=product_category,
                            item=checkitem)
            item_update = session.query(CategoryItem).\
                filter_by(name=category_item_name,
                          product_category_id=product_category.id).one()
            if request.form['name']:
                item_update.name = request.form['name']
            if request.form['price']:
                item_update.price = request.form['price']
            if request.form['subcategory']:
                item_update.subcategory = request.form['subcategory']
            if request.form['description']:
                item_update.description = request.form['description']
            session.commit()
            flash('Item updated successfully')
            return redirect(url_for('showCategoryItemId',
                            product_category_id=product_category.id,
                            category_item_id=item_update.id))
        else:
            category = session.query(ProductCategory).\
                filter_by(name=product_category_name).one()
            item_update = session.query(CategoryItem).\
                filter_by(name=category_item_name,
                          product_category_id=category.id).one()
            return render_template('edititem.html', category=category,
                                   item=item_update)
    except Exception, e:
        print 'Exception ', str(e)
        return ('No category can be found to edit item.')


# DELETE routing

@app.route('/catalog/<int:product_category_id>/<int:category_item_id>/delete/')
def deleteCategoryItemId(product_category_id, category_item_id):
    """ Find category and product name and forwards to function for
    deletion """
    try:
        # check if user is authenticated
        if not isUserAuthenticated():
            flash("You're not logged in to delete items!")
            return redirect(url_for('showCategoryItemId',
                            product_category_id=product_category_id,
                            category_item_id=category_item_id))
        category = session.query(ProductCategory).\
            filter_by(id=product_category_id).one()
        item = session.query(CategoryItem).\
            filter_by(id=category_item_id,
                      product_category_id=category.id).one()
        return redirect(url_for('deleteCategoryItem',
                        product_category_name=category.name,
                        category_item_name=item.name))
    except Exception, e:
            print "Exception", str(e)
            return('No item matching this category found.')


@app.route('/catalog/<path:product_category_name>/'
           '<path:category_item_name>/delete/', methods=['GET', 'POST'])
def deleteCategoryItem(product_category_name, category_item_name):
    """ Delete item from a category """
    try:
        # check if user is authenticated

        if not isUserAuthenticated():
            flash("You're not logged in to delete items!")
            return redirect(url_for('showCategoryItem',
                            product_category_name=product_category_name,
                            category_item_name=category_item_name))

        # check if user is authorized
        if not isUserAuthorized(product_category_name, category_item_name):
            flash("You're not allowed to delete this item.")
            return redirect(url_for('showCategoryItem',
                            product_category_name=product_category_name,
                            category_item_name=category_item_name))

        if request.method == 'POST':
            item_delete = session.query(CategoryItem).\
                filter_by(name=category_item_name,
                          product_category_id=session.
                          query(ProductCategory.id).filter_by(
                              name=product_category_name)).one()
            session.delete(item_delete)
            session.commit()
            flash('Item has been successfully deleted.')
            return redirect(url_for('showCategory',
                            product_category_name=product_category_name))
        else:
            item_delete = session.query(CategoryItem).\
                filter_by(name=category_item_name,
                          product_category_id=session.
                          query(ProductCategory.id).filter_by(
                              name=product_category_name)).one()
            return render_template('deleteitem.html', item=item_delete)
    except Exception, e:
        print 'Exception', str(e)
        return ('No item can be found for deletion.')


# application execution entry point


if __name__ == '__main__':
    app.secret_key = os.urandom(32)
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
