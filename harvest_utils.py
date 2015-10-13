from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.proxy import Proxy, ProxyType
import time
from time import sleep
from urllib import parse
from selenium.common.exceptions import NoSuchElementException, \
        TimeoutException, StaleElementReferenceException, \
        WebDriverException
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement


class Waiter:
    def __init__(self,driver):
        self._driver =driver
        self._wait = WebDriverWait(driver, 60, poll_frequency=3.0)
    def Elem(self,css:str) -> WebElement:
        return self._wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,css)))
    

    def Elems(self,css:str) -> [WebElement] :
        return self._wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,css)))

    @staticmethod
    def getElemText(e:WebElement,trialCount=20,pollInterval=3,default=None) -> str:
        for trial in range(trialCount):
            try:
                return e.text
            except (StaleElementReferenceException, NoSuchElementException, TimeoutException):
                sleep(pollInterval)
        return default

    def Text(self,css:str,trialCount=20,pollInterval=3,default=None) -> str:
        try:
            e = self.Elem(css)
        except TimeoutException:
            print('[Waiter.Text]TimeoutException css=%s'%css)
            return default
        return Waiter.getElemText(e,trialCount,pollInterval,default)

    def Texts(self,css:str,trialCount=20,pollInterval=3,default=None) -> [str]:
        try:
            es = self.Elems(css)
        except TimeoutException:
            print('[Waiter.Text]TimeoutException css=%s'%css)
            return [default]
        return [Waiter.getElemText(e,trialCount,pollInterval,default) for e in es]

    @staticmethod
    def getElemAttrib(e:WebElement,attName:str, trialCount=20,pollInterval=3,default=None) -> str:
        for trial in range(trialCount):
            try:
                return e.get_attribute(attName)
            except (StaleElementReferenceException, NoSuchElementException, TimeoutException):
                sleep(pollInterval)
        return default
    def Attrib(self,css:str,attName:str, trialCount=20,pollInterval=3,default=None) -> str:
        try:
            e = self.Elem(css)
        except TimeoutException:
            print('[Waiter.Text]TimeoutException css=%s'%css)
            return default
        return Waiter.getElemAttrib(e,attName,trialCount,pollInterval,default)

    def Visible(self,css:str) -> WebElement :
        return self._wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,css)))
    def Clickable(self,css:str) -> WebElement :
        return self._wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,css)))

    def ElemN(self, css:str, n:int) -> [WebElement] :
        for x in range(30):
            try:
                es = self.elems(css)
                if len(es)>=n:
                    return es
            except TimeoutException:
                pass
            self._driver.execute_script('window.scrollBy(0,800);')
            print('window.scrollBy(0,800); sleep(2);')
            sleep(2)
        print('[Waiter.elemN] Insufficient elements, expected=%d, '
                'actual=%d'%(n, len(es)))
        raise TimeoutException('[waitElemN] Insufficient elements'
                ', expected=%d, actual=%d'%(n, len(es)))

    def queryAllText(self,css):
        n = self._driver.execute_script("return document.querySelectorAll('%(css)s').length"%locals())
        txts=[]
        for i in range(n):
            for trial in range(10):
                try:
                    txt = self._driver.execute_script(
                            "return document.querySelectorAll('%(css)s')[%(i)d].textContent"%locals())
                    break
                except WebDriverException:
                    sleep(2)
            txts += [txt.strip()]
        return txts

    def waitTextChanged(self, css:str,oldText:str) -> str:
        sign = 1
        for x in range(30):
            e = self.elem(css)
            try:
                newText = e.text
                if newText != oldText:
                    return newText
            except StaleElementReferenceException:
                pass
            self._driver.execute_script('window.scrollBy(0,%d);'%( 5*sign ))
            print('window.scrollBy(0,%d); sleep(2);'%(5*sign))
            sign = -sign;
            sleep(2)
        raise TimeoutException('[waitTextChanged] oldText="%s", '
                'newText="%s"'%(oldText,newText))

        

# -------

