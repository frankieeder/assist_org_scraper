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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

options = webdriver.ChromeOptions()
options.add_experimental_option('prefs', {
    "download.default_directory": "/Users/frankieeder/Google Drive/Code/assist_org_scraper/pdfs",  # Change default directory for downloads
    "download.prompt_for_download": False,  # To auto download the file
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True  # It will not show PDF directly in chrome
})
driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
UNVERIFIED_CONTEXT = ssl._create_unverified_context()

def downloadPDF(url):
    driver.get(url)
    pdf_url = driver.find_element_by_tag_name('iframe').get_attribute("src")
    driver.get(pdf_url)

def getForm(form_title):
    form = driver.find_element_by_xpath(f"//*[@formcontrolname='{form_title}']")
    return form

def getOptions(form):
    form.click()
    options = form.find_elements_by_xpath("//*[contains(@role, 'option')]")
    return options

def filterOptions(opts, patterns):
    filtered = []
    for o in opts:
        for p in patterns:
            if p in o.text:
                filtered.append(o)
                break
    return filtered

def getFormOptions(form_title, option_filter):
    form = getForm(form_title)
    opts = getOptions(form)
    try:
        opts = filterOptions(opts, option_filter)
    except StaleElementReferenceException:
        opts = getOptions(form)
        opts = filterOptions(opts, option_filter)
    return opts

def findPDFs(
        academic_year=['2019-2020'],
        from_school=[''],
        to_school=['To: University of California, Berkeley'],
        department=['Physics']
):
    driver.get('http://assist.org')
    driver.implicitly_wait(5)

    # Set Academic Year
    academic_years = getFormOptions('academicYear', academic_year)
    for y in range(len(academic_years)):
        academic_years = getFormOptions('academicYear', academic_year)
        year = academic_years[y]
        year.click()
        #driver.implicitly_wait(0.5)

        # Get From Schools
        from_schools = getFormOptions('fromInstitution', from_school)
        for s in range(140, len(from_schools)):
            from_schools = getFormOptions('fromInstitution', from_school)
            school = from_schools[s]
            school.click()
            #driver.implicitly_wait(10)

            # Set To School
            agreements = getFormOptions('agreement', to_school)
            for a in range(len(agreements)):
                agreements = getFormOptions('agreement', to_school)
                agreement = agreements[a]
                agreement.click()
                #driver.implicitly_wait(0.5)

                # View Agreements
                viewAgreementsButton = driver.find_element_by_xpath("//button[contains(text(), 'View Agreements')]")
                viewAgreementsButton.click()
                #driver.implicitly_wait(10)

                # Get Departments
                departments = driver.find_elements_by_xpath("//div[contains(@class, 'viewByRowColText')]")
                try:
                    departments = filterOptions(departments, department)
                except StaleElementReferenceException:
                    departments = driver.find_elements_by_xpath("//div[contains(@class, 'viewByRowColText')]")
                    departments = filterOptions(departments, department)
                for d in departments:
                    d.click()
                    #driver.implicitly_wait(0.5)

                    dlAgreementsButton = driver.find_element_by_xpath("//button[contains(text(), 'Download Agreement')]")
                    dlAgreementsButton.click()
                    #driver.implicitly_wait(0.5)

if not osp.isdir('./pdfs/'):
    os.mkdir('./pdfs/')

findPDFs()

x=2