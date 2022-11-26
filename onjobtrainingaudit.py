from typing import Tuple
from onjobtraining_lib import create_sess, append_to_csv
from requests import Session
from pprint import pprint
from datetime import datetime
import csv
from logging import info

def datetime_from_tw_fmt(s:str)->datetime:
    y, m, d = s.split("/")
    return datetime(int(y) + 1911, int(m), int(d))

def get_audit_result(sess:Session, year_n_month:Tuple[int, int]):
    usr_date = datetime(year_n_month[0], year_n_month[1], 1)
    plan_key = None
    with sess.get("https://onjobtraining.wda.gov.tw/WdaRestart/Api/Labor/GetCaseNoListWriteOff/") as resp:
        for k in resp.json():
            start_date, end_date = k["name"][13:-1].split(" ~ ")
            start_date = datetime_from_tw_fmt(start_date)
            end_date = datetime_from_tw_fmt(end_date)
            if start_date <= usr_date <= end_date:
                if plan_key != None:
                    raise Exception("detect dulplicated range")
                plan_key = k["key"]
    if plan_key is None:
        raise Exception("could not find any matched key")
    with sess.get(f"https://onjobtraining.wda.gov.tw/WdaRestart/Api/Labor/QueryLaborWriteOff/?param.year={year_n_month[0]}&param.applyId={plan_key}&") as resp:
        for k in resp.json():
            if usr_date == datetime.strptime(k["writeOffMonth"], "%Y-%m-%dT%H:%M:%S"):
                return k["writeOffResult"] == "審查通過"
        else:
            raise Exception("could not find specify month")
def main():
    with open('account.csv', newline='', encoding="utf-8") as csvfile:
        rows = csv.reader(csvfile)
        for idx, row in enumerate(rows):
            if idx < 92:
                continue
            info(f"processing {row[1]}")
            sess = create_sess(row[3], row[6])
            append_to_csv("audit.csv", [row[1], str(get_audit_result(sess, (2022, 11)))])
if __name__ == "__main__":
    main()