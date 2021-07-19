import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import random
import sqlite3
import time
import json
import re

urls = []

# initializing web browser.
option = webdriver.ChromeOptions()
option.add_argument("incognito")
option.add_argument("--disable-notifications")
option.add_argument("--start-maximized");
driver = webdriver.Chrome(executable_path='./chromedriver', options=option)

driver.get("https://www.propertyfinder.ae/en/buy/dubai/townhouses-for-sale.html")
time.sleep(3)

soup = BeautifulSoup(driver.page_source, "html.parser")
json_data = json.loads(soup.find_all("script", {"type": "application/ld+json"})[1].contents[0])


products = json_data[0].get("itemListElement")
for product in products:
    
    listing_url = product.get("url")
    print(listing_url)
    urls.append(listing_url)
    
for n in range(2, len(json_data)-1):
    listing_url = json_data[n].get("url")
    print(listing_url)
    urls.append(listing_url)

print(len(list(set(urls))))