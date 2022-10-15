from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime


def create_sess(
    account="L120966821",
    passwd="Zzaaqq831109!"
) -> requests.Session:
    sess = requests.session()
    capcha_url = ""
    capcha_code = ""

    with sess.get("https://onjobtraining.wda.gov.tw/WDATraining/?i=5#") as resp:
        soup = BeautifulSoup(resp.text, "html.parser")
        capcha_url = soup.find_all("img", {"id": "imgCheckCode"})[0]["src"]
    with sess.get(f"https://onjobtraining.wda.gov.tw{capcha_url}") as resp:
        pass
        # with open("capcha.jpg", "wb") as fp:
        #    fp.write(resp.content)
    with sess.post("https://onjobtraining.wda.gov.tw/WDATraining/Login/GetCheckCodeTEXT", headers={
        "Content-Type": "application/json; charset=utf-8"
    }) as resp:
        capcha_code = resp.text.replace('"', "").strip()
    with sess.post("https://onjobtraining.wda.gov.tw/WDATraining/Login/Login", json={
        "loginInfoVM": {
            "Account": account,
            "AdminType": 0,
            "CheckWord": capcha_code,
            "ClientIP": "",
            "Identity": 5,
            "Password": passwd
        }
    }) as resp:
        res = resp.json()
        if not res["IsSuccess"]:
            print(res)
            raise Exception(res["ExceptionMessage"])
    sess.get("https://onjobtraining.wda.gov.tw/WDARestart/Account/Sso")
    return sess


def get_usr_fin_info(sess: requests.Session) -> List[str]:
    with sess.get("https://onjobtraining.wda.gov.tw/WdaRestart/Api/Labor/GetMeDetail/") as resp:
        usr_data = resp.json()
        return [
            usr_data["finCode"],
            usr_data["finBranchCode"],
            usr_data["finName"],
            usr_data["finBranchName"],
            usr_data["finAccount"]
        ]


def append_to_csv(fname: str, line: List[str]):
    with open(fname, 'a', newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(line)

def del_course(sess: requests.Session, cid:str):
    with sess.get(f"https://onjobtraining.wda.gov.tw/WdaRestart/Api/Labor/DeleteCourseRegisterAtHome/?registerId={cid}") as resp:
        print(resp.json())

def add_course(sess: requests.Session, dates: List[Tuple[int, int, int]], time_period: Tuple[Tuple[int, int], Tuple[int, int]]):
    usr_dates = [
        datetime(d[0], d[1], d[2])
        for d in dates
    ]
    tp = [
        datetime(dates[0][0], dates[0][1], dates[0][2],
                 time_period[0][0], time_period[0][1], 0),
        datetime(dates[0][0], dates[0][1], dates[0][2],
                 time_period[1][0], time_period[1][1], 0)
    ]
    hrs, mins = (tp[1] - tp[0]).seconds // 3600, ((tp[1] - tp[0]).seconds // 60) % 60
    apply_info = []

    with sess.get("https://onjobtraining.wda.gov.tw/WdaRestart/Api/Labor/GetCaseNoListAtHome/") as resp:
        data = resp.json()

        for d in data:
            red_start = datetime.strptime(
                d["reduceStart"], "%Y-%m-%dT%H:%M:%S")
            red_ed = datetime.strptime(d["reduceEnd"], "%Y-%m-%dT%H:%M:%S")
            for usr_d in usr_dates:

                if not (red_start <= usr_d <= red_ed):
                    break
            else:
                apply_info.append(d)

    assert len(apply_info) == 1
    apply_info = apply_info[0]
    # print(apply_info)
    for d in usr_dates:
        with sess.post("https://onjobtraining.wda.gov.tw/WdaRestart/Api/Labor/SaveCourseRegisterAtHome/", json={
            "registerId": "", 
            "isWithdraw": False, 
            "applyId": apply_info["key"], 
            "applyDate": apply_info["applyDate"], 
            "reduceStart": apply_info["reduceStart"], 
            "reduceEnd": apply_info["reduceEnd"], 
            "expectedDate": d.strftime("%Y-%m-%d"), 
            "expectedTimeStart": str(tp[0].hour).zfill(2), 
            "expectedTimeEnd": str(tp[1].hour).zfill(2), 
            "expectedTimeStartMin": str(tp[0].min).zfill(2), 
            "expectedTimeEndMin": str(tp[1].min).zfill(2),
            "minDate": apply_info["reduceStart"], 
            "expectedHours": hrs, 
            "expectedMinute": mins
            }) as resp:
            if resp.status_code != 200 or (resp.json()["data"] != "儲存成功" and resp.json()["message"] != "此課程時間已與其他時間重複,無法登錄"):
                print(resp.status_code)
                raise Exception(resp.text)
    usr_dates_fmt = [ d.strftime("%Y-%m-%dT00:00:00") for d in usr_dates ]
    with sess.get("https://onjobtraining.wda.gov.tw/WdaRestart/Api/Labor/QueryCourseReplayAtHome/?param.laborId=&param.keyword=&param.sorting=CreatedDate&param.sortingDesc=true&param.currentPage=1&param.pageSize=1000&") as resp:
        data = resp.json()["data"]
        for d in data:
            if d["expectedDate"] in usr_dates_fmt:
                with sess.post("https://onjobtraining.wda.gov.tw/WdaRestart/Api/Labor/SaveCourseReplayAtHome/", json={
                    "registerId":d["registerId"],
                    "expectedDate":d["expectedDate"],
                    "actualTimeStart":d["expectedTimeStart"],
                    "actualTimeEnd":d["expectedTimeEnd"],
                    "actualTimeStartMin":d["expectedTimeStartMin"],
                    "actualTimeEndMin":d["expectedTimeEndMin"],
                    "actualHours":d["expectedHours"],
                    "actualMinute":d["expectedMinute"],
                    "isAttend":False,
                    "isAttendDisplay":None,
                    "caseNo":None,
                    "applyDate":d["applyDate"]
                }) as resp:
                    if resp.status_code != 200 or resp.json()["data"] != "儲存成功":
                        print(resp.status_code)
                        print(resp.text)
                        raise Exception()


def main():
    with open('usr_table.csv', newline='', encoding="utf-8") as csvfile:
        rows = csv.reader(csvfile)
        for idx, row in enumerate(rows):
            usr_r_name = row[1]
            usr_com_name = row[2]
            usr_id = row[3]
            usr_pw = row[6]
            if row[11] == "":
                continue
            if idx < 122:
                continue
            try:
                print(f"processing {usr_r_name}...")
                sess = create_sess(usr_id, usr_pw)
                print("login done!")
            except:
                print(f"{usr_r_name} can not login!", file=open(
                    "except.log", "a", encoding="utf-8"))
                continue
            usr_c_dates = [(2022, 10, int(d)) for d in row[11].split(",")]
            usr_c_tp = tuple(tuple(map(int, i.split(":")))
                             for i in row[9].split("~"))

            add_course(sess, usr_c_dates, usr_c_tp)
            #append_to_csv("fin_info.csv", [usr_r_name, usr_com_name] + get_usr_fin_info(sess))

if __name__ == "__main__":
    main()
