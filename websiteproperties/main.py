import requests
from bs4 import BeautifulSoup
from datetime import date, datetime

import firebase_admin
from firebase_admin import credentials

import re

# Import database module.
from firebase_admin import db


def init_db():
    # initialize authentication to firebase
    cred = credentials.Certificate("path/to/your/credential.json")
    firebase_admin.initialize_app(
        cred,
        {'databaseURL': 'https://your-firebase-project-url.firebasedatabase.app/'},
    )


# function to rewrite all db content
def write_database(data_ref, data_to_write):
    # Get a database reference for the marketplace listing.
    ref = db.reference('webprop/')

    # get reference for data
    datadb_ref = ref.child(data_ref)
    datadb_ref.set(data_to_write)


# function to update db content
def update_database(data_ref, data_to_write):
    # Get a database reference for the marketplace listing.
    ref = db.reference('webprop/')

    # get reference for data
    datadb_ref = ref.child(data_ref)
    datadb_ref.update(data_to_write)


def init_headers():
    headers = {
        'referer': 'https://google.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    }
    return headers


def get_webprop(event):
    init_db()

    # start url with params filter content site only
    home_url = 'https://websiteproperties.com'
    start_url = 'https://websiteproperties.com/websites-for-sale/'

    # counting & collecting list data
    scrap_count = 0
    scrapped_listing = []
    scrapped_listing_data = {}

    next_url = start_url

    # getting the page
    while next_url:
        print(next_url)
        session = requests.Session()
        r = session.get(next_url, headers=init_headers())
        soup = BeautifulSoup(r.text, 'lxml')

        listings = soup.findAll('article', class_='listing-card')

        for item in listings:
            title = item.find('div', class_='listing-card-title').find('a').text.strip()
            list_id = item.find('p', class_='mb-0 mr-4').find('strong').text.strip()
            list_url = item.find('div', class_='listing-card-title').find('a')['href']

            scrapped_listing.append(list_id)

            # getting the stats
            gross_rev, cash_flow, asking_price = '', '', ''
            stats = item.findAll('li', class_='d-flex justify-content-between')
            for stat in stats:
                stat_name = stat.find('span').text.strip().lower()
                stat_value = stat.find('strong').text.strip()

                if stat_name == 'gross rev:':
                    gross_rev = stat_value
                elif stat_name == 'cash flow:':
                    cash_flow = stat_value
                elif stat_name == 'asking price:':
                    asking_price = stat_value

            # scrapping individual listing page to get description, category and established year
            # print(list_url)

            # set scrape timestamp
            scrap_time = datetime.now().astimezone()

            item_page = session.get(list_url)
            item_soup = item_soup = BeautifulSoup(item_page.text, 'lxml')
            category = (
                item_soup.find('span', class_='fa fa-folder')
                .nextSibling.strip()
                .lower()
            )

            # getting established year from tabledata
            tabledata = item_soup.find(
                'table', class_='table listing-data-table'
            ).findAll('tr')
            for data in tabledata:
                if data.find('th').text.strip().lower() == 'year established':
                    established = data.find('td').text.strip()

            # getting description
            description = ''
            content = item_soup.find(
                'div', class_='blog-single-content listing-single-content'
            )
            content_p = content.findAll('p')
            content_li = content.findAll('li')
            for p in content_p:
                description += p.text.strip()

            for li in content_li:
                description += f'{li.text.strip()}.'

            listing_data = {
                'listing_id': list_id,
                'listing_url': list_url,
                'title': title,
                'gross_revenue': gross_rev,
                'asking_price': asking_price,
                'cash_flow': cash_flow,
                'established': established,
                'description': description,
                'scrap_time': scrap_time.strftime("%m/%d/%Y - %H:%M:%S %z"),
            }

            scrapped_listing_data[list_id] = listing_data
            scrap_count += 1

        if soup.find('a', class_='next page-numbers'):
            next_url = home_url + soup.find('a', class_='next page-numbers')['href']
        else:
            next_url = False

    write_database(f'listings/', scrapped_listing_data)

    scrap_info = {
        'scrap_count': scrap_count,
        'recent_scrapped_listings': scrapped_listing,
        'scrap_time_stamp': scrap_time.strftime("%m/%d/%Y - %H:%M:%S %z"),
    }
    write_database('scrap_info/', scrap_info)
