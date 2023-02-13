# import packages
import selenium.common.exceptions
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import math
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
import os
import pytz
from random import randint
from time import sleep
from sqlalchemy import create_engine


# Create Chromeoptions instance
options = webdriver.ChromeOptions()
# Adding argument to disable the AutomationControlled flag
options.add_argument("--disable-blink-features=AutomationControlled")
# Exclude the collection of enable-automation switches
options.add_experimental_option("excludeSwitches", ["enable-automation"])
# Turn-off userAutomationExtension
options.add_experimental_option("useAutomationExtension", False)
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

################# Enter Values Here #####################
## values 10,25,50,100,150,200,500,50000 (nationwide)
##entity for models: d2978 - taycan, d590 - honda element, d2430 - 718 cayman, d404 - 911, d311 - Tacoma
# models = ['d2974', 'd2430', 'd590', 'd404', 'd311']
zipcode = 78645
distance = 100
models = ['d2430']
# models_start_year = {"d2974": "2021", "d590": "2003", "d311": "2020", "d2430": "2017", "d404": "2009"}
max_price = 150000
################# Beginning of code #######################

from tqdm import tqdm

temp = []
progress_count = []
url_list = []

for model in models:

    link = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?maxAccidents=0&zip={zip}&sortDir=ASC&distance={dist}&maxPrice={maxprice}&entitySelectingHelper.selectedEntity={model}".format(zip=zipcode, dist=distance, model=model, maxprice=max_price)
    number_extract_pattern = "\\d+"

    driver.get(link)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    number_of_records = int(soup.find("span", {"class": "eegHEr"}).getText().split(' of ')[1].split(' ')[0])
    number_of_results = int(soup.find("span", {"class": "eegHEr"}).getText().split(' of ')[0].split(' - ')[1])
    number_of_pages_to_search_for = math.ceil(number_of_records / number_of_results)

    print("\n ** {number} cars found".format(number=number_of_records))
    print("\n ** pages processing: {}".format(number_of_pages_to_search_for))
    assert "CarGurus" in driver.title
    for i in range(number_of_pages_to_search_for):
        # try:
        #     WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'jX_mq2')))
        # except TimeoutException:
        #     continue
        html2 = driver.page_source
        soup2 = BeautifulSoup(html2, "html.parser")
        cars = soup2.find_all("a", {"data-cg-ft": "car-blade-link"})
        # missing the cycle through pages.
        for car in cars:
            url = "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?" + car.get("href")
            url_test = car.get("href")
            url_list.append(url)
        try:
            for element in driver.find_elements(By.CLASS_NAME, 'jX_mq2'):
                if element.text == "Next page":
                    sleep(randint(0, 3))
                    element.click()
        except selenium.common.exceptions.TimeoutException:
            continue
        except selenium.common.exceptions.ElementClickInterceptedException:
            continue
        except selenium.common.exceptions.StaleElementReferenceException:
            continue
        # Sleep a random number of seconds (between 1 and 5)
        sleep(randint(0, 3))
    for car_detail in url_list:
        try:
            driver.get(car_detail)
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, 'Ro9a_t')))
            html2 = driver.page_source
            soup2 = BeautifulSoup(html2, "html.parser")
            insert_time = datetime.now(pytz.utc)
            ## Parses all the info about the car and the listing into a json attribute:value pair
            info = {(e.find_previous_sibling('dt').text.strip()).replace(':', ''): e.text.strip() for e in
                    soup2.select('dt + dd')}
            accident_status = soup2.find("span", {"class": "aWYTCL"}).getText()
            try:
                dealer_name = soup2.find("a", {"class": "KA8oQB"}).getText()
            except:
                dealer_name = 'No dealer name'
            try:
                dealer_address = soup2.find("span", {"data-track-ui": "dealer-address"}).getText()
            except:
                dealer_address = 'No dealer address'
            car_data_json = json.dumps(info)
            inventory_history = soup2.find("div", {"class": "PaczrG"}).getText()
            days_at_dealership = sum(map(int, re.findall("\\d+", inventory_history.split(' · ')[0])))
            first_date_available = insert_time - timedelta(days=days_at_dealership)
            days_on_cargurus = sum(map(int, re.findall("\\d+", inventory_history.split(' · ')[1])))
            first_date_listed = insert_time - timedelta(days=days_on_cargurus)
            try:
                number_of_saves = sum(map(int, re.findall("\\d+", inventory_history.split(' · ')[2])))
            except:
                number_of_saves = 0
            temp.append([insert_time, first_date_available, first_date_listed, accident_status, dealer_name,
                         dealer_address, days_on_cargurus, days_at_dealership, car_data_json, number_of_saves])
            # perform other operations within the url
        except TimeoutException as e:
            continue
        # Sleep a random number of seconds (between 1 and 5)
        sleep(randint(1, 5))
driver.close()
driver.quit()
df = pd.DataFrame(temp)
data = df.rename(columns={0: "insert_time", 1: "first_date_available", 2: "first_date_listed", 3: "accident_status", 4: "dealer_name",
                          5: "dealer_address", 6: "days_on_cargurus", 7: "days_at_dealership", 8: "car_data_json", 9: "number_of_saves"})

# establish connections
user = os.environ.get("postgres-user")
password = os.environ.get("postgres-pass")
host = os.environ.get("postgres-host")
conn_string = 'postgresql://{user}:{password}@{host}:25060/defaultdb'.format(password=password, user=user, host=host)

db = create_engine(conn_string)
conn = db.connect()

# converting data to sql
data.to_sql('raw_cargurus_scrape', db, schema='public', if_exists='append', index=False)

count = len(df).__str__()
print(count + " car(s) found and added to data source.")
