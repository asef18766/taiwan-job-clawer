import logging
from datetime import datetime
from typing import List
import csv
def create_logger_to_file(fname:str):
    logging.basicConfig(filename=fname, level=logging.INFO, encoding="utf-8")

def check_date_exsist(year:int, month:int, day:int, hrs=0, mins=0, secs=0)->bool:
    try:
        datetime(year, month, day, hrs, mins, secs)
    except ValueError as e:
        if str(e) == "day is out of range for month":
            return False
        else:
            raise e
    return True

def datetime_from_tw_fmt(s:str)->datetime:
    y, m, d = s.split("/")
    return datetime(int(y) + 1911, int(m), int(d))

def append_to_csv(fname: str, line: List[str]):
    with open(fname, 'a', newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(line)
