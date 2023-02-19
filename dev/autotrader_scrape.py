# import packages
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
# selenium 4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
from datetime import timedelta
import re
import pytz
from sqlalchemy import create_engine
import os

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

################# Enter Values Here #####################

zipcode = os.environ.get("zipcode")
## values 10,25,50,100,500,50000 (nationwide)
distance = 25
## this gets the intial listings based on about 15 cars per page.
number_of_records = 25
##entity d2978 - taycan, d590 - honda element, d2430 - 718 cayman, d404 - 911
models = ['d2974']
minimum_year = '2009'
manual = '&transmissionCodes=MAN'
pages = 4
# models = ['d2974', 'd2430', 'd590', 'd404']
## must get entity code from cargurus website, may put together lookup dimension later to grab them
max_price = 150000
################# Beginning of code #######################

temp = []

link = "https://www.autotrader.com/cars-for-sale/cars-under-{maxprice}/{zip}?requestId=FIT&makeCodeList=HONDA%2CPOR&transmissionCodes=MAN&searchRadius={dist}&modelCodeList=POR718CAY%2C911%2CELEMENT%2CFIT&marketExtension=include&startYear={minyear}&sortBy=relevance&numRecords={numofrecords}".format(dist=distance, zip=zipcode, numofrecords=number_of_records, minyear=minimum_year, maxprice=max_price)
number_extract_pattern = "\\d+"

print(link)

print("\n ** ready to extract data from: {}...{}".format(link[:20], link[-20:]))
print("\n ** pages processing: {}".format(pages))

driver.get(link)
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")
number_of_results = int(soup.find("div", {"class": "results-text-container text-size-200"}).getText().split(' of ')[1].split(' Results')[0])
number_of_pages_to_search_for = round(number_of_records/number_of_results)

url_list = []
for i in range(number_of_pages_to_search_for):
    cars = soup.find_all("div", {"class": "inventory-listing cursor-pointer panel panel-default"})
    # print(cars)
    ## missing the cycle through pages.
    for car in cars:
        try:
            car_link_test = car.get("id")
            url = "https://www.autotrader.com/cars-for-sale/vehicledetails.xhtml?listingId={listingid}".format(listingid=car_link_test)
            url_list.append(url)
        except:
            continue
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ae_jim_pagination796"]/li[3]/a'))).click()
        except:
            break
print(url_list)
        # for car_detail in url_list:
        #         driver.get(car_detail)
        #     #     WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, 'Ro9a_t')))
        #         html2 = driver.page_source
        #         soup2 = BeautifulSoup(html2, "html.parser")
        #         print(soup2)
            #     insert_time = datetime.now(pytz.utc)
            #     ## Parses all the info about the car and the listing into a json attribute:value pair
            #     info = {(e.find_previous_sibling('dt').text.strip()).replace(':', ''): e.text.strip() for e in
            #             soup2.select('dt + dd')}
            #     accident_status = soup2.find("span", {"class": "aWYTCL"}).getText()
            #     try:
            #         dealer_name = soup2.find("a", {"class": "KA8oQB"}).getText()
            #     except:
            #         dealer_name = 'No dealer name'
            #     try:
            #         dealer_address = soup2.find("span", {"data-track-ui": "dealer-address"}).getText()
            #     except:
            #         dealer_address = 'No dealer address'
            #     car_data_json = json.dumps(info)
            #     inventory_history = soup2.find("div", {"class": "PaczrG"}).getText()
            #     days_at_dealership = sum(map(int, re.findall("\\d+", inventory_history.split(' · ')[0])))
            #     first_date_available = insert_time - timedelta(days=days_at_dealership)
            #     days_on_cargurus = sum(map(int, re.findall("\\d+", inventory_history.split(' · ')[1])))
            #     first_date_listed = insert_time - timedelta(days=days_on_cargurus)
            #     try:
            #         number_of_saves = sum(map(int, re.findall("\\d+", inventory_history.split(' · ')[2])))
            #     except:
            #         number_of_saves = 0
            #     temp.append([insert_time, first_date_available, first_date_listed, accident_status, dealer_name,
            #                  dealer_address, days_on_cargurus, days_at_dealership, car_data_json, number_of_saves])
            #     time.sleep(0.25)
            #     # perform other operations within the url
            # except TimeoutException as e:
            #     continue


# driver.close()
# driver.quit()
# df = pd.DataFrame(temp)
# data = df.rename(columns={0: "insert_time", 1: "first_date_available", 2: "first_date_listed", 3: "accident_status", 4: "dealer_name",
#                           5: "dealer_address", 6: "days_on_cargurus", 7: "days_at_dealership", 8: "car_data_json", 9: "number_of_saves"})
# print(data.dtypes)


# establish connections
# user = os.environ.get("postgres-user")
# password = os.environ.get("postgres-pass")
# host = os.environ.get("postgres-host")
# conn_string = 'postgresql://{user}:{password}@{host}:25060/defaultdb'.format(password=password, user=user, host=host)
#
# db = create_engine(conn_string)
# conn = db.connect()
#
# # converting data to sql
# data.to_sql('raw_cargurus_scrape', db, schema='public', if_exists='append', index=False)
#
# count = len(df).__str__()
# print(count + " car(s) found and added to data source.")
