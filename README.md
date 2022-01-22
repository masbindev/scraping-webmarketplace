# scraping-webmarketplace
sample collections of my scraping projects

webmarketplace is marketplace for buying and selling online assets such as websites, domain etc.

This python script will scrap and aggregate website listings information such as price, visitor, trafic etc.

As part of my previous project, the scripts runs on google cloud function (python cloud function is based on flask) and store the scrapped information into firebase realtime DB.

## List of web marketplace
- flippa.com
- feinternational.com
- websiteproperties.com

## How to use the script

The script was intended to run on google cloud function where it can be triggered automatically by using cloud sceduler.

cloud scheduler invoke http --> cloud function endpoint | ptyon script perform scraping --> store the information on firebase realtime DB

1. Create you cloud function in CGP
2. Upload main.py and requirements.txt
3. Update the firebase DB credentals and url on main.py
```python
  def init_db():
      # initialize authentication to firebase
      cred = credentials.Certificate("path/to/your/credentials.json")
      firebase_admin.initialize_app(
          cred,
          {'databaseURL': 'https://your-firebase-project-url.firebasedatabase.app/'},
      )
```

Alternatively you can run the script on your own machine CLI (I recommend using virtual env), just call the script main.py and the main function, after editing how you will output the scapped information.
```bash
> cd flippa
> pip install -r requirements.txt
> python -i main.py
> get_flippa(event='')
```



