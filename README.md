# scrapy_quote
爬取quotes所有的作者
#还是以scrapy基础教程中的爬虫为例

##tag:love

[tag_love](http://quotes.toscrape.com/tag/love/)

[scrapy教程](https://scrapy-chs.readthedocs.io/zh_CN/1.0/intro/tutorial.html#spider)

注意要在根目录下运行
`scrapy crawl "name"`

love_spider:

```python
import scrapy
from love_spd.items import LoveSpdItem

class Lovespider(scrapy.Spider):
	name = "love"
	start_urls = ["http://quotes.toscrape.com/tag/love/"]


	def parse(self, response):
		group = response.xpath('//div[@class = "quote"]')
		for pattern in group:
			item = LoveSpdItem()
			item['article'] = pattern.xpath('./span[@class = "text"]/text()').extract()
			item['author'] = pattern.xpath('./span/small/text()').extract()
			item['tags'] = pattern.xpath('./div//a/text()').extract()
			yield item
			# article = pattern.xpath('./span[@class = "text"]/text()').extract()
			# author = pattern.xpath('./span/small/text()').extract()
			# tags = pattern.xpath('./div//a/text()').extract()
			# print(article, author, tags)
```

输出了一个json保存，但是只包含了第一页，今天的目标是利用一个新的parse进行request，然后再调用这个保存`article`，`author`，`tags`的

换页在：

`/html/body/div/div[2]/div[1]/nav/ul`

如果`class = "previous"`，则表示无下一页

如果`class = "next"`，则表示有下一页

`<a href="/tag/love/page/2/">`

Spider类定义了如何爬取某个(或某些)网站。包括了爬取的动作(例如:是否跟进链接)以及如何从网页的内容中提取结构化数据(爬取item)。 换句话说，Spider就是您定义爬取的动作及分析某个网页(或者是有些网页)的地方。

```
对spider来说，爬取的循环类似下文:

1. 以初始的URL初始化Request，并设置回调函数。 当该request下载完毕并返回时，将生成response，并作为参数传给该回调函数。

2. spider中初始的request是通过调用 start_requests() 来获取的。 start_requests() 读取 start_urls 中的URL， 并以 parse 为回调函数生成 Request 。
在回调函数内分析返回的(网页)内容，返回 Item 对象、dict、 Request 或者一个包括三者的可迭代容器。 返回的Request对象之后会经过Scrapy处理，下载相应的内容，并调用设置的callback函数(函数可相同)。
3. 在回调函数内，您可以使用 选择器(Selectors) (您也可以使用BeautifulSoup, lxml 或者您想用的任何解析器) 来分析网页内容，并根据分析的数据生成item。
4. 最后，由spider返回的item将被存到数据库(由某些 Item Pipeline 处理)或使用 Feed exports 存入到文件中。
```

现在的想法就是把`href`的内容弄出来，把url拼接，然后发送请求，继续爬。

`response.xpath('//*[@class = "next"]').xpath('./a/@href').extract_first() `

得到`href`内容`/tag/love/page/2/`

[参考这里](https://www.cnblogs.com/zxfei/p/12064378.html)


拼接咋办？request.urlopen

`http://quotes.toscrape.com/tag/love/`
`http://quotes.toscrape.com/tag/love/page/2/`

```python
In [3]: strrr                                                                          
Out[3]: '/tag/love/page/2/'

In [4]: strrr.split('/', 2)                                                            
Out[4]: ['', 'tag', 'love/page/2/']

In [5]: strrr.split('/', 2)[-1]                                                        
Out[5]: 'love/page/2/'


```

蜜汁报错：
`#TypeError: urljoin() takes 2 positional arguments but 3 were given
`

为什么说给了3个参数呢？

太坑了，这个用法类似于C++了，不是response.url已经包含在内部了，urljoin后面跟的是需要添加的参数。。。
`response.urljoin(response.url, ''/tag/love/page/2/'')`
`response.urljoin(''/tag/love/page/2/'')`

第一页爬不了了……还是想要callback，不想放在一个parse里面，无解，直接写吧

就这样吧

```python
import scrapy
from love_spd.items import LoveSpdItem

class Lovespider(scrapy.Spider):
	name = "love"
	start_urls = ["http://quotes.toscrape.com/tag/love/"]
	start = "next"
	end = "previous"

	def parse(self, response):
		pager = response.xpath('//ul[@class = "pager"]')
		if pager.xpath('./li[@class = "next"]'):
			group = response.xpath('//div[@class = "quote"]')
			for pattern in group:
				item = LoveSpdItem()
				item['article'] = pattern.xpath('./span[@class = "text"]/text()').extract_first()
				item['author'] = pattern.xpath('./span/small/text()').extract_first()
				item['tags'] = pattern.xpath('./div//a/text()').extract()
				yield item
			next_page = pager.xpath('.//a/@href').extract_first()
			url = response.urljoin(next_page)
			yield scrapy.Request(url)
			#yield scrapy.Request(url, callback = parse_dir_contents)
		


	def parse_dir_contents(self, response):
		group = response.xpath('//div[@class = "quote"]')
		for pattern in group:
			item = LoveSpdItem()
			item['article'] = pattern.xpath('./span[@class = "text"]/text()').extract_first()
			item['author'] = pattern.xpath('./span/small/text()').extract_first()
			item['tags'] = pattern.xpath('./div//a/text()').extract_first()
			yield item
			# article = pattern.xpath('./span[@class = "text"]/text()').extract()
			# author = pattern.xpath('./span/small/text()').extract()
			# tags = pattern.xpath('./div//a/text()').extract()
			# print(article, author, tags)		

##ERROR: Spider error processing <GET http://quotes.toscrape.com/tag/love/> (referer: None)
#url = response.urljoin(response.url, next_page_num)
#TypeError: urljoin() takes 2 positional arguments but 3 were given

```

别人的写法：

这个是把整个扒下来，不仅仅是扒love的内容

```python
import scrapy


class ToScrapeSpiderXPath(scrapy.Spider):
    name = 'toscrape-xpath'
    start_urls = [
        'http://quotes.toscrape.com/',
    ]

    def parse(self, response):
        for quote in response.xpath('//div[@class="quote"]'):
            yield {
                'text': quote.xpath('./span[@class="text"]/text()').extract_first(),
                'author': quote.xpath('.//small[@class="author"]/text()').extract_first(),
                'tags': quote.xpath('.//div[@class="tags"]/a[@class="tag"]/text()').extract()
            }

        next_page_url = response.xpath('//li[@class="next"]/a/@href').extract_first()
        if next_page_url is not None:
            yield scrapy.Request(response.urljoin(next_page_url))
```

恭喜你，好像掌握了最简单的爬虫技巧，但是，如果要登陆账号，你就没辙了，还有发送请求，进行响应，你就完了。

**拓展request:**
爬取每一个作者的信息，基本的思路应该就是从根目录出发，建立一个dict，思路应该差不多。

[比如爱因斯坦](http://quotes.toscrape.com/author/Albert-Einstein/)

`<h3 class="author-title">Albert Einstein</h3>`
`<span class="author-born-date">March 14, 1879</span>`
`<span class="author-born-location">in Ulm, Germany</span>`
`<div class="author-description">.....</div>`

```python
import scrapy

from author_inf.items import AuthorInfItem

class Authorspider(scrapy.Spider):
	name = "author"
	start_urls = ["http://quotes.toscrape.com"]


	def parse(self, response):
		collect = response.xpath('//div[@class = "quote"]')
		for part in collect:
			author_page = part.xpath('./span/a/@href').extract_first()
			author_url = response.urljoin(author_page)
			yield scrapy.Request(author_url, callback = self.parse_content)

		if response.xpath('//ul[@class = "pager"]').xpath('./li[@class = "next"]'):
			next_page = response.xpath('//ul[@class = "pager"]').xpath('.//a/@href').extract_first()
			next_url = response.urljoin(next_page)
			yield scrapy.Request(next_url)

	def parse_content(self, response):
		item = AuthorInfItem()
		item['name'] = response.xpath('//h3[@class = "author-title"]/text()').extract_first()
		item['Birth'] = response.xpath('//span[@class = "author-born-date"]/text()').extract_first()
		item['Born_in'] = response.xpath('//span[@class = "author-born-location"]/text()').extract_first()
		item['Descrip'] = response.xpath('//div[@class = "author-description"]/text()').extract_first()
		yield item
```
只返回了部分，原因不明，有时间再看哪里出了问题

>这里展现的即是Scrpay的追踪链接的机制: 当您在回调函数中yield一个Request后, Scrpay将会调度,发送该请求,并且在该请求完成时,调用所注册的回调函数。

>基于此方法,您可以根据您所定义的跟进链接的规则,创建复杂的crawler,并且, 根据所访问的页面,提取不同的数据.

>一种常见的方法是,回调函数负责提取一些item,查找能跟进的页面的链接, 并且使用相同的回调函数yield一个 Request:

为什么只爬了两页，肯定跟循环条件结束有关。

不行的原因是，`if`判断出错了。。。

之前担心过的问题还是出现了，空列表`[]`也会被`if`判断为`True`

```python
if response.xpath('//li[@class = "next"]') is not None:
			next_page = response.xpath('//li[@class = "next"]').xpath('./a/@href').extract_first()
			next_url = response.urljoin(next_page)
			print("Next Page is : {}".format(next_page))
			yield scrapy.Request(next_url, callback = self.parse)
```

怪问题又来了，现在又不能保存json了。

`yield`要加
