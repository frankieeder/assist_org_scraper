import os
import os.path as osp
import pandas as pd
from tika import parser
import urllib
import ssl
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
options.add_experimental_option('prefs', {
    "download.default_directory": "/Users/frankieeder/Google Drive/Code/assist_org_scraper/pdfs",  # Change default directory for downloads
    "download.prompt_for_download": False,  # To auto download the file
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True  # It will not show PDF directly in chrome
})
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
UNVERIFIED_CONTEXT = ssl._create_unverified_context()

def wait_for(condition_function):
  start_time = time.time()
  while time.time() < start_time + 3:
    if condition_function():
      return True
    else:
      time.sleep(0.1)
  raise Exception(
   'Timeout waiting for {}'.format(condition_function.__name__)
  )

class wait_for_page_load(object):
  def __init__(self, browser):
    self.browser = browser
  def __enter__(self):
    self.old_page = self.browser.find_element_by_tag_name('html')
  def page_has_loaded(self):
    new_page = self.browser.find_element_by_tag_name('html')
    return new_page.id != self.old_page.id
  def __exit__(self, *_):
    wait_for(self.page_has_loaded)


def downloadPDF(url):
    driver.get(url)
    pdf_url = driver.find_element_by_tag_name('iframe').get_attribute("src")
    driver.get(pdf_url)

def extractArticulationAgreement(url):
    driver = webdriver.Safari()
    driver.get(url)
    driver.implicitly_wait(3)
    pdfurl = driver.find_element_by_xpath("//div[@class='blob-url']/iframe").get_property('src')
    pdf = requests.get(pdfurl)
    #urllib.request.urlretrieve(url, "temp.pdf")#, context=UNVERIFIED_CONTEXT)
    #pdf = urllib.request.urlopen(url, context=UNVERIFIED_CONTEXT)
    raw = parser.from_buffer(pdf)
    lines = raw['content'].splitlines()
    lines = [l for l in lines if l]
    courses =[l for l in lines if '←' in l]
    school_to = [l for l in lines if 'To: ' in l][-1]
    school_to_year = lines[lines.index(school_to)+1][:9]
    school_to = school_to[4:]
    school_from = [l for l in lines if 'From: ' in l][-1]
    school_from_year = lines[lines.index(school_from)+1][:9]
    school_from = school_from[6:]
    subject = lines[lines.index("END OF AGREEMENT")-1]
    df = pd.DataFrame({
        'SchoolTo': school_to,
        'SchoolToYear': school_to_year,
        'SchoolFrom': school_from,
        'SchoolFromYear': school_from_year,
        'Subject': subject,
        'Course': courses,
    })
    df[['CourseTo', 'CourseFrom']] = df['Course'].str.split(' ← ', expand=True)
    df['CourseToSubject'] = df['CourseTo'].str.extract(r'^(\w+)')
    df['CourseFromSubject'] = df['CourseFrom'].str.extract(r'^(\w+)')
    df['CourseToNumber'] = df['CourseTo'].str.extract(r'\s(\d+\w*)\s-')
    df['CourseFromNumber'] = df['CourseFrom'].str.extract(r'\s(\d+\w*)\s-')
    df['CourseToName'] = df['CourseTo'].str.extract(r'-\s(.*)\s\(')
    df['CourseFromName'] = df['CourseFrom'].str.extract(r'-\s(.*)\s\(')
    df['CourseToUnits'] = df['CourseTo'].str.extract(r'\((.*)\)').astype(float)
    df['CourseFromUnits'] = df['CourseFrom'].str.extract(r'\((.*)\)').astype(float)

    df = df.drop(columns=['Course', 'CourseTo', 'CourseFrom'])

    df.to_csv(f'./data/{subject}__{school_from}_to_{school_to}_{school_from_year}.csv')
    return df

if not osp.isdir('./data/'):
    os.mkdir('./data/')

downloadPDF('https://assist.org/transfer/report/23021054')
extractArticulationAgreement('https://assist.org/transfer/report/23021054')
x=2