import argparse
import os
from taiwanjobs_lib import main as taiwanjob_main
from csv import writer
import platform
import pytesseract

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("username",     help="user Chinese name")
    parser.add_argument("account",      help="user account, usually email")
    parser.add_argument("password",     help="user password bj4")
    parser.add_argument("month",        help="the month they had courses", type=int)
    parser.add_argument("fname_suffix", help="the suffix of result file, usually shall ends with .pdf")
    parser.add_argument("dst_f",        help="destination folder for storing all user records")
    parser.add_argument("csv",          help="csv location")
    args = parser.parse_args()
    if not os.path.exists(f"{args.dst_f}/{args.username}"):
        os.makedirs(f"{args.dst_f}/{args.username}", exist_ok=True)
    os.chdir(f"{args.dst_f}")
    total_time = taiwanjob_main(
        args.fname_suffix, 
        args.month, 
        args.username,
        args.account, 
        args.password
    )

    with open(args.csv, 'a', newline='', encoding="utf-8") as f_object:  
        writer_object = writer(f_object)
        writer_object.writerow([args.username, total_time])  
        f_object.close()

    
if __name__ == "__main__":
    if platform.node() == "LAPTOP-KQCO29TK":
        pytesseract.pytesseract.tesseract_cmd = "C:\\Users\\User\\Documents\\softwares\\tesseract-ocr\\tesseract.exe"
    else:
        raise Exception("please define tesseract.exe path")
    main()