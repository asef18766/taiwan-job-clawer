from logging import error
from pprint import pprint
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
import csv
import os
import shutil
from csv import writer
import cv2
from pytesseract import image_to_string
import pytesseract

bad_pw = []

user_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}
total_time = 0
def send_get_req_txt(s:requests.Session, url:str, req_header = user_headers):
    with s.get(url, headers=req_header) as resp:
        if resp.status_code != 200:
            print(f"status code:{resp.status_code}")
            print(resp.text)
            exit(-1)
        return resp.text

def ocr(mode="--psm", model=6, imgname="capcha.jpg")->str:
    img = cv2.imread(imgname)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #cv2.imwrite("gry.jpg", img)
    (h, w) = img.shape[:2]
    img = cv2.resize(img, (w*2, h*2))
    #cv2.imwrite("gry2.jpg", img)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, None)
    #cv2.imwrite("morph.jpg", img)
    img = cv2.threshold(img, 65, 255, cv2.THRESH_BINARY)[1]
    #cv2.imwrite("thr.jpg", img)
    txt:str = image_to_string(img, config=f"-c tessedit_char_whitelist=0123456789 --oem 3 {mode} {model}").strip()
    return txt

def main(
    user_email = "a0911971848@gmail.com",
    user_passwd = "Zzaaqq831109!",
    fname = "res.pdf"
):
    logon_url = ""
    sess = requests.session()
    
    print("process with initial logon...")
    lg_txt = send_get_req_txt(sess, "https://portal.wda.gov.tw/mooc/index.php")
    soup = BeautifulSoup(lg_txt, 'html.parser')
    for link in soup.find_all('a'):
        if str(link.get('href')).startswith("https://sso.taiwanjobs.gov.tw/member/login.aspx"):
            logon_url = link.get('href')
            break
    else:
        print("can not find logon url...?")
        exit(-1)

    print("processing login...")
    print(f"logon url: {logon_url}")
    login_page_txt = send_get_req_txt(sess, logon_url)
    soup = BeautifulSoup(login_page_txt, 'html.parser')
    viewstate = soup.find("input", {"id": "__VIEWSTATE"}).get("value")
    viewstate_generator = soup.find("input", {"id": "__VIEWSTATEGENERATOR"}).get("value")

    print(f"view state: {viewstate}")
    print(f"viewstate generator: {viewstate_generator}")
    
    # capcha login
    while True:
        print("obtaining capcha image...")
        capcha_txt = send_get_req_txt(
            sess, 
            "https://sso.taiwanjobs.gov.tw/Internet/jobwanted/ValidateImage.aspx"
        )

        capcha_img_url = ""
        soup = BeautifulSoup(capcha_txt, 'html.parser')
        for link in soup.find_all('img'):
            #print(link.get('src'))
            if str(link.get('src')).startswith("util/ValidateNumber.ashx?"):
                capcha_img_url = link.get('src')
                break

        capcha_img_url = f"https://sso.taiwanjobs.gov.tw/Internet/jobwanted/{capcha_img_url}"
        img_header = user_headers.copy()
        img_header.update({
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        })


        print(f"requesting img url {capcha_img_url}")
        with sess.get(capcha_img_url, headers=img_header) as resp:
            if resp.status_code != 200:
                print(f"status code:{resp.status_code}")
                print(resp.text)
                exit(-1)
            
            with open("capcha.jpg", 'wb') as f:
                for chunk in resp:
                    f.write(chunk)

        ver_code = ocr()
        if len(ver_code) != 5:
            print("retry ocr")
            continue
        with sess.post(logon_url, headers=user_headers, data={
            "__EVENTTARGET":"",
            "__EVENTARGUMENT":"",
            "__VIEWSTATE":viewstate,
            "__VIEWSTATEGENERATOR":viewstate_generator,
            "ctl00$CPH1$txt_EmailId":user_email,
            "ctl00$CPH1$txt_dwsp":user_passwd,
            "ctl00$CPH1$txt_VerifyCode":ver_code,
            "ctl00$CPH1$btnLogin":"送 出",
            "ctl00$CPH1$confirm_txt":""

        }, allow_redirects=False) as resp:
            print(resp.status_code)
            if resp.status_code == 302:
                print(resp.headers["Location"])
                login_success_page = resp.headers["Location"]
                break
                # log to ML dataset
                # shutil.copyfile("capcha.jpg", f"dataset/{ver_code}.jpg")
            elif resp.status_code == 200:
                if resp.text.find("帳號或密碼錯誤，請重新輸入!") != -1:
                    error(f"user {username} has wrong password !")
                    global bad_pw
                    bad_pw.append(username)
                    break
                elif resp.text.find("圖型驗證碼輸入有誤，請重新輸入") != -1:
                    print("retry ocr")
                else:
                    print("200 with unknowned situation ... QQ")
                    exit(-1)
            else:
                print(f"{resp.status_code} unknowned situation ... QQ")
                exit(-1)

if __name__ == "__main__":
    pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\User\\Documents\\softwares\\tesseract-ocr\\tesseract.exe"
    with open('account.csv', newline='', encoding="utf-8") as csvfile:
        rows = csv.reader(csvfile)

        ST_FM = 0
        for rid, row in enumerate(rows):
            total_time = 0
            if rid < ST_FM:
                continue

            username = row[1]
            user_email = row[2]
            passwd = row[3]
            print(f"current user {username}")
            main(user_email, passwd, username)
        pprint(bad_pw)