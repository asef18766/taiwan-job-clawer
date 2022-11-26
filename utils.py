import logging
from datetime import datetime

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