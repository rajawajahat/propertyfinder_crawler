import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import random
import sqlite3
import time
import re


# Headers.
headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'referrer': 'https://google.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Pragma': 'no-cache',
    }


# categories lookup dictionary.
categories_dic = {"buy": "https://www.propertyfinder.ae/en/buy/properties-for-sale.html",
              "rent": "https://www.propertyfinder.ae/en/rent/properties-for-rent.html",
              "commercial buy": "https://www.propertyfinder.ae/en/commercial-buy/properties-for-sale.html",
              "commercial rent": "https://www.propertyfinder.ae/en/commercial-rent/properties-for-rent.html"
    }


def get_proxies():
    
    """
    This method extract the available free proxies from
    https://free-proxy-list.net/ and return
    a list of proxies.
    """
    proxy_list = []
    res = requests.get('https://free-proxy-list.net/', headers=headers)
    soup = BeautifulSoup(res.text,"lxml")
    for items in soup.select("#proxylisttable tbody tr"):
        proxy_list.append(':'.join([item.text for item in items.select("td")[:2]]))
    return proxy_list


def pick_random(proxies):
    
    """
    This method select and then return the 
    random proxy from the list of proxies.
    """
    random_proxy = None
    if proxies:
        random_proxy = proxies[random.randint(0, len(proxies) - 1)]
    return random_proxy


def get_listing_urls(driver, category, category_url):
    
    """
    This method extracting the listing url from all the pages
    of the specified category. It returns the list of
    urls of the listing and their categories.
    """
    
    listing_urls = []
    listing_categories = []
    
    final_urls = deep_search(driver, category_url)
    # print(f"Urls By Each Link: {len(final_urls)}")
    
    for final_url in final_urls:
    
        driver.get(final_url)
        time.sleep(3)
        while True:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            for link in soup.find_all("a", {"class": "card card--clickable"}):
                listing_urls.append(link.get("href"))
                listing_categories.append(category)
            try:
                driver.find_element_by_class_name("pagination__link.pagination__link--next").click()
                time.sleep(3)
            except:
                break      
    return listing_urls, listing_categories


def create_table():
    
    """
    This method creating The table if don't exist, then 
    creating table.
    """
    
    try:
        sqliteConnection = sqlite3.connect('listings.db')
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        sqlite_create_table_query= """ CREATE TABLE Listings 
                                    (id integer primary key autoincrement,
                                    category varchar(30),
                                    url varchar(200));"""

        cursor.execute(sqlite_create_table_query)
        sqliteConnection.commit()
        print("Table Has been Created")

    except sqlite3.Error as error:
        print("Failed to Connect: ", error)

    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("The SQLite connection is closed")

            
def insert_data(records):
    
    """
    This method inserting data into the table.
    """
    
    try:
        sqliteConnection = sqlite3.connect('listings.db')
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        cursor.executemany("insert into Listings(category, url) values (?,?)", records)
        sqliteConnection.commit()
        print("Records Have Been Inserted")
        cursor.close()

    except sqlite3.Error as error:
        print("Error While Inserting Records: ", error)
        cursor.close()
        

def deep_search(driver, category_url):

    final_urls = []
    backlog_urls = []

    driver.get(category_url)
    time.sleep(6)

    fetch_underlying_urls(driver, backlog_urls, final_urls)
    while backlog_urls:

        target_url = backlog_urls.pop()
        driver.get(target_url)
        time.sleep(6)

        fetch_underlying_urls(driver, backlog_urls, final_urls)
        
    return final_urls


def fetch_underlying_urls(driver, backlog_urls, final_urls):
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    divs = soup.find_all("div", {"class": "breadcrumb-serp__list-item"})

    for div in divs:
        count = int(re.search(r'\((.*?)\)',div.find("div", {"class": "breadcrumb-serp__link-counter"}).get_text()).group(1).replace(",", ""))
        url = f'https://www.propertyfinder.ae{div.find("a", {"class": "breadcrumb-serp__link"}).get("href")}'

        if check_count(count):
            final_urls.append(url)
        else:
            backlog_urls.append(url)
            
            
def check_count(count):
    check_count = False
    if count <= 1000:
        check_count = True
    return check_count


def main():

    urls = []
    categories = []
    records = []
    
    # Fetching proxies and then picking random one.
    random_proxy = pick_random(get_proxies())
    proxy = {"http": random_proxy, "https": random_proxy}

    # initializing web browser.
    option = webdriver.ChromeOptions()
    option.add_argument("incognito")
    option.add_argument("--disable-notifications")
    option.add_argument("--start-maximized")
    # option.add_argument('--proxy-server=%s' % random_proxy)
    driver = webdriver.Chrome(executable_path='./chromedriver', options=option)

    # Crawling and fetching urls for all the categories.
    for category, category_url in categories_dic.items():
        listing_urls, listing_categories = get_listing_urls(driver, category, category_url)
        urls += listing_urls
        categories += listing_categories

    # Making list of tuples to insert into db.
    for category, url in zip(urls, categories):
        records.append((url, category))

    create_table()

    print(f"Records Found: {str(len(records))}")
    insert_data(records)


main()