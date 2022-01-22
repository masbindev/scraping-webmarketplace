import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
import lxml

import firebase_admin
from firebase_admin import credentials

# Import database module.
from firebase_admin import db


def init_db():
    # initialize authentication to firebase
    cred = credentials.Certificate("path/to/your/credentials.json")
    firebase_admin.initialize_app(
        cred,
        {'databaseURL': 'https://your-firebase-project-url.firebasedatabase.app/'},
    )


def write_database(data_ref, data_to_write):
    # Get a database reference for the marketplace listing.
    ref = db.reference('feinternational/')

    # get reference for data
    datadb_ref = ref.child(data_ref)
    datadb_ref.set(data_to_write)


def get_listing_id(listing_url):
    last_url_path = listing_url.split('/')[4]
    return last_url_path.split('-')[0]


def get_feint(event):
    print(event)
    init_db()

    start_url = 'https://feinternational.com/buy-a-website/#tabs-1'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    }

    r = requests.get(start_url, headers=headers)
    print(r.status_code)

    # set scrape timestamp
    scrap_time = datetime.now().astimezone()
    scrap_date = date.today()

    html_soup = BeautifulSoup(r.content, 'lxml')
    listings = html_soup.findAll('div', class_='listing')

    # initialize scrap count
    scrap_count = 0
    scrapped_listing = []
    scrapped_listing_data = {}

    for listing in listings:

        listing_status = listing.find('span', class_='asking-price-sold')
        # print(f'listing_status = {listing_status}')

        if not listing_status or listing_status.text.strip() != 'SOLD':

            title = listing.find('h2', class_='listing-title').find('a').text.strip()
            listing_url = listing.find('h2', class_='listing-title').find('a')['href']
            # print(listing_url)
            listing_id = get_listing_id(listing_url)

            # collect listings ids
            scrapped_listing.append(listing_id)

            yearly_revenue = listing.find(
                'dd',
                class_='listing-overview-item listing-overview-item--yearly-revenue',
            )

            # anticipate item not found
            if yearly_revenue:
                yearly_revenue = yearly_revenue.text.strip()
            else:
                yearly_revenue = ''

            yearly_net_profit = listing.find(
                'dd',
                class_='listing-overview-item listing-overview-item--yearly-profit',
            )
            # anticipate item not found
            if yearly_net_profit:
                yearly_net_profit = yearly_net_profit.text.strip()
            else:
                yearly_net_profit = ''

            asking_price = listing.find(
                'dd', class_='listing-overview-item listing-overview-item--asking-price'
            )
            # anticipate item not found
            if asking_price:
                asking_price = asking_price.text.strip()
            else:
                asking_price = ''

            description = listing.find('p').text.strip()

            listing_data = {
                'listing_id': listing_id,
                'title': title,
                'listing_url': listing_url,
                'yearly_revenue': yearly_revenue,
                'yearly_net_profit': yearly_net_profit,
                'asking_price': asking_price,
                'decription': description,
                'scrapped_time': scrap_time.strftime("%m/%d/%Y - %H:%M:%S %z"),
            }

            scrapped_listing_data[listing_id] = listing_data

            scrap_count += 1

    # write scrapped data into DB
    write_database('listings/', scrapped_listing_data)

    # prepare some additional info about scrapping activity status and write to DB
    scrap_info = {
        'scrap_count': scrap_count,
        'recent_scrapped_listings': scrapped_listing,
        'last_scrap_url': start_url,
        'scrap_time_stamp': scrap_time.strftime("%m/%d/%Y - %H:%M:%S %z"),
    }
    write_database('scrap_info/', scrap_info)
