# get_product_info.py
'''
A first shot at using Selenium to scrape an Amazon search
results page for product info, which it summarizes.
'''

import sys
import os
from google import genai
from dotenv import load_dotenv
import logging
import argparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EXP_COND
from webdriver_manager.chrome import ChromeDriverManager


VERBOSE_MODE = True
WAIT_SECONDS = 5
NUM_RESULTS_TO_REPORT = 5

MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "")
API_KEY = os.getenv("GEMINI_API_KEY", "")
prompt = 'Using the following description of the product, categorize it into one of three categories: Budget, Gaming, or Professional, or Unknown. Respond with only one of these four words. Here is the description of the product: '
client = genai.Client(api_key=API_KEY)

# I got this URL by manually navigating to Amazon and searching for 'laptops'
AMZ_URL1 = 'https://www.amazon.com/s?k=laptops&crid=2I8DQEWR8T6I5&sprefix=laptops%2Caps%2C168&ref=nb_sb_noss_1'
AMZ_URL2 = 'https://www.amazon.com/s?k=samsung+tablets&crid=1A1MX7BETAF6T&sprefix=samsung+tablets%2Caps%2C169&ref=nb_sb_noss_1'

# Top Brands so I can get some reviews!
AMZ_URL3 = 'https://www.amazon.com/s?k=laptops&rh=p_n_g-101014971069111%3A119653281011&dc&crid=19L1PSLDJ9LA9&qid=1773772920&rnid=119653280011&sprefix=%2Caps%2C203&ref=sr_nr_p_n_g-101014971069111_1&ds=v1%3AqoOQjTEfmpCitPvOSQSrlsBL%2Fn0JHKS8k7F7fNPzjdY'
AMZ_URL4 = 'https://www.amazon.com/s?k=laptops&dc&crid=19L1PSLDJ9LA9&qid=1773773282&rnid=1248877011&sprefix=%2Caps%2C203&ref=sr_nr_p_72_1&ds=v1%3Axo97hdAZUBc9qxpKvc95HZ%2FroVW7i5P%2BXf%2BUo1mXzKI'

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Makes Amazon less likely to detect automation
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option('excludeSwitches', ['enable-automation'])

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

try:
    driver.get(AMZ_URL4)
except:
    print(f'Exception calling driver.get for url: {AMZ_URL4}')
    sys.exit(1)
    
if VERBOSE_MODE:
    print("Page title:", driver.title)
    driver.save_screenshot('screenshot_from_url.png')


# Load results
driver_wait = WebDriverWait(driver, WAIT_SECONDS)
driver_wait.until(EXP_COND.presence_of_element_located((By.CSS_SELECTOR, '[data-component-type="s-search-result"]')))

# Each product card has this attribute
product_cards = driver.find_elements(By.CSS_SELECTOR, '[data-component-type="s-search-result"]')

if VERBOSE_MODE:
    print(f"Found {len(product_cards)} product cards\n")
    print(f"Showing info for {NUM_RESULTS_TO_REPORT} products ...")

# If we don't get as many as we hard-coded for, take what we get.
if len(product_cards) < NUM_RESULTS_TO_REPORT:
    NUM_RESULTS_TO_REPORT = len(product_cards)

products = []
for card in product_cards[:NUM_RESULTS_TO_REPORT]:
    product = {}

    # Title
    try:
        product['title'] = card.find_element(By.CSS_SELECTOR, 'h2 span').text
        full_prompt = prompt + ' ' + product['title']
        response = client.models.generate_content(model=MODEL_NAME, contents=full_prompt)
        product['predicted_category'] = response.text

    except:
        product['predicted_category'] = None
        product['title'] = None

    # Price (whole + fraction, e.g. "$999" + ".99")
    try:
        whole = card.find_element(By.CSS_SELECTOR, '.a-price-whole').text.replace(',', '')
        fraction = card.find_element(By.CSS_SELECTOR, '.a-price-fraction').text
        product['price'] = float(f"{whole}.{fraction}")
    except:
        product['price'] = None

    # Rating (e.g. "4.5 out of 5 stars")
    try:
        rating_text = card.find_element(By.CSS_SELECTOR, '.a-icon-star-small span').get_attribute('innerHTML')
        product['rating'] = float(rating_text.split(' ')[0])
    except:
        product['rating'] = None

    # Number of reviews
    try:
        product['review_count'] = card.find_element(By.CSS_SELECTOR, '[aria-label$="stars"] + span a span').text.replace(',', '')
    except:
        product['review_count'] = None

    # Product URL
    try:
        product['url'] = card.find_element(By.CSS_SELECTOR, 'h2 a').get_attribute('href')
    except:
        product['url'] = None

    # ASIN (Amazon's unique product ID, from the card's data attribute)
    try:
        product['asin'] = card.get_attribute('data-asin')
    except:
        product['asin'] = None

    # Thumbnail image URL
    try:
        product['image_url'] = card.find_element(By.CSS_SELECTOR, '.s-image').get_attribute('src')
    except:
        product['image_url'] = None

    if product['title']:  # Skip sponsored/ad cards with no title
        products.append(product)

if len(product_cards) == 0:
    print('Search did not return any matching products.')
else:
    for i, p in enumerate(products[:NUM_RESULTS_TO_REPORT], 1):
        print(f"[{i}] {p['title']}")
        print(f"    Price:   ${p['price']}")
        print(f"   Rating:  {p['rating']} ({p['review_count']} reviews)")
        print(f"     ASIN:    {p['asin']}")
        print(f"      URL:     {p['url']}")
        print(f"Image URL:     {p['image_url']}")
        print(f"Predicted Category: {p['predicted_category']}")
        print()

driver.quit()
