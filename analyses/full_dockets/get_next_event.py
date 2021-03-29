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
LINE_WIDTH = 14.4 # Based on DPI of 72, line width of 0.20"

def get_newest_event(filepath):

    parsedData = {}
    
    # Get PDF text as list of pages, then search for certain strings
    pageTextList = get_page_text(filepath)
    pages = find_string(pageTextList, "CALENDAR EVENTS")
    pdfObj = pdfquery.PDFQuery(filepath)
    pdfObj.load(set([0] + pages)) # Include first page also
    
    s = "Docket Number"
    parsedData['docket_no'] = pdfObj.pq(f'LTTextLineHorizontal:contains({s})').text().split({s})[1].strip()
    parsedData['event_date'], parsedData['event_time'], parsedData['event_room'], parsedData['event_type'] = parse_recent_events(pdfObj, pages)


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

    # Start on last page, if more than one page of charges
    pages = sorted(pages)[::-1]
    pageNum = pages[0]
    
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
    
    # Find bottom of section in current page
    bottomOfSectionLoc = pdf.pq(funcs.query_contains_box(pageNum, 'CONFINEMENT INFORMATION'))
    bottomOfPageLoc = pdf.pq(funcs.query_contains_box(pageNum, 'CPCMS 9082'))
    if bottomOfSectionLoc.text() and bottomOfPageLoc.text():
        y_bottom = max(float(bottomOfSectionLoc.attr('y1')),
                       float(bottomOfPageLoc.attr('y1')))
    else:
        if bottomOfSectionLoc.text():
            y_bottom = float(bottomOfSectionLoc.attr('y1'))
        elif bottomOfPageLoc.text():
            y_bottom = float(bottomOfPageLoc.attr('y1'))
    
    # Find bottom-most entry 
    coordinates = [x_left_date, y_bottom, x_left_time, y_bottom + 2*LINE_WIDTH]
    print(coordinates)
    currentDate = pdf.pq(funcs.query_line(pageNum, coordinates)).text()
    while currentDate == '':
        coordinates[1] += 2*LINE_WIDTH
        coordinates[3] += 2*LINE_WIDTH
        currentDate = pdf.pq(funcs.query_line(pageNum, coordinates)).text()

    return currentDate

def test():
    csvfile = os.path.join(TMP, "events_validated_trim.csv")
    df = pd.read_csv(csvfile)
    
    