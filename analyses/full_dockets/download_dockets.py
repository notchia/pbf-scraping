import os
import requests
import pandas as pd

CWD = os.path.dirname(__file__)
TMP = os.path.join(CWD, "tmp/")

def download_pdfs(csvfile):
    df = pd.read_csv(csvfile)
    docketdir = os.path.join(TMP, "dockets")
    
    for i, entry in df.iterrows():
        print("downloading " + entry['Docket Number (Main)'])
        download_pdf(entry['Docket URL'], entry['Docket Number (Main)'], dirpath=docketdir)

def download_pdf(link, docketNumber, dirpath=''):
    """ Save PDF at given URL link to given temporary folder """
    
    if dirpath == '':
        dirpath = os.path.join(CWD, "tmp/pdfs/")
    if not os.path.isdir(dirpath):
        os.mkdir(dirpath)
    filepath = os.path.join(dirpath, '{0}.pdf'.format(docketNumber))
    
    r_pdf = requests.get(link, headers={"User-Agent": "ParsingThing"})
    with open(filepath, 'wb') as f:
        f.write(r_pdf.content)
        
# Main -----------------------------------------------------------------------
if __name__=="__main__":
    csvfile = os.path.join(TMP, "events_validated_trim.csv")
    download_pdfs(csvfile)
