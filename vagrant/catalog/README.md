#Product catalog v0.1
Catalog management application implemented using Flask and sqlalchemy.
Product information used in this project can be found at http://www.mec.ca

## 1. Running the application

```
cd /vagrant/catalog # code should be checked out here
chmod u+x bootstrap.sh # make script executable
./bootstrap.sh # initialize database
python application.py # start application
```

## 1. Contents
```
catalog
+-- application.py - main application 
+-- bootstrap.sh - shell script to rewrite database with data and download product image
+-- checkuserdatabase.py -- maintenance script to verify user_table contents
+-- client_secrets.json -- Google client authentication data
+-- database_setup.py -- ORM database definition
+-- loadproductcatalog.py -- script to insert values from json catalog file
+-- productcatalog.db -- database data file
+-- README.md -- this document
+-- static -- static data
|   +-- images -- product image files
|   |   +-- comingsoong.jpg -- image placeholder if image not available
|   +-- style.css -- catalog stylesheet
+-- templates -- Flask template files
|   |   +-- layout.html -- main template
|   |   +-- catalog.html -- render all product categories
|   |   +-- gheaders.html -- javascript includes for Google signin
|   |   +-- gbutton.html -- html/js code to render and action Google signin button
|   |   +-- login.html -- login welcome page
|   |   +-- products.html -- render category products
|   |   +-- publicitem.html -- render item for view only
|   |   +-- item.html -- render item for edit/delete
|   |   +-- newitem.html -- render new item page
|   |   +-- edititem.html -- render edit item page
|   |   +-- flash.html -- application notifications placeholder
|   |   +-- teststyles.html -- maintenance page to test styles
|   |   +-- error.html -- fallback page in case application handles an exception
+-- data -- data scraping and preparation
|   |   +-- productdata -- scrapy project to build data from mec.ca
|   |   |   +-- product_catalog.json -- generated product data to bootstrap application
```

## 2. Database design

* Every item is linked to its respective category.
* There could be two categories that have the same item name.
* Category names are unique.
* Item names are unique within its own category.

## 3. Routing

* Categories and items within them can be referred by id. The will be routed to its respective names
* Login and logout functionality is available in all pages (except error page)
* Login and logout actions are redirected to current page navigation

## 4. Data endpoints

* JSON output is available at the catalog level (all items), category level (one category), and item level (single item)

## 5. Future enhancements

* When adding new items, an image placeholder is added; a future enhancement would be to add image upload to the database

