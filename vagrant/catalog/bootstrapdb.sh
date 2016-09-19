#!/bin/bash
# cleanup and rebuild database
# catalog is owned by me initially

rm productcatalog.db
python database_setup.py
python loadproductcatalog.py

# optional, if we need to scrape data from mec.ca again

#pushd "data/productdata"
#scrapy crawl product_catalog -o product_catalog.json
#popd

# download product images from mec.ca into static area
pushd static/images
cat ../../data/productdata/product_catalog.json | python -m json.tool | grep image_url | cut -f4 -d'"' | sed -e 's/,$//' | while read i ;do curl -O $i;done
popd

# we're all set!