def getFirefox(tempDir='/tmp', showImage=1):
    """get Firefox Webdriver object
    :param showImage: 2 = don't show, 1=show
    """
    proxy = Proxy(dict(proxyType=ProxyType.AUTODETECT))
    profile = webdriver.FirefoxProfile()
    profile.set_preference("plugin.state.flash", 0)
    profile.set_preference("plugin.state.java", 0)
    profile.set_preference("media.autoplay.enabled", False)
    # 2=dont_show, 1=normal
    profile.set_preference("permissions.default.image", showImage)
    profile.set_preference("webdriver.load.strategy", "unstable")
    # automatic download
    # 2 indicates a custom (see: browser.download.dir) folder.
    profile.set_preference("browser.download.folderList", 2)
    # whether or not to show the Downloads window when a download begins.
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", tempDir)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", 
        "application/octet-stream"+\
        ",application/zip"+\
        ",application/x-rar-compressed"+\
        ",application/x-gzip"+\
        ",application/msword")
    return webdriver.Firefox(firefox_profile=profile, proxy=proxy)


def safeFileName(s:str) -> str:
    return parse.quote(s, ' (),')


driver=None

def waitElem(css:str,timeOut:float=60) -> WebElement:
    global driver
    wait = WebDriverWait(driver, timeOut, poll_frequency=3.0)
    return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,css)))

def mouseClick(css:str):
    global driver
    actions = ActionChains(driver)
    el = waitElem(css)
    actions.move_to_element(el).click().perform()


def waitVisible(css:str,timeOut:float=60) -> WebElement :
    global driver
    wait = WebDriverWait(driver, timeOut, poll_frequency=3.0)
    return wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,css)))

def getElems(css:str,timeOut:float=60) -> [WebElement]:
    global driver
    waitVisible(css,timeOut)
    return driver.find_elements_by_css_selector(css)

def getText(css:str,timeOut:int=60)->str:
    global driver
    interval=3
    timeElapsed=0
    while timeElapsed < timeOut:
        beginTime=time.time()
        try:
            return driver.execute_script("return "
                "document.querySelector('%s').textContent"%css)
        except WebDriverException as ex:
            print(ex)
            time.sleep(interval)
            timeElapsed+=(time.time()- beginTime)
    return None

def getNumElem(css:str):
    global driver
    return driver.execute_script("return "
        "document.querySelectorAll('%s').length"%css)

def getElemText(elem:WebElement, timeOut:float=60) -> str:
    timeElapsed=0
    pollFreq=3
    while timeElapsed < timeOut:
        try:
            return elem.text.strip()
        except StaleElementReferenceException:
            time.sleep(pollFreq)
            timeElapsed+=pollFreq
            continue
    raise TimeoutException("time out getElemText")


def waitText(css:str,timeOut:float=60) -> str :
    timeElapsed=0
    pollFreq=3
    while timeElapsed < timeOut:
        beginTime = time.time()
        try:
            return waitVisible(css, pollFreq).text
        except (TimeoutException, StaleElementReferenceException):
            time.sleep(pollFreq)
            timeElapsed += (time.time()-beginTime)
            continue
        except Exception as ex:
            print(ex)
            return None
    return None


def waitClickable(css:str, timeOut:float=60) -> WebElement :
    global driver
    wait = WebDriverWait(driver, timeOut, poll_frequency=3.0)
    return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,css)))

def waitTextChanged(css:str,oldText:str=None) -> str:
    if oldText is None:
        oldText=getText(css)
    for x in range(20):
        newText = getText(css)
        if newText != oldText:
            return newText
        sleep(3)
    raise TimeoutException('[waitTextChanged] oldText="%s", '
            'newText="%s"'%(oldText,newText))

def dumpSnapshot(msg:str):
    global driver
    fileTitle = safeFileName(msg) 
    driver.save_screenshot(fileTitle+'.png')
    with open(fileTitle+'.html', 'w', encoding='utf-8-sig') as fout:
        fout.write(driver.page_source)

