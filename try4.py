# try4.py
'''
This version does NOT use the --headless option, so it
requires that vcXsrv X server is running (Xlaunch).
It needs to be launched with "Multiple Windows", display number 0 and 
with "Disable Access Control" checked.
It also requires the DISPLAY env variable to be set in .bashrc with:
    export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0


'''

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
# options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get('https://www.google.com')


print(driver.title)          # prints "Google"
driver.save_screenshot('screenshot_from_try4a.png')


print('Done!')