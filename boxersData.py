# -*- coding: utf-8 -*-
import scrapy
import re
import csv


class BoxersdataSpider(scrapy.Spider):
    name = 'boxersData'
    allowed_domains = ['boxrec.com']
    start_urls = ['http://boxrec.com/en/login']

    def parse(self, response):
        print("parsing url " + response.url)
        # log in to boxrec.com to bypass requests limit
        return scrapy.FormRequest('http://boxrec.com/en/login',
                                  formdata={'_username': 'username', '_password': 'password'},
                                  callback=self.after_login
        )

    def after_login(self, response):
        # check if login worked, if so start extracting data about boxers from ratings subpage
        if "authentication failed" in str(response.body):
            self.logger.error("Login failed")
            print('Login failed')
            return
        yield response.follow("http://boxrec.com/en/ratings?BlL%5Bcountry%5D=&BlL%5Bdivision%5D=&BlL%5Bsex%"
                              "5D=M&BlL%5Bstance%5D=&BlL%5Bstatus%5D=&r_go=", self.parse_pages)

    def parse_pages(self, response):
        print("Parsing authenticated url " + response.url)
        # get boxers ids
        boxers = response.xpath('//a[contains(@href, "/en/boxer/")]').extract()
        for boxer in boxers:
            # process boxers sites with 'parse_boxer' function
            yield response.follow('http://boxrec.com/en/boxer' + re.search("/\d+", boxer).group(), self.parse_boxer)

        # get inforamtion from 'next page' button
        next_page = response.xpath('//div[contains(@class, "tableInfoBottom")]/div/div[last()]/a').extract()
        try:
            next_page = re.search("href.+onclick", str(next_page)).group()[6:-9]
        except AttributeError:
            return

        # delete 'amp;' characters
        next_page = next_page.replace("amp;", "")
        # go to the next page
        yield response.follow("http://boxrec.com/en/" + next_page, self.parse_pages)

    def parse_boxer(self, response):
        # extract name of the boxer
        name = response.xpath('//td[contains(@class, "defaultTitleAlign")]/h1').extract()
        # remove '<' and '>' from extracted name
        name = re.search('>.*<', str(name)).group()[1:-1]
        print(name)
        # extract data from site of the boxer
        data = str(response.xpath('//table[contains(@class, "rowTable")]').extract())
        # extract height and reach if available
        if data.__contains__('height') and data.__contains__('reach'):
            height, reach = re.findall('\d\d\dcm', data)
        elif data.__contains__('height'):
            height = re.findall('\d\d\dcm', data)[0]
            reach = '0cm'
            print('Only height parameter. Saving')
        elif data.__contains__('reach'):
            reach = re.findall('\d\d\dcm', )[0]
            height = '0cm'
            print('Only reach parameter. Saving.')
        else:
            print('No reach and height parameter. Aborting')
            return

        # extract division
        division = re.search('[a-zA-z]* *[a-zA-z]+weight', data).group()
        # extract wins
        wins = response.xpath('//td[contains(@class, "bgW")]').extract()
        wins = re.search('>\d+<', str(wins)).group()[1:-1]
        # extract win KOs
        win_KOs = response.xpath('//th[contains(@class, "textWon")]').extract()
        win_KOs = re.search('>\d+ KOs<', str(win_KOs)).group()[1:-5]
        # extract loses
        loses = response.xpath('//td[contains(@class, "bgL")]').extract()
        loses = re.search('>\d+<', str(loses)).group()[1:-1]
        # extract loses KOs
        loses_KOs = response.xpath('//th[contains(@class, "textLost")]').extract()
        loses_KOs = re.search('>\d+ KOs<', str(loses_KOs)).group()[1:-5]
        # extract draws
        draws = response.xpath('//td[contains(@class, "bgD")]').extract()
        draws = re.search('>\d+<', str(draws)).group()[1:-1]

        # save to 'boxers.csv' file
        with open('boxers.csv', 'a', newline='') as csvfile:
            boxer_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            boxer_writer.writerow([name, height, reach, wins, win_KOs, loses, loses_KOs, draws, division])

