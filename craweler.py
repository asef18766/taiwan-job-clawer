from typing import Dict, List, Tuple
import requests
from bs4 import BeautifulSoup
import csv
import os
import shutil
from csv import writer
import cv2
from pytesseract import image_to_string
import pytesseract

user_headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
}
total_time = 0


def send_get_req_txt(s: requests.Session, url: str, req_header=user_headers):
    with s.get(url, headers=req_header) as resp:
        if resp.status_code != 200:
            print(f"status code:{resp.status_code}")
            print(resp.text)
            exit(-1)
        return resp.text


def query_course(
    sess: requests.Session,
    pg: int,
    st_date: Tuple[int, int, int],
    en_date: Tuple[int, int, int]
    ) -> Tuple[List[str], List[int]]:
    base_url = f"https://portal.wda.gov.tw/mooc/my_profile.php?reqPage={pg}&stYear={st_date[0]}&stMonth={st_date[1]}&stDay={st_date[2]}&endYear={en_date[0]}&endMonth={en_date[1]}&endDay={en_date[2]}"
    res = []
    res_time = []

    with sess.get(base_url, headers=user_headers) as resp:
        soup = BeautifulSoup(resp.text, 'html.parser')
        for tag in soup.find_all("a", {"target": "_blank"}):
            if str(tag.get("href")).startswith("/info/"):
                res.append(str(tag.get("href"))[6:])
        for tag in soup.find_all("td", {"data-title": "認證時數"}):
            course_time = int(str(tag.text).strip().replace("分鐘", ""))
            res_time.append(course_time)
    return res, res_time


def add_to_cart(
    sess: requests.Session,
    cid: int,
    nid: int,
    referer: str
):
    cart_header = user_headers.copy()
    cart_header.update({
        "x-requested-with": "XMLHttpRequest",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "referer": referer
    })
    base_url = "https://portal.wda.gov.tw/mooc/controllers/user_ajax.php"
    print(f"add cid :{cid}")
    with sess.post(base_url, headers=cart_header, data={
        "action": "addPrintList",
        "id": cid,
        "type": "course",
        "nid":nid
    }) as resp:
        if resp.status_code != 200:
            print(f"status code: {resp.status_code}")
            print(resp.text)
            exit(-1)
        print(f"add2cart resp:{resp.json()}")


def del_to_cart(
    sess: requests.Session,
    referer: str
):
    cart_header = user_headers.copy()
    cart_header.update({
        "x-requested-with": "XMLHttpRequest",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "referer": referer
    })
    base_url = "https://portal.wda.gov.tw/mooc/controllers/user_ajax.php"
    print(f"delete cart")
    with sess.post(base_url, headers=cart_header, data={
        "action": "delPrintList",
        "id": 0,
        "type": "All"
    }) as resp:
        if resp.status_code != 200:
            print(f"status code: {resp.status_code}")
            print(resp.text)
            exit(-1)
        print(f"add2cart resp:{resp.json()}")


def download_region(
    sess: requests.Session,
    date: Tuple[int, int, int],
    fname: str
):
    base_url = f"https://portal.wda.gov.tw/mooc/co_search_record.php?stYear={date[0]}&stMonth={date[1]}&stDay={date[2]}&endYear={date[0]}&endMonth={date[1]}&endDay={date[2]}"
    print("query date...")
    if send_get_req_txt(sess, base_url).find("查無該時間區間的學習紀錄") != -1:
        return

    print("recv data...")
    reg_headers = user_headers.copy()
    reg_headers.update({
        "referer": base_url,
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    })
    with sess.post(base_url, headers=reg_headers, data={
        "stYear": date[0],
        "stMonth": date[1],
        "stDay": date[2],
        "endYear": date[0],
        "endMonth": date[1],
        "endDay": date[2],
        "isPDF": "Y",
        "isDetail": 0
    }) as resp:
        if resp.status_code != 200:
            print(f"status code:{resp.status_code}")
            print(resp.text)
            exit(-1)

        with open(fname, 'wb') as f:
            for chunk in resp:
                f.write(chunk)
