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

def findPDFs2(academic_year=[''], from_school=[''], to_school=[''], department=['']):
    driver.get('http://assist.org')
    driver.implicitly_wait(5)

    academic_years, from_schools, agreements = pdfFinder(academic_year, from_school, to_school, department, download=False)
    for y, yr in enumerate(academic_years):
        for s, schl in enumerate(from_schools):
            driver.get('http://assist.org')
            driver.implicitly_wait(5)
            for a, agreement in enumerate(agreements):
                r = pdfFinder(academic_year, from_school, to_school, department, y, s, a)
                if r:
                    academic_years, from_schools, agreements, viewAgreementsButton, departments, dlAgreementsButton = r
                else:
                    continue



def rescrapeObjects(academic_year, from_school, to_school, department, y, s, a, download):
    academic_years = getFormOptions('academicYear', academic_year)
    academic_years[y].click()

    from_schools = getFormOptions('fromInstitution', from_school)
    from_schools[s].click()

    agreements = getFormOptions('agreement', to_school)
    agreements[a].click()

    if not download:
        return academic_years, from_schools, agreements

    viewAgreementsButton = driver.find_element_by_xpath("//button[contains(text(), 'View Agreements')]")
    viewAgreementsButton.click()

    departments = driver.find_elements_by_xpath("//div[contains(@class, 'viewByRowColText')]")
    departments = filterOptions(departments, department)
    for d in departments:
        d.click()

        dlAgreementsButton = driver.find_element_by_xpath("//button[contains(text(), 'Download Agreement')]")
        dlAgreementsButton.click()
    return academic_years, from_schools, agreements, viewAgreementsButton, departments, dlAgreementsButton


def pdfFinder(academic_year, from_school, to_school, department, y=0, s=0, a=0, download=True):
    MAX_ITERS = 5
    c = 0
    objs = None
    while c < MAX_ITERS:
        try:
            objs = rescrapeObjects(academic_year, from_school, to_school, department, y, s, a, download)
            break
        except Exception as e:
            print(e)
            print(f"Retrying... (attempt {c})")
        c += 1
    return objs

def findPDFs(academic_year=[''], from_school=[''], to_school=[''], department=['']):
    driver.get('http://assist.org')
    driver.implicitly_wait(5)

    # Set Academic Year
    academic_years = getFormOptions('academicYear', academic_year)
    y = 0
    while y < len(academic_years):
        try:
            academic_years = getFormOptions('academicYear', academic_year)
            year = academic_years[y]
            year.click()
            #driver.implicitly_wait(0.5)

            # Get From Schools
            from_schools = getFormOptions('fromInstitution', from_school)
            s = 0
            while s < len(from_schools):
                try:
                    from_schools = getFormOptions('fromInstitution', from_school)
                    school = from_schools[s]
                    school.click()
                    #driver.implicitly_wait(10)

                    # Set To School
                    agreements = getFormOptions('agreement', to_school)
                    a = 0
                    while a < (len(agreements)):
                        try:
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
                            departments = filterOptions(departments, department)
                            di = 0
                            while di < len(departments):
                                try:
                                    d = departments[di]
                                    d.click()
                                    #driver.implicitly_wait(0.5)

                                    dlAgreementsButton = driver.find_element_by_xpath("//button[contains(text(), 'Download Agreement')]")
                                    dlAgreementsButton.click()
                                    di += 1
                                except Exception as e:
                                    print(e)
                                    continue
                                #driver.implicitly_wait(0.5)
                            a += 1
                        except Exception as e:
                            print(e)
                            continue
                    s+=1
                except Exception as e:
                    print(e)
                    continue
            y += 1
        except Exception as e:
            print(e)
            continue

if not osp.isdir('./pdfs/'):
    os.mkdir('./pdfs/')

findPDFs2(
    academic_year=['2019-2020'],
    to_school=['To: University of California, Berkeley']
)