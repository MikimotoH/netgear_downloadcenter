#!/usr/bin/env python3
# coding: utf-8
from fuzzywuzzy import fuzz
import harvest_utils
from harvest_utils import waitClickable, waitVisible, waitText, getElems, \
        getElemText,getFirefox,driver,dumpSnapshot,\
        getText,getNumElem,waitTextChanged,waitElem
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, \
        TimeoutException, StaleElementReferenceException, \
        WebDriverException
from infix_operator import Infix
import os
from os import path
import time
import sys
import sqlite3
import re

fzeq=Infix(fuzz.token_set_ratio)
preq=Infix(fuzz.partial_token_set_ratio)
dlDir= path.abspath('firmware_files/')
driver,conn=None,None
modelName=""

def uprint(msg:str):
    sys.stdout.buffer.write((msg+'\n').encode('utf8'))

def sql(query:str, var=None):
    global conn
    csr=conn.cursor()
    csr.execute(query, var)
    if not query.upper().startswith("SELECT"):
        conn.commit()

def waitUntil(cond, pollFreq:float=0.5, timeOut:float=40):
    timeElapsed=0.0
    while timeElapsed < timeOut:
        timeBegin=time.time()
        if cond()==True:
            return True
        time.sleep(pollFreq)
        timeElapsed += (time.time()-timeBegin)
    print("Error Timeout cond()=%s"%(str(cond)))
    return False

catSelCss="#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_adsPanel_lbProductCategory"
famSelCss="#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_adsPanel_lbProductFamily"
prdSelCss="#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_adsPanel_lbProduct"
catWaitingCss="#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_adsPanel_updProgress > div > img"
famWaitingCss="#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_adsPanel_UpdateProgress1 > div > img"
prdWaitingCss='#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_adsPanel_upProgProductLoader > div > img'
numResultsCss='#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_adsPanel_lvwAllDownload_lblAllDownloadResult'

#"#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_adsPanel_upProgProductLoader > div:nth-child(1) > img:nth-child(1)"

def main():
    startCatIdx = int(sys.argv[1]) if len(sys.argv)>1 else 0
    startFamIdx = int(sys.argv[2]) if len(sys.argv)>2 else 0
    startPrdIdx = int(sys.argv[3]) if len(sys.argv)>3 else 0
    global driver,conn
    harvest_utils.driver=getFirefox(dlDir)
    driver = harvest_utils.driver
    conn=sqlite3.connect('netgear.sqlite3')
    csr=conn.cursor()
    csr.execute("CREATE TABLE IF NOT EXISTS TFiles("
        "brand TEXT,"
        "category TEXT,"
        "family TEXT,"
        "product TEXT,"# -- is model
        "desc TEXT,"# -- is fileName
        "href TEXT,"
        "file_sha1 TEXT,"
        "PRIMARY KEY (product,desc)"
        ")");
    conn.commit()
    driver.get('http://downloadcenter.netgear.com/')
    #click DrillDown
    waitClickable('#ctl00_ctl00_ctl00_mainContent_localizedContent_bodyCenter_BasicSearchPanel_btnAdvancedSearch').click()
    #
    # wait Page2
    try:
        catSel=Select(waitClickable(catSelCss))
        numCat=len(catSel.options)
        for catIdx in range(startCatIdx,numCat):
            catSel=Select(waitClickable(catSelCss))
            print('catIdx=',catIdx)
            catTxt=catSel.options[catIdx].text
            uprint('catTxt='+catTxt)
            catSel.select_by_index(catIdx)
            waitTextChanged(famSelCss)
            famSel=Select(waitClickable(famSelCss))
            numFam=len(famSel.options)
            for famIdx in range(startFamIdx,numFam):
                famSel=Select(waitClickable(famSelCss))
                print('famIdx=',famIdx)
                startFamIdx=0
                famTxt =famSel.options[famIdx].text
                uprint('famTxt='+famTxt)
                famSel.select_by_index(famIdx)
                waitTextChanged(prdSelCss)
                prdSel=Select(waitClickable(prdSelCss))
                numPrd=len(prdSel.options)
                for prdIdx in range(startPrdIdx,numPrd):
                    prdSel=Select(waitClickable(prdSelCss))
                    startPrdIdx=0
                    print("catIdx=%d, famIdx=%d, prdIdx=%d"%(catIdx,famIdx,prdIdx))
                    prdTxt=prdSel.options[prdIdx].text
                    uprint('cat,fam,prd=("%s","%s","%s")'%(catTxt,famTxt,prdTxt))
                    prdWaiting = waitElem(prdWaitingCss)
                    prdSel.select_by_index(prdIdx)
                    WebDriverWait(driver, 5, poll_frequency=0.5).\
                        until(lambda x:prdWaiting.is_displayed()==True)
                    WebDriverWait(driver, 60, poll_frequency=0.5).\
                        until(lambda x:prdWaiting.is_displayed()==False)
                    #waitUntil(lambda:prdWaiting.is_displayed()==True)
                    #waitUntil(lambda:prdWaiting.is_displayed()==False)
                    numResults=waitText(numResultsCss,3)
                    print('numResults=',numResults)
                    if numResults is None:
                        continue
                    numResults=int(re.search(r"\d+", numResults).group(0))
                    if numResults >10:
                        showMore=waitClickable("#lnkAllDownloadMore",3)
                        showMore.click()
                    try:
                        erItems=getElems('a.register-product.navlistsearch',3)
                    except TimeoutException:
                        erItems=getElems('div#LargeFirmware > ul > li > div > p > a.navlistsearch',3)

                    if len(erItems) != numResults:
                        print('Error, numResults=%d, but len(erItems)=%d'
                            %(numResults,len(erItems)))
                    for erItem in erItems:
                        if not erItem.is_displayed():
                            continue
                        desc=getElemText(erItem)
                        uprint('desc="%s"'%desc)
                        href=erItem.get_attribute('data-durl')
                        if not href:
                            href=erItem.get_attribute('href')
                        print('href=',href)
                        if not href.startswith('http'):
                            print('Error: href=',href)
                        sql("INSERT OR REPLACE INTO TFiles"
                            "(brand,category,family,product,desc,href)VALUES"
                            "('Netgear',:catTxt,:famTxt,:prdTxt,:desc,:href)",
                            locals())
                        uprint('INSERT '
                            '("%(catTxt)s","%(famTxt)s","%(prdTxt)s","%(desc)s","%(href)s")'
                            %locals())
    except Exception as ex:
        import ipdb; ipdb.set_trace()
        print(ex)
        import traceback; traceback.print_exc()
    print('-- terminate firefox')
    driver.quit()


if __name__=='__main__':
    try:
        main()
    except Exception as ex:
        import ipdb; ipdb.set_trace()
        print(str(ex))
        dumpSnapshot(str(ex))