'''
    returns {date: serial}
'''
def query_correct_course_id_by_fancybox(
    sess: requests.Session,
    cid:str,
    refer_date:Tuple[int, int, int]
)->Dict[str, Tuple[str, str]]:
    print(f"query fancybox {cid}")
    base_url = "https://portal.wda.gov.tw/mooc/controllers/fancybox_ajax.php"
    fancybox_header = user_headers.copy()
    fancybox_header.update({
        "x-requested-with": "XMLHttpRequest",
        "x-fancybox": "true",
        "referer":f"https://portal.wda.gov.tw/mooc/my_profile.php?type=0&kw=&stYear={refer_date[0]}&stMonth={refer_date[1]}&stDay={refer_date[2]}&endYear={refer_date[0]}&endMonth={refer_date[1]}&endDay={refer_date[2]}"
    })
    with sess.post(base_url, headers=fancybox_header, data={
        "action":"getMajorCourseDetail",
        "cid":cid,
        "c_type":"course"
    }) as resp:
        if resp.status_code != 200:
            print(f"status code:{resp.status_code}")
            exit(-1)
        soup = BeautifulSoup(resp.text, 'html.parser')
        serials = [ 
            (
                link["onclick"].split(',')[1].replace(')', '').replace('(', '').strip(),
                link["onclick"].split(',')[3].replace(')', '').replace('(', '').strip(), 
            )
            for link in soup.find_all('a')
        ]
        dates = [ l.text.strip() for l in soup.find_all("td", {"data-title": "通過日期"}) ]
        assert len(serials) == len(dates)
        return {dates[idx]:serials[idx] for idx in range(len(serials)) }

def ocr(mode="--psm", model=6, imgname="capcha.jpg") -> str:
    img = cv2.imread(imgname)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # cv2.imwrite("gry.jpg", img)
    (h, w) = img.shape[:2]
    img = cv2.resize(img, (w*2, h*2))
    # cv2.imwrite("gry2.jpg", img)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, None)
    # cv2.imwrite("morph.jpg", img)
    img = cv2.threshold(img, 65, 255, cv2.THRESH_BINARY)[1]
    # cv2.imwrite("thr.jpg", img)
    txt: str = image_to_string(
        img, config=f"-c tessedit_char_whitelist=0123456789 --oem 3 {mode} {model}").strip()
    return txt

def add_time(cids:List[Tuple[str, str]], cids_times:List[int]):
    for idx, (_, nid) in enumerate(cids):
        if nid != '0':
            continue
        print(f"add time {cids_times[idx]}")
        global total_time
        total_time += cids_times[idx]

