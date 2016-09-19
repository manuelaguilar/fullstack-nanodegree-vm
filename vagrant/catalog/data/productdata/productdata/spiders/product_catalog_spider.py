import scrapy
from scrapy import Spider
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from scrapy.utils.response import get_base_url
from productdata.items import ProductDataItem

class ProductCatalogSpider(Spider):
    name="product_catalog"
    start_urls = [
            "https://www.mec.ca/en/ideal-for/snowsports/products/gear/snowboarding/backcountry-snowboards/c/1425?q=%3Asales-rank",
            "https://www.mec.ca/en/ideal-for/snowsports/products/gear/snowboarding/backcountry-snowboard-bindings/c/1420?q=%3Asales-rank",
            "https://www.mec.ca/en/ideal-for/snowsports/products/gear/snowboarding/backcountry-snowboard-skins/c/1423?q=%3Asales-rank",
            "https://www.mec.ca/en/ideal-for/snowsports/products/gear/snowboarding/backcountry-snowboard-boots/c/1421?q=%3Asales-rank",
            "https://www.mec.ca/en/products/gear/sleeping-bags%2c-sleeping-pads%2c-quilts-and-pillows/sleeping-bags/c/1410?q=%3Asales-rank",
            "https://www.mec.ca/en/products/gear/sleeping-bags%2c-sleeping-pads%2c-quilts-and-pillows/sleeping-pads/c/1416?q=%3Asales-rank",
            "https://www.mec.ca/en/products/gear/sleeping-bags%2c-sleeping-pads%2c-quilts-and-pillows/sleeping-pad-accessories/c/1415?q=%3Asales-rank",
            "https://www.mec.ca/en/ideal-for/watersports/products/gear/boats-and-boards/kayaks/touring-kayaks/c/913?q=%3Asales-rank",
            "https://www.mec.ca/en/ideal-for/watersports/products/gear/boats-and-boards/kayaks/recreational-kayaks/c/916?q=%3Asales-rank",
            "https://www.mec.ca/en/ideal-for/watersports/products/gear/boats-and-boards/kayaks/whitewater-kayaks/c/920?q=%3Asales-rank"
            ]

    def parse(self, response):
        print "*** TEST PARSE ***"
        #product_section = Selector(response).xpath("//div[contains(@class, 'flexigrid__tile__content')]")
        #product_section = Selector(response).xpath("//div[contains(@class, 'flexigrid__tile')]")
        product_section = Selector(response).xpath("//div[contains(@itemtype, 'http://schema.org/Product')"
                " and position() <=5]")
        for item in product_section:
            name = item.xpath("div[1]/div/p/a/span/text()").extract_first()
            price = item.xpath("div[1]/ul[@class='price-group']//"
                    "span[@itemprop='price' or @itemprop='lowPrice']/text()").extract_first()
            #category = item.xpath("//div[@id='facetGroup']//"
            #    "li[@class='list__item'][0]/a/text()").extract()
            category = item.xpath("//div[@id='facetGroup']//ul[@class='list list--tree list--active ']"
                        "/li/ul/li/a/text()").extract_first()
            subcategory = item.xpath("//h1[@class='page-title']/text()").extract_first()
            image_url = item.xpath("div[1]//div[@class='product__image fluid-image fluid-image--1x1']"
                "/img/@data-high-res-src").extract_first()
            product_url = item.xpath("div[1]//a[contains(@class, 'product__name__link')]/@href").extract_first()
            item_data = ProductDataItem()
            item_data['name'] = name
            item_data['price'] = price
            item_data['category'] = category
            item_data['subcategory'] = subcategory
            item_data['image_url'] = image_url
            description = yield scrapy.Request(response.urljoin(product_url), callback=self.parse_description,
                    meta={'item_data':item_data}) 
            #description = Selector(description_request).xpath("//div[@id='pdp-description']/p/text()").extract_first()
            #print price
            #if not price:
            #    price = item.xpath("div[1]/ul[contains(@class, 'price-group')]/li/span[3]/span[1]/text()").extract()
                #print price
            #yield {
            #'name' : item.xpath("div[1]/div/p/a/span/text()").extract(),
            #'price' : price,
            #'image_url' : image_url,
            #'description' : description 
            #}

    def parse_description(self, response):
        item = response.meta['item_data']
        description = Selector(response).xpath("//div[@id='pdp-description']/p/text()").extract_first()
        #print "Description", description
        yield {
                'name' : item['name'],
                'price' : item['price'],
                'category' : item['category'],
                'subcategory' : item['subcategory'],
                'image_url' : item['image_url'],
                'description' :description,
        }

