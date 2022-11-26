from typing import Tuple
from onjobtraining_lib import create_sess, get_audit_result, get_writeoff_data
from requests import Session
from datetime import datetime
import csv
from logging import info
from utils import create_logger_to_file, append_to_csv
import argparse
from os import chdir
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
from time import sleep

def download_pdf(
    sess:Session,
    wid:str
):
    chrome_options = Options()
    chrome_options.add_argument('--kiosk-printing')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')

    browser = webdriver.Chrome(options=chrome_options)
    browser.get("https://onjobtraining.wda.gov.tw/WDATraining/?i=5#")
    for k, v in sess.cookies.items():
        browser.add_cookie({"name":k, "value":v})
    for it in ["B2", "B3"]:
        info(f"trying to get pdf {it}")
        browser.get(f"https://onjobtraining.wda.gov.tw/WdaRestart/Report/{it}/{wid}")
        sleep(10)
        # ref: https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-printToPDF
        pdf_data = browser.execute_cdp_cmd("Page.printToPDF", {"scale":0.9})
        with open(f'{it}.pdf', 'wb') as file:
            file.write(base64.b64decode(pdf_data['data']))
    browser.quit()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("account",  help="user account, usually national identification number")
    parser.add_argument("password", help="user password bj4")
    parser.add_argument("month",    help="the month they had courses", type=int)
    parser.add_argument("work_dir", help="working directory")
    parser.add_argument("audit_csv",help="the audit csv file")
    parser.add_argument("username" ,help="the realname of the user")
    args = parser.parse_args()

    chdir(args.work_dir)
    create_logger_to_file(datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".log3")
    info("start login ...")
    sess = create_sess(
            args.account,
            args.password
        )
    info("login done")
    info("start query audit result ...")
    audit_str = get_audit_result(sess, (2022, args.month))
    info("audit query done")
    append_to_csv(args.audit_csv, [args.username, audit_str])
    if audit_str == "":
        info("audit not passed")
        return
    info("obtaining writeOff id ...")
    wfid = get_writeoff_data(sess, (2022, args.month))["writeOffId"]
    info(f"get wfid: {wfid}")
    info("start downloading pdf ...")
    download_pdf(
        sess,
        wfid
    )

if __name__ == "__main__":
    main()