def main(
    user_email="a0911971848@gmail.com",
    user_passwd="Zzaaqq831109!",
    fname="res.pdf"
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
    viewstate_generator = soup.find(
        "input", {"id": "__VIEWSTATEGENERATOR"}).get("value")

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
            # print(link.get('src'))
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
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstate_generator,
            "ctl00$CPH1$txt_EmailId": user_email,
            "ctl00$CPH1$txt_dwsp": user_passwd,
            "ctl00$CPH1$txt_VerifyCode": ver_code,
            "ctl00$CPH1$btnLogin": "送 出",
            "ctl00$CPH1$confirm_txt": ""

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
                    print(f"user {username} has wrong password !")
                    exit(-1)
                elif resp.text.find("圖型驗證碼輸入有誤，請重新輸入") != -1:
                    print("retry ocr")
                elif resp.text.find("您的密碼即將到期") != -1 or resp.text.find("建議您立即變更密碼，是否立即變更？") != -1:
                    print("retry login")
                    with sess.post(logon_url, headers=user_headers, data={
                        "__EVENTTARGET": "",
                        "__EVENTARGUMENT": "",
                        "__VIEWSTATE": viewstate,
                        "__VIEWSTATEGENERATOR": viewstate_generator,
                        "ctl00$CPH1$txt_EmailId": user_email,
                        "ctl00$CPH1$txt_dwsp": "",
                        "ctl00$CPH1$txt_VerifyCode": "",
                        "ctl00$CPH1$confirm_txt": "",
                        "ctl00$CPH1$btnRelogin": "" 
                    }, allow_redirects=False) as resp2:
                        print(resp2.status_code)
                        if resp2.status_code != 302:
                            print("relogin failed")
                            exit(-1)
                        print(resp2.headers["Location"])
                        login_success_page = resp2.headers["Location"]
                        break
                else:
                    print("200 with unknowned situation ... QQ")
                    exit(-1)
            else:
                print(f"{resp.status_code} unknowned situation ... QQ")
                exit(-1)
    # get cookie
    send_get_req_txt(sess, login_success_page)
    send_get_req_txt(sess, "https://portal.wda.gov.tw/mooc/my_profile.php")

    for dt in range(1, 32):
        pg_idx = 1
        all_course = []

        st_date = (2022, 9, dt)
        en_date = (2022, 9, dt)
        print(f"process day {dt}")
        while True:
            cids, cids_time = query_course(sess, pg_idx, st_date, en_date)
            cids = [ query_correct_course_id_by_fancybox(sess, sig_cid, st_date)[f"{st_date[0]}-{str(st_date[1]).zfill(2)}-{str(st_date[2]).zfill(2)}"] for sig_cid in cids ]
            if pg_idx != 1 and set(cids).issubset(all_course):
                print("detect duplicated course")
                break
            if cids == []:
                print(f"detect null page on {pg_idx}")
                break
            all_course += cids
            print(cids)
            
            add_time(cids, cids_time)
            
            for cid, nid in cids:
                ref_url = f"https://portal.wda.gov.tw/mooc/my_profile.php?reqPage={pg_idx}&stYear={st_date[0]}&stMonth={st_date[1]}&stDay={st_date[2]}&endYear={en_date[0]}&endMonth={en_date[1]}&endDay={en_date[2]}"
                add_to_cart(sess, cid, nid, ref_url)
            pg_idx += 1
        if all_course == []:
            continue
        with sess.get("https://portal.wda.gov.tw/mooc/print_profile.php?print=1", headers=user_headers) as resp:
            if resp.status_code != 200:
                print(f"status code:{resp.status_code}")
                print(resp.text)
                exit(-1)

            with open(f"{username}/" + fname[:-4]+f"{str(st_date[1]).zfill(2)}{str(st_date[2]).zfill(2)}"+fname[-4:], 'wb') as f:
                for chunk in resp:
                   f.write(chunk)
        del_to_cart(sess, "https://portal.wda.gov.tw/mooc/print_profile.php")
    
    send_get_req_txt(sess, "https://portal.wda.gov.tw/mooc/co_search_record.php")
    for i in range(1, 31):
        print(f"process day {i}")
        download_region(sess, (2022, st_date[1], i), f"{username}/勞動部勞動力發展數位服務平台線上課程學習紀錄{str(st_date[1]).zfill(2)}.{str(i).zfill(2)}.pdf") 

if __name__ == "__main__":
    # pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\User\\Documents\\softwares\\tesseract-ocr\\tesseract.exe"
    pytesseract.pytesseract.tesseract_cmd = r"D:\tesseract\tesseract.exe"
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
            print(username, user_email, passwd)
            if not os.path.exists(username):
                os.mkdir(username)
            main(user_email, passwd, username + ".pdf")
            print(f"total_time: {total_time} min")
            with open('time.csv', 'a', newline='', encoding="utf-8") as f_object:  
                # Pass the CSV  file object to the writer() function
                writer_object = writer(f_object)
                # Result - a writer object
                # Pass the data in the list as an argument into the writerow() function
                writer_object.writerow([username, total_time])  
                # Close the file object
                f_object.close()