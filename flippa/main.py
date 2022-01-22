import requests
from bs4 import BeautifulSoup
import json
from datetime import date, datetime

import firebase_admin
from firebase_admin import credentials

# Import database module.
from firebase_admin import db


def init_db():
    # initialize authentication to firebase
    cred = credentials.Certificate("path/to/your/credential.json")
    firebase_admin.initialize_app(
        cred,
        {'databaseURL': 'https://your-firebaser-project-url.firebasedatabase.app/'},
    )


# function to rewrite all db content
def write_database(data_ref, data_to_write):
    # Get a database reference for the marketplace listing.
    ref = db.reference('flippa/')

    # get reference for data
    datadb_ref = ref.child(data_ref)
    datadb_ref.set(data_to_write)


# function to update db content
def update_database(data_ref, data_to_write):
    # Get a database reference for the marketplace listing.
    ref = db.reference('flippa/')

    # get reference for data
    datadb_ref = ref.child(data_ref)
    datadb_ref.update(data_to_write)


def get_flippa(event):
    init_db()

    start_url = 'https://api.flippa.com/v3/listings?filter[property_type]=starter_site,established_website&filter[sitetype]=blog&filter[status]=open&page%5Bsize%5D=200'

    # starting url
    next_url = start_url

    # initialize scrap count
    scrap_count = 0

    # initialize listings
    scrapped_listing = []
    scrapped_listing_data = {}

    # getting the API when we have next url
    while next_url:
        print(next_url)

        # set scrape timestamp
        scrap_time = datetime.now().astimezone()
        scrap_date = date.today()
        # print(scrap_time, scrap_date)

        # get paginated listing from flippa api
        r = requests.get(next_url)
        scrap_url = next_url
        # print(r.status_code)

        # load into json format
        result_json = json.loads(r.text)

        # loop through listing data
        for item in result_json['data']:
            list_id = item['id']

            # collect listings ids
            scrapped_listing.append(list_id)

            listing_url = item['html_url']
            est = item['established_at']
            status = item['status']
            thumbnail = item['images']['thumbnail']['url']
            domain = item['hostname']
            industry = item['industry']

            # get net profit
            if item['profit_per_month']:
                net_profit = int(item['profit_per_month'])
            else:
                net_profit = None

            # get revenue
            if item['revenue_per_month']:
                revenue = int(item['revenue_per_month'])
            else:
                revenue = ''

            # get/calculate listing price
            if item['display_price']:
                display_price = int(item['display_price'])
            else:
                display_price = ''

            if item['current_price']:
                current_price = int(item['current_price'])
                if display_price:
                    asking_price = max(current_price, display_price)
                else:
                    asking_price = current_price
            else:
                current_price = ''
                if display_price:
                    asking_price = display_price
                else:
                    asking_price = ''

            # can calculate multiple only if display price available and revenue per mo available
            # multiple = display price / (revenue per mo * 12)
            if (display_price != '') & (revenue != ''):
                multiple = round(display_price / (revenue * 12), 1)
            else:
                multiple = ''

            # calculate website age
            est_strip = est.split('T')[0]
            est_date = datetime.strptime(est_strip, '%Y-%m-%d')
            age_month = (scrap_date.year - est_date.year) * 12 + (
                scrap_date.month - est_date.month
            )

            if age_month < 12:
                website_age = str(age_month) + " month"
            else:
                website_age = str(age_month // 12) + " year(s)"

            # get seller location
            location = item['seller_location']

            monetization = item['revenue_sources']

            listing_data = {
                'list_id': list_id,
                'listing_url': listing_url,
                'thumbnail_url': thumbnail,
                'domain name': domain,
                'industry': industry,
                'net_profit': net_profit,
                'price': asking_price,
                'country': location,
                'multiple': multiple,
                'website_age': website_age,
                'monetization': monetization,
                'scraped_time': scrap_time.strftime("%m/%d/%Y - %H:%M:%S %z"),
            }

            scrapped_listing_data[list_id] = listing_data
            scrap_count += 1

        # print(scrap_data)

        # preparae some additional info about scrapping activity status
        scrap_info = {
            'scrap_count': scrap_count,
            'recent_scrapped_listings': scrapped_listing,
            'last_scrap_url': scrap_url,
            'scrap_time_stamp': scrap_time.strftime("%m/%d/%Y - %H:%M:%S %z"),
        }

        # getting next url (if any)
        if result_json['links']['next']:
            next_url = result_json['links']['next']
        else:
            next_url = False

    # update scrapped listing into DB
    write_database('listings/', scrapped_listing_data)
    update_database('scrap_info/', scrap_info)
