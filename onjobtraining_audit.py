from typing import Tuple
from onjobtraining_lib import create_sess, get_audit_result, get_writeoff_data
from requests import Session
from datetime import datetime
import csv
from logging import info
from utils import create_logger_to_file
import argparse
from os import chdir
from pprint import pprint
 
def download_pdf(
    account:str,
    passwd:str,
    wid:str
):
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
    
    sess = create_sess(
            args.account,
            args.password
        )
    audit_str = get_audit_result(sess, (2022, args.month))
    if audit_str == "":
        info("audit not passed")
        return
    wfid = get_writeoff_data(sess, (2022, args.month))["writeOffId"]
    info(f"get wfid: {wfid}")
    
if __name__ == "__main__":
    main()