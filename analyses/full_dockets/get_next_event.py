# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import os
import re
import pdfquery
import pandas as pd

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from io import StringIO

import funcs_parse as funcs

CWD = os.path.dirname(__file__)
TMP = os.path.join(CWD, "tmp/")
LINE_OFFSET = 2 # A bit arbitrary... may need to fix
LINE_WIDTH = 13#14.4 # Based on DPI of 72, line width of 0.20"
LINE_WIDTH_DOUBLE = 2*LINE_WIDTH


def parse_events(directory):
    
    infoList = []
    
    for item in sorted(os.listdir(directory)):
        item = os.path.join(directory, item)
        if os.stat(item).st_size > 0:
            info = get_newest_event(item)
            infoList.append(info)
    
    parsed = pd.DataFrame(infoList)
    parsed.to_csv(os.path.join(TMP,"parsed.csv"), index=False, mode='a')


def get_newest_event(filepath):

    parsedData = {}
    
    # Get PDF text as list of pages, then search for certain strings
    pageTextList = get_page_text(filepath)
    pages = find_string(pageTextList, "CALENDAR EVENTS")
    pages.append(0)
    pdfObj = pdfquery.PDFQuery(filepath)
    pdfObj.load(list(set(pages))) # Include first page also
    
    s = "Docket Number: "
    parsedData['docket_no'] = pdfObj.pq(f'LTTextLineHorizontal:contains("{s}")').text().split(s)[1].split(" ")[0].strip()
    parsedData['event_date'] = parse_recent_events(pdfObj, pages) #, parsedData['event_time'], parsedData['event_room'], parsedData['event_type']

    for key, value in parsedData.items():
        print(f"{key}:\t{value}")

    return parsedData


def get_page_text(filename):
    """Return list of strings corresponding to text on each page"""

    manager = PDFResourceManager()
    pages = []

    with open(filename, 'rb') as pdf:
        for i, page in enumerate(PDFPage.get_pages(pdf)):
            sio = StringIO()
            device = TextConverter(manager, sio, codec='utf-8', laparams=LAParams())
            interpreter = PDFPageInterpreter(manager, device)
            interpreter.process_page(page)
            
            text = sio.getvalue()
            
            pages.append(text)
            
            device.close()
            sio.close()

    return pages


def find_string(PDFpages, string):
    """Given list of text on pages of PDF, return list of page numbers in which
    the string is found """

    pagesFound = []
    for i, text in enumerate(PDFpages):
        if re.search(string, text):
            pagesFound.append(i)

    return pagesFound


def parse_recent_events(pdf, pages):
    """Get last event in list"""

    dateList = []

    # Start on last page, if more than one page of charges
    pages = sorted(pages)[::-1]
    pageNum = pages[0]
    
    try:
        # Find top of section and left of each column in current page
        eventTypeLoc = pdf.pq(funcs.query_contains_box(pageNum, 'Case Calendar Event Type'))
        dateLoc = pdf.pq(funcs.query_contains_box(pageNum, 'Schedule Start Date'))
        timeLoc = pdf.pq(funcs.query_contains_box(pageNum, 'Start Time'))
        judgeLoc = pdf.pq(funcs.query_contains_box(pageNum, 'Judge Name'))
        statusLoc = pdf.pq(funcs.query_contains_box(pageNum, 'Schedule Status'))
    
        y_top = float(eventTypeLoc.attr('y0')) 
        x_left_eventType = float(eventTypeLoc.attr('x0')) 
        x_left_date = float(dateLoc.attr('x0')) 
        x_left_time = float(timeLoc.attr('x0')) 
        x_left_judge = float(judgeLoc.attr('x0')) 
        x_left_status = float(statusLoc.attr('x0')) 
        
        coordinates = [x_left_date, y_top - 2*LINE_WIDTH, x_left_time, y_top]
        currentDates = pdf.pq(funcs.query_line(pageNum, coordinates)).text()
        currentDateList = currentDates.split()
        currentDate = currentDateList[0]
        dateList.append(currentDate)
        print("\tfirst date: " + currentDates)
        while currentDate != '':
            if len(currentDateList) == 1:
                coordinates[1] -= 2*LINE_WIDTH
                coordinates[3] -= 2*LINE_WIDTH
            elif len(currentDateList) == 2:
                coordinates[1] -= LINE_WIDTH
                coordinates[3] -= LINE_WIDTH          
            else:
                print("oh no")
            currentDates = pdf.pq(funcs.query_line(pageNum, coordinates)).text()
            print("\tnext date: " + currentDates)
            if currentDates:
                currentDateList = currentDates.split()
                currentDate = currentDateList[0]
                dateList.append(currentDate)
            else:
                currentDate = ''
    except Exception as e:
        print(e)
                
    return dateList[-1]

def test():
    csvfile = os.path.join(TMP, "events_validated_trim.csv")
    df = pd.read_csv(csvfile)
    
    
# Main -----------------------------------------------------------------------
if __name__=="__main__":
    directory = os.path.join(TMP, "dockets")
    parse_events(directory)
    