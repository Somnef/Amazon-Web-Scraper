from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService

from webdriver_manager.chrome import ChromeDriverManager

import time
import os
import sys
import re

import pandas as pd
import numpy as np

import datetime


# usage
if len(sys.argv) != 3:
    print("Usage: python amazon_scraper.py <search_term> <number_of_pages>")
    sys.exit(1)

# get search term and number of pages
search_term = sys.argv[1]
nb_pages = int(sys.argv[2])


def random_wait(avg: float = 4, std: float = 1) -> None:
    # make sure the random number is positive and doesn't go above or below the average by more than 2 standard deviations
    random_time = -1
    while random_time < 0 or random_time > avg + 2 * std or random_time < avg - 2 * std:
        random_time = np.random.normal(avg, std)
    time.sleep(random_time)


chrome_options = Options()
# chrome_options.add_argument("-start-maximized")
chrome_options.add_argument('--log-level=3')
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

url = "https://www.amazon.fr"
driver.get(url)

random_wait(2, 0.5)

# look for accept cookies button
try:
    accept_cookies = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "sp-cc-accept")))
    accept_cookies.click()

    random_wait(2, 0.5)

except Exception as e:
    # continue if no cookies button
    pass

# search bar
try:
    search_bar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
    search_bar.clear()

    for letter in search_term:
        search_bar.send_keys(letter)
        random_wait(0.2, 0.05)

    random_wait(1, 0.2)
    search_bar.send_keys(Keys.RETURN)

    random_wait()

except Exception as e:
    print(f"Couldn't find search bar: {e}")
    driver.close()
    sys.exit(1)

page = 1

# products json
products = []

while page <= nb_pages:
    print(f"Scraping page {page} of {nb_pages}")

    # get all products
    products_list_raw = []
    try:
        products_list_raw = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[(@class and contains(concat(' ', normalize-space(@class), ' '), ' a-section ')) and (@class and contains(concat(' ', normalize-space(@class), ' '), ' a-spacing-small '))]")))
        # print(f"Found {len(products_list_raw)} products in raw list")

    except Exception as e:
        print(f"Couldn't find any products: {e}")
        driver.close()
        sys.exit(1)

    for product in products_list_raw:
        # get product name
        try:
            product_name = product.find_element(By.XPATH, ".//h2/a/span").text

            # only keep products with a name
            if product_name == '':
                continue

        except Exception as e:
            continue

        # get product price
        try:
            product_price = product.find_element(By.XPATH, ".//span[@class and contains(concat(' ', normalize-space(@class), ' '), ' a-price-whole ')]").text
            product_price = float(product_price.replace(",", ".").replace(" ", ""))

        except Exception as e:
            product_price = ""

        # get product rating
        try:
            product_rating = product.find_element(By.XPATH, ".//i[@class and contains(concat(' ', normalize-space(@class), ' '), ' a-icon-star-small ')]/span").get_attribute("innerHTML").split()[0]
            product_rating = float(product_rating.replace(",", "."))
        except Exception as e:
            product_rating = ""

        # get product number of ratings
        try:
            product_nb_ratings = ""

            nb_ratings_tmp = product.find_elements(By.XPATH, ".//div[(@class and contains(concat(' ', normalize-space(@class), ' '), ' a-row ')) and (@class and contains(concat(' ', normalize-space(@class), ' '), ' a-size-small '))]/span/a[(((@class and contains(concat(' ', normalize-space(@class), ' '), ' a-link-normal ')) and (@class and contains(concat(' ', normalize-space(@class), ' '), ' s-underline-text '))) and (@class and contains(concat(' ', normalize-space(@class), ' '), ' s-underline-link-text '))) and (@class and contains(concat(' ', normalize-space(@class), ' '), ' s-link-style '))]/..")
            for rating in nb_ratings_tmp:
                r = rating.get_attribute("aria-label").replace("\xa0", "").replace("(", "").replace(")", "").replace(" ", "").replace(",", "")
                if r[0].isdigit():
                    product_nb_ratings = int(r)
                    break

        except Exception as e:
            product_nb_ratings = ""

        # get product link
        try:
            product_link = product.find_element(By.XPATH, ".//h2/a").get_attribute("href")
        except Exception as e:
            product_link = ""

        products.append({
                "name": product_name,
                "price": product_price,
                "rating": product_rating,
                "nb_ratings": product_nb_ratings,
                "link": product_link,
                "scrape_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    random_wait(1, 0.2)
    
    # go to next page
    if page == nb_pages:
        break

    try:
        next_page = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[text() = 'Suivant']")))
        next_page.click()
        random_wait(2, 0.5)

        page += 1
    
    except Exception as e:
        print(f"No more pages")
        break

driver.close()

products_df = pd.DataFrame(products)
if not products_df.empty:
    print(f"\n\nFound {len(products_df)} products with matching name. Saving to file...\n\n")

    # save products' dataframe to file
    if not os.path.exists(f"./amazon/{'_'.join(search_term.lower().strip().split())}"):
        # print(f"Creating directory ./amazon/{'_'.join(search_term.lower().strip().split())}")
        os.makedirs(f"./amazon/{'_'.join(search_term.lower().strip().split())}")

    products_df.to_csv(
        f"./amazon/{'_'.join(search_term.lower().strip().split())}/{datetime.datetime.now().strftime('%Y-%m-%d__%H-%M-%S')}.csv", 
        index=False
    )