import scrapy

from author_inf.items import AuthorInfItem

class Authorspider(scrapy.Spider):
	name = "author"
	start_urls = ["http://quotes.toscrape.com"]


	def parse(self, response):
		collect = response.xpath('//div[@class = "quote"]')
		#找到作者信息页
		for part in collect:
			author_page = part.xpath('./span/a/@href').extract_first()
			author_url = response.urljoin(author_page)
			yield scrapy.Request(author_url, callback = self.parse_content)
		#下一页内容	
		if response.xpath('//li[@class = "next"]') is not None:
			next_page = response.xpath('//li[@class = "next"]').xpath('./a/@href').extract_first()
			next_url = response.urljoin(next_page)
			print("Next Page is : {}".format(next_page))
			yield scrapy.Request(next_url, callback = self.parse)

	def parse_content(self, response):
		item = AuthorInfItem()
		name = response.xpath('//h3[@class = "author-title"]/text()').extract_first().rstrip()
		Birth = response.xpath('//span[@class = "author-born-date"]/text()').extract_first()
		Born_in = response.xpath('//span[@class = "author-born-location"]/text()').extract_first()
		Descrip = response.xpath('//div[@class = "author-description"]/text()').extract_first().strip()
		item['name'] = name
		item['Birth'] = Birth
		item['Born_in'] = Born_in
		item['Descrip'] = Descrip
		yield item