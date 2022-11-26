import csv
import os
from typing import List
from PyPDF2 import PdfFileReader, PdfFileWriter
from logging import info
for com in [
    "高桀"
]:
    users = []
    with open('account.csv', newline='', encoding="utf-8") as csvfile:
        info(f"processing {com}")
        rows = csv.reader(csvfile)
        for rid, row in enumerate(rows):
            if row[2] != com:
                continue
            username = row[1]
            users.append(username)
    pdfs:List[str] = []
    for folder in users:
        pdfs += [f"{folder}/{i}" for i in sorted(os.listdir(folder))]
    #from pprint import pprint
    #pprint(pdfs)
    writer = PdfFileWriter()

    for pdf_path in pdfs:
        rd = PdfFileReader(pdf_path)
        for i in range(len(rd.pages)):
            writer.addPage(rd.getPage(i))
    with open(f"{com}.pdf", "wb") as output:
        writer.write(output)