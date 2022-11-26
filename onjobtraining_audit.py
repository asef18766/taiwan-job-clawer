from typing import Tuple
from onjobtraining_lib import create_sess, get_audit_result, get_writeoff_data
from requests import Session
from datetime import datetime
import csv
from logging import info
from utils import create_logger_to_file
import argparse
from os import chdir, getcwd
from pprint import pprint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
import json
def download_pdf(
    sess:Session,
    account:str,
    wid:str
):
    chrome_options = Options()
    
    appState = {
        'recentDestinations': [
            {
                'id': 'Save as PDF',
                'origin': 'local',
                'account': ''
            }
        ],
        "scalingType": 3,
        'scaling': '90',
        'selectedDestinationId': 'Save as PDF',
        'version': 2
    }
    prefs = {
        'printing.print_preview_sticky_settings.appState': json.dumps(appState), 
        'savefile.default_directory': getcwd(),
        "profile.password_manager_enabled": False,
        "credentials_enable_service": False
    }
    chrome_options.add_experimental_option('prefs', prefs)
    chrome_options.add_argument('--kiosk-printing')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    ''' 
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    '''
    browser = webdriver.Chrome(options=chrome_options)
    browser.get("https://onjobtraining.wda.gov.tw/WDATraining/?i=5#")
    for k, v in sess.cookies.items():
        browser.add_cookie({"name":k, "value":v})
    browser.get(f"https://onjobtraining.wda.gov.tw/WdaRestart/Report/B2/{wid}")
    info("trying to get pdf")
    from selenium.webdriver.support.ui import WebDriverWait
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(),'{account}')]"))
    )
    info("done locating user id, start printing")
    browser.execute_script("window.print();")
    browser.quit()
    pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("account",  help="user account, usually national identification number")
    parser.add_argument("password", help="user password bj4")
    parser.add_argument("month",    help="the month they had courses", type=int)
    parser.add_argument("work_dir", help="working directory")
    args = parser.parse_args()

    chdir(args.work_dir)
    create_logger_to_file(datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".log2")
    info("start login ...")
    sess = create_sess(
            args.account,
            args.password
        )
    info("login done")
    '''
    info("start query audit result ...")
    audit_str = get_audit_result(sess, (2022, args.month))
    info("audit query done")
    if audit_str == "":
        info("audit not passed")
        return
    info("obtaining writeOff id ...")
    wfid = get_writeoff_data(sess, (2022, args.month))["writeOffId"]
    info(f"get wfid: {wfid}")
    '''
    wfid = "1948388a-59a5-4ac5-bf0a-1a3c39c8d977"
    info("start downloading pdf ...")
    download_pdf(
        sess,
        args.account,
        wfid
    )
if __name__ == "__main__":
    main()