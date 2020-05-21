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
    return [o for o in opts if any(p in o.text for p in patterns)]

def refreshFormOptions(form_title, option_filter):
    form = getForm(form_title)
    opts = getOptions(form)
    opts = filterOptions(opts, option_filter)
    form.click()
    return form, opts

def findPDFs(
        academic_year=['2019-2020'],
        from_school=[''],
        to_school=['Berkeley'],
        department=['Physics']
):
    driver.get('http://assist.org')
    driver.implicitly_wait(5)

    # Set Academic Year
    academic_year_form = getForm('academicYear')
    academic_years = getOptions(academic_year_form)
    academic_years = filterOptions(academic_years, academic_year)
    for year in academic_years:
        try:
            academic_year_form.click()
        except StaleElementReferenceException:
            academic_year_form = getForm('academicYear')
            academic_year_form.click()
        year.click()  # Most Recent Academic Year
        driver.implicitly_wait(0.5)

        # Get From Schools
        from_school_form = getForm('fromInstitution')
        from_schools = getOptions(from_school_form)
        from_schools = filterOptions(from_schools, from_school)
        for school in from_schools:
            try:
                from_school_form.click()
            except StaleElementReferenceException:
                from_school_form = getForm('fromInstitution')
                from_school_form.click()
            school.click()
            driver.implicitly_wait(0.5)

            # Set To School
            agreement_form = getForm('agreement')
            agreements = getOptions(agreement_form)
            agreements = filterOptions(agreements, to_school)
            for agreement in agreements:
                try:
                    agreement_form.click()
                except StaleElementReferenceException:
                    agreement_form = getForm('agreement')
                    agreement_form.click()
                agreement.click()
                driver.implicitly_wait(0.5)

                # View Agreements
                viewAgreementsButton = driver.find_element_by_xpath("//button[contains(text(), 'View Agreements')]")
                viewAgreementsButton.click()
                driver.implicitly_wait(0.5)

                # Get Departments
                departments = driver.find_elements_by_xpath("//div[contains(@class, 'viewByRowColText')]")
                departments = filterOptions(departments, department)
                for d in departments:
                    d.click()
                    driver.implicitly_wait(0.5)

                    dlAgreementsButton = driver.find_element_by_xpath("//button[contains(text(), 'Download Agreement')]")
                    dlAgreementsButton.click()
                    driver.implicitly_wait(0.5)

if not osp.isdir('./pdfs/'):
    os.mkdir('./pdfs/')

findPDFs()

x=2