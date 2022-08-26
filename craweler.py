from lib2to3.pgen2 import pgen
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup

user_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}

def send_get_req_txt(s:requests.Session, url:str, req_header = user_headers):
    with s.get(url, headers=req_header) as resp:
        if resp.status_code != 200:
            print(f"status code:{resp.status_code}")
            print(resp.text)
            exit(-1)
        return resp.text

def query_course(
    sess:requests.Session,
    pg:int,
    st_date:Tuple[int, int, int],
    en_date:Tuple[int, int, int]
    )->List[str]:
    base_url = f"https://portal.wda.gov.tw/mooc/my_profile.php?reqPage={pg}&stYear={st_date[0]}&stMonth={st_date[1]}&stDay={st_date[2]}&endYear={en_date[0]}&endMonth={en_date[1]}&endDay={en_date[2]}"
    res = []
    
    with sess.get(base_url, headers=user_headers) as resp:
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup.find_all("a", {"target":"_blank"}):
            if str(tag.get("href")).startswith("/info/"):
                res.append(str(tag.get("href"))[6:])
    return res

def add_to_cart(
    sess:requests.Session,
    cid:int,
    referer:str
):
    cart_header = user_headers.copy()
    cart_header.update({
        "x-requested-with": "XMLHttpRequest",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "referer":referer
    })
    base_url = "https://portal.wda.gov.tw/mooc/controllers/user_ajax.php"
    print(f"add cid :{cid}")
    with sess.post(base_url, headers=cart_header, data={
        "action": "addPrintList",
        "id": cid,
        "type": "course"
    }) as resp:
        if resp.status_code != 200:
            print(f"status code: {resp.status_code}")
            print(resp.text)
            exit(-1)
        print(f"add2cart resp:{resp.json()}")

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

    ver_code = input("please insert ver code:")

    login_success_page = ""

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
        else:
            print("login failed...QQ")
            exit(-1)
    # get cookie
    send_get_req_txt(sess, login_success_page)
    send_get_req_txt(sess, "https://portal.wda.gov.tw/mooc/my_profile.php")

    pg_idx = 1
    all_course = []
    
    st_date = (2022, 8, 1)
    en_date = (2022, 8, 31)
    while True:
        cids = query_course(sess, pg_idx, st_date, en_date)
        all_course += cids
        if cids == []:
            break
        print(cids)
        for cid in cids:
            ref_url = f"https://portal.wda.gov.tw/mooc/my_profile.php?reqPage={pg_idx}&stYear={st_date[0]}&stMonth={st_date[1]}&stDay={st_date[2]}&endYear={en_date[0]}&endMonth={en_date[1]}&endDay={en_date[2]}"
            add_to_cart(sess, cid, ref_url)
        pg_idx += 1
    with sess.get("https://portal.wda.gov.tw/mooc/print_profile.php?print=1", headers=user_headers) as resp:
        if resp.status_code != 200:
            print(f"status code:{resp.status_code}")
            print(resp.text)
            exit(-1)
        
        with open(fname, 'wb') as f:
            for chunk in resp:
                f.write(chunk)
    sess.close()

import csv
if __name__ == "__main__":
    with open('account.csv', newline='', encoding="utf-8") as csvfile:
        rows = csv.reader(csvfile)

        ST_FM = 33
        for rid, row in enumerate(rows):
            if rid < ST_FM:
                continue

            username = row[0]
            user_email = row[1]
            passwd = row[2]
            print(username, user_email, passwd)
            main(user_email, passwd, username + ".pdf")
            break