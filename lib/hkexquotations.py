import requests
import re
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as bs
from datetime import date, datetime


ISO_CCY = ["HKD","AUD","CAD","CNY","EUR","GBP","JPY","SGD","USD"]
DB_CONFIG = {'usr': 'solo_bros',
             'pwd': '0n9SoloBros!',
             'host': '192.168.1.186',
             'port': '3307',
             'db': 'solo_bros',
             'tbl': 'hkex_prc'
             }

class NoQuotationsException(Exception):
    def __init__(self, url):
        self.err_msg = f"Quotations is yet avaliable on:\n {url}"

def get_price(cob_date = None):

    if not cob_date: cob_date = date.today()
    url = f"https://www.hkex.com.hk/eng/stat/smstat/dayquot/d{cob_date:%y%m%d}e.htm"

    # Web scrap to get the whole document #
    page = requests.get(url)
    soup = bs(page.content, 'html.parser')
    fragments = soup.find_all('pre')
    fragments = map(lambda f: f.text, fragments)
    doc = ''.join(fragments)


    # Regex #
    section_ptrn = r"\s{5,}QUOTATIONS(.|\n|\r)*?-{5,}"
    stk_code_ptrn = r"[0-9]{1,4}"
    annotation_ptrn = r"(?:\*|#)?"
    ccy_ptrn = f"(?:{'|'.join(ISO_CCY)})"
    prc_ptrn = r"(?:\d{1,3}\.\d{2,4}|-|N/A)"
    vol_ptrn = r"(?:(?:\d{1,3},)*\d{1,3}|-|N/A)"
    quotaion_ptrn = "\\n" + r"\s+".join([annotation_ptrn, f"({stk_code_ptrn})", ".*?", f"({ccy_ptrn})",
                                        f"({prc_ptrn})", f"({prc_ptrn})", f"({prc_ptrn})", f"({vol_ptrn})" + "\\r\\n",
                                        f"({prc_ptrn})", f"({prc_ptrn})", f"({prc_ptrn})", f"({vol_ptrn})"]) + "\\r"
    suspended_ptrn = "\\n" + r"\s+".join([annotation_ptrn, f"({stk_code_ptrn})", ".*?", f"({ccy_ptrn})",  "TRADING SUSPENDED"]) + "\\r"

    # Regex to find the QUOTATTIONS section string#
    pattern = re.compile(section_ptrn, re.MULTILINE)
    quotation_section = pattern.search(doc)
    if not quotation_section:
        raise NoQuotationsException(url)
    sec = quotation_section.group(0)

    # Regex to find all quoatation in the section into Dataframes #
    pattern = re.compile(quotaion_ptrn, re.MULTILINE)
    qs = pattern.findall(sec)
    qs_df = pd.DataFrame(qs, columns=['code', 'ccy', 'open', 'ask', 'high', 'shares_traded', 'close', 'bid', 'low', 'turnover'])

    #pattern = re.compile(suspended_ptrn, re.MULTILINE)
    #suspended = pattern.findall(sec)
    #suspended_df = pd.DataFrame(suspended, columns=['code', 'ccy'])
    
    # Massage the Dataframes #
    #qs_df['dt'] = pd.to_datetime(cob_date)
    #suspended_df['dt'] = pd.to_datetime(cob_date)
    qs_df['is_suspended'] = False
    #suspended_df['is_suspended'] = True
    qs_df = qs_df.replace('(?:N/A|-)', np.NaN, regex=True)
    qs_df[['open', 'ask', 'high', 'shares_traded', 'close', 'bid', 'low', 'turnover']] = qs_df[['open', 'ask', 'high', 'shares_traded', 'close', 'bid', 'low', 'turnover']].replace(",", "", regex=True)
    qs_df[['open', 'ask', 'high', 'shares_traded', 'close', 'bid', 'low', 'turnover']] = qs_df[['open', 'ask', 'high', 'shares_traded', 'close', 'bid', 'low', 'turnover']].apply(pd.to_numeric)
    #qs_df.info()
    #suspended_df.info()

    return qs_df

