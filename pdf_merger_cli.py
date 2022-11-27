from os import chdir
import os
from typing import List
from PyPDF2 import PdfFileReader, PdfFileWriter
from logging import info
from utils import create_logger_to_file
from datetime import datetime
import argparse

def merge_to_pdfs(users:List[str], com:str):
    info(f"user: {users}")
    info(f"com: {com}")
    pdfs:List[str] = []
    for folder in users:
        pdfs += [f"{folder}/{i}" for i in sorted(os.listdir(folder)) if i.endswith(".pdf")]
    
    writer = PdfFileWriter()

    for pdf_path in pdfs:
        rd = PdfFileReader(pdf_path)
        for i in range(len(rd.pages)):
            writer.addPage(rd.getPage(i))
    with open(f"{com}.pdf", "wb") as output:
        writer.write(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work_dir", help="working directory, usually the month folder", required=True)
    parser.add_argument("--users", help="the users to be merge into pdf, seperate them with a space", nargs='+', required=True, type=str)
    parser.add_argument("--com", help="company name")
    args = parser.parse_args()
    
    chdir(args.work_dir)
    create_logger_to_file(datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".log_merger")
    info(f"arg obtain user count: {args.users}")
    merge_to_pdfs(args.users, args.com)
    
if __name__ == "__main__":
    main()