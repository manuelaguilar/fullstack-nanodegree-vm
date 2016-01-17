from scrapy import Spider
from scrapy.selector import Selector
from scrapy.loader import ItemLoader
from atp_rankings.items import AtpRankedPlayer

class AtpRankingsSpider(Spider):
	name="atp_rankings"
	start_urls = [
		"http://www.atpworldtour.com/en/rankings/singles"
		]
	
	def parse(self, response):
		#//*[@id="rankingDetailAjaxContainer"]/table/tbody/tr[1]
		rankings_table = Selector(response).xpath("//*[@id='rankingDetailAjaxContainer']/table/tbody/tr[position() <= 17]")
		#//*[@id="rankingDetailAjaxContainer"]/table/tbody/tr[1]/td[4]/a
		#//*[@id="rankingDetailAjaxContainer"]/table/tbody/tr[1]/td[5]
                #loader = ItemLoader(item=AtpRankedPlayer(),selector=rankings_table)
		#loader.add_xpath('player',"td[4]/a/text()")
		#loader.add_xpath('age',"td[5]/text()")
		#loader.add_xpath('points',"td[6]/a/text()") 
		for player in rankings_table:
			yield {
			'player': player.xpath("td[4]/a/text()").extract(),
			'age' : player.xpath("td[5]/text()").extract(),
			'points' : player.xpath("td[6]/a/text()").extract()
		}
		#	print "PLAYER: " + player_name[0].strip() + "\t AGE: " + age[0].strip() + "\t POINTS: " + points[0].strip() 
		#print "Loaded: " 
		#print loader.load_item()

