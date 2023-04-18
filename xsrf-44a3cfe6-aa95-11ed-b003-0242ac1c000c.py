import scrapy
import json
# It seems like this reference is wrong but due to the different invocation of scrapy it is right
from scrapers.scrapy_couchcrawl.helpers.profileLinkExtractor import KeyExtractor
#from selenium import webdriver


class FetchProfileKeysSpider(scrapy.Spider):
    name = "fetch_profiles"
    login_url = "https://www.couchsurfing.com/users/sign_in"
    login_user = "q1686061@mvrht.net"
    login_password = "3R3fk*CP"

    login_data = {
        "user[login]": login_user,
        "user[password]": login_password,
    }

    custom_settings = {
        'ITEM_PIPELINES': {
            'scrapy_couchcrawl.pipelines.ProfilesPipeline': 400,
        },
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 60,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'AUTOTHROTTLE_DEBUG': True,
    }

    # To be used for request debugging with local proxy; add as request parameter
    # meta={'proxy': 'http://127.0.0.1:8080'}

    # On what subject should be iterated?
    def start_requests(self):
        yield scrapy.Request(self.login_url, self.parse_login)

    def parse_login(self, response):
        # Send the request with our login data
        print("Login")
        print(response.url)
        yield scrapy.FormRequest.from_response(response, formdata=self.login_data, callback=self.start_crawl)

    def start_crawl(self, response):
        print("Start Crawl")
        print(response.url)
        key_extractor = KeyExtractor()

        # Iteration on all ProfileLinks
        # Some of these links are not accessible without login
        while key_extractor.hasMoreProfileLinks():
            links = key_extractor.getMoreProfileLinks()
            for link in links:

                about_link = link
                couch_link = link + "/couch"
                photos_link = link + "/photos"
                references_link = link + "/references"
                friends_link = link + "/friends"
                favorites_link = link + "/favorites"

                link_list = [about_link, couch_link, photos_link, references_link, friends_link, favorites_link]

                for sub_link in link_list:
                    yield scrapy.Request(url=sub_link, callback=self.parse)

    def parse(self, response):
        url_parts = response.url.split("/")

        if len(url_parts)==5:
            print("Mainpage")
            page_name = "Main"
            profile_name = url_parts[len(url_parts) - 1]
        else:
            print("Not Mainpage")
            page_name = url_parts[len(url_parts)-1]
            profile_name = url_parts[len(url_parts) - 2]

        websites = {"_id": profile_name, "URL":response.url, page_name:response.body.decode("utf-8")}
        yield {'websites': websites}



        #  def parse_
        #
        #       https: // www.couchsurfing.com / people / goodpennyworths / references?experience = all & per_page = 100 & type = host
