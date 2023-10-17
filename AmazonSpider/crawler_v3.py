#%%
#region import
# import sys
# sys.path.append("../")
from abc import abstractmethod
import traceback
from selenium import webdriver
from Server import DBMongo
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import time
from datetime import datetime
import requests
from Config.settings import *
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, StaleElementReferenceException
import re
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError
import pymongo
import pickle
import json
from webdriver_manager.chrome import ChromeDriverManager
import zipfile
import os
import copy
import random
from Browser import ChromeWithHelium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from lxml import etree
#endregion


class BaseCrawler():
    def __init__(self):
        self.__browser = None # MyBrowser(headers=self.__cfg.getHeaders(), proxies=self.__cfg.proxies)

    def request(self, data=None, proxies=None):
        

#region class
class BaseCrawler():

    chromes = {} #chromes pool
    options = [] #browser settings
    cookies = [] #browser cookies
    __proxies = [] #proxy server

    fURL = None
    navIndicator = None
    validateAsin = False
    initComplete = True
    useMyproxy = False
    helium = False
    collection = "untitled-collection"
    
    def __init__(self, targets, targets_signal=AUTO, threads=4, autoProxy=False, headless=False, verbose = True):

        self.db = DBMongo()
        self.options = BROWSER['options']
        self.threads = threads
        self.headless = headless
        self.targets_signal = targets_signal
        self.verbose = verbose
        self.targets = targets
        
        os.environ['WDM_LOG_LEVEL'] = '0'

        # preparing the total number of targets have to connect mysql
        # that is why we write two if verbose statement
        #if we put the mysql statement into __crawl(), it will connect sql over and over again
        # therefore we prepare the total amout first in the element cause it's fixed to each time of crawling data.
        if self.verbose:
            url = 'http://192.168.2.94:8080/lizhi/'
            myobj = {'total':'static'}
            # myobj = {'total':'sports_outdoors'}
            x = requests.post(url, data = myobj)
            total_num = json.loads(x.text)
            self.total = total_num
            print(f'The total amount of asins would be {self.total}...')
            # myobj = {'total_seller':''}
            # x = requests.post(url, data = myobj)
            # total_num = json.loads(x.text)
            # self.total = total_num
            # print(f'The total amount of sellers would be {self.total}...')

        if AUTOCOOKIES:
            with open("dump/amazonCookies.json", "r") as f:
                self.setCookies(json.load(f))

        # fetch proxies from "free-proxy-list"
        if autoProxy:
            print("Fetching proxies from 'free-proxy-list'.... ")
            self.__proxies = self.fetchProxies()

        if self.initComplete:
            print("Tasks ready")

    def setCookies(self, cookies):
        self.cookies = cookies

    def setProxies(self, proxies=AUTO):
        # delete old invalid proxies
        # with open("dump/old_proxies.json", "r") as f:
        #         proxies = json.load(f)

        # for proxy in proxies:
        #     # print(proxy)
        #     try: 
        #         self.db.delete(table = "proxy", id = proxy["_id"])
        #     except DuplicateKeyError:
        #         continue
            
        if proxies == AUTO:
            try: 
                proxies = self.db.getAll(table='proxy', filter={}, column={'_id'})
                for proxy in proxies:
                    self.db.delete(table = "proxy", id = proxy["_id"])
                # self.db['proxy'].drop()
            except DuplicateKeyError:
                pass
            with open("dump/proxies.json", "r") as f:
                proxies = json.load(f)
                # print(proxies)

            for proxy in proxies:
                try:
                    self.db.insert_one("proxy", {
                        "_id": proxy["proxy"],
                        "region": proxy["region"],
                        "status": "A"
                    })
                except DuplicateKeyError:
                    continue
        
        if self.headless:
            print("**Notice: headless mode is not supported when using private proxy!")
            self.headless = False
        self.useMyproxy = True

    def resetPrivateProxies(self):
        self.db.updateMany("proxy", { "$set": {"status":"A"}})

    def setOptions(self, options):
        self.options = options

    def startBrowser(self, thread):
        buffer = self.db.getAll("proxy", 
                    {"status": {"$eq":"A"}},
                    {"_id":1},
                )

    def validateProxy(self, )

    def startChrome(self, thread):

        options = webdriver.ChromeOptions()
        buffer = self.db.getAll("proxy", 
                            {"status": {"$eq":"A"}},
                            {"_id":1},
                        )
        #restart chrome if something went wrong
        while True:

            #if proxies are defined, use proxy server
            if self.useMyproxy:
                if len(buffer) <1:
                    buffer = self.db.getAll("proxy", 
                        {"status": {"$eq":"A"}},
                        {"_id":1},
                        )
                try:
                    proxy_row = random.randint(-1, len(buffer)-1)
                    candidateProxy = buffer[proxy_row]["_id"]
                    buffer = buffer[:proxy_row] + buffer[proxy_row:]
                except IndexError:
                    self.resetPrivateProxies()
                
                authentication = copy.deepcopy(background_js)
                authentication = authentication % (
                    candidateProxy.split(":")[0],
                    candidateProxy.split(":")[1],
                    privateProxy['username'],
                    privateProxy['password']
                )
                
                pluginfile = 'dump/proxy_auth_plugin.zip'
                with zipfile.ZipFile(pluginfile, 'w') as zp:
                    zp.writestr("manifest.json", manifest_json)
                    zp.writestr("background.js", authentication)
                options.add_extension(pluginfile)

                #self.db.update("proxy", candidateProxy, {"status":"O"})
            elif len(self.__proxies) > 0:
                proxy_row = random.randint(0,len(self.__proxies)-1)
                candidateProxy = self.__proxies[proxy_row]
                options.add_argument(f"--proxy-server={candidateProxy}")
                self.__proxies = self.__proxies[:proxy_row] + self.__proxies[proxy_row:] #pop proxy once it is being used
            # elif len(self.__proxies) > 0:
            #     candidateProxy = self.__proxies[0]
            #     options.add_argument(f"--proxy-server={candidateProxy}")
            #     self.__proxies = self.__proxies[1:] #pop proxy once it is being used
            else:
                if REFRESH_PROXY:
                    self.__proxies = self.fetchProxies()
                candidateProxy = "local"

            #load browser settings
            for option in self.options:
                options.add_argument(option)

            #go headless mode
            if self.headless:
                options.add_argument('--headless')

            options.add_experimental_option("excludeSwitches", ["enable-logging"])

            #start chrome
            print(f"Thread {thread+1} -> starting chrome with '{candidateProxy}' proxy")
            if self.helium:
                options.add_extension("AmazonSpider/Config/helium10.crx")
                newChrome = ChromeWithHelium(ChromeDriverManager().install(), options=options)
            else:
                newChrome = webdriver.Chrome(ChromeDriverManager().install(), options=options)
            newChrome.set_page_load_timeout(BROWSER['browserTimeout'])

            if self.helium:
                newChrome.implicitly_wait(20)
            else:
                newChrome.implicitly_wait(BROWSER['elementTimeout'])

            #test if amazon.com is loaded successfully
            try:
                newChrome.get("https://www.amazon.com")
            #if timeout, restart chrome
            except TimeoutException:
                newChrome.quit()
                #self.db.update("proxy", candidateProxy, {"status":"U"})
                continue
            except WebDriverException:
                newChrome.quit()
                #self.db.update("proxy", candidateProxy, {"status":"U"})
                continue
            #if loaded successfully
            else:

                #test if content is loaded properly
                try:
                    newChrome.find_element_by_id("pageContent")
                #if not, wait for a specified time and try again
                except NoSuchElementException:
                    newChrome.quit()
                    #self.db.update("proxy", candidateProxy, {"status":"U"})
                    #if there are proxy in the list, restart chrome with a new proxy immediately
                    if self.useMyproxy or (len(self.__proxies) > 0):
                        continue
                    #if no proxy is available, wait for a while before restarting chrome
                    else:
                        time.sleep(BROWSER['waitInterval'])
                        continue

                #everything goes well, add cookies if any
                if len(self.cookies) > 0:  
                    for cookie in self.cookies:
                        newChrome.add_cookie(cookie)

                #save chrome session
                self.chromes[thread] = (newChrome, candidateProxy)
                return
     
    def logError(self, target, error):
        #log error
        self.db.insert_one(f'{LOGGER}-{self.collection}',{
            "_id": target,
            "timestamp": datetime.now(),
            "error": error,
        })

    def navigatePage(self, thread, target):
        self.chromes[thread][0].get(self.fURL % target)
        return True

    def navigatePageWithValidator(self, thread, target, indicator):

        while True:
            
            try:
                self.chromes[thread][0].get(self.fURL % target)
            except TimeoutException:
                self.chromes[thread][0].quit()
                #self.db.update("proxy", self.chromes[thread][1], {"status":"U"})
                self.startChrome(thread)  
                continue
            except WebDriverException:
                self.chromes[thread][0].quit()
                #self.db.update("proxy", self.chromes[thread][1], {"status":"U"})
                self.startChrome(thread)
                continue
            
            try:
                self.chromes[thread][0].find_element_by_id(indicator)
            except NoSuchElementException:

                try:
                   self.chromes[thread][0].find_element_by_id('g')
                except NoSuchElementException:

                    self.chromes[thread][0].quit()
                    #self.db.update("proxy", self.chromes[thread][1], {"status":"U"})

                    if not len(self.__proxies) > 0:
                        time.sleep(BROWSER['waitInterval'])

                    self.startChrome(thread)
                    continue

                else:
                    self.logError(target, 'URLError: page was not found or product was removed')
                    return False

            else:
                return True

    def __autoload(self):
        try:
            with open("dump/tasks_20220818.pkl", "rb") as f:
                data = pickle.load(f)
        except FileNotFoundError:
            print("No tasks were found!")
            self.initComplete = False
            return []
        else:
            if type(data) != list:
                raise TypeError("Input tasks must be a list object")
            return data

    @abstractmethod
    def getTasks(self):
        '''
            Abstract method
            input: <User specified>
            output: targetId (list object)
        '''
        raise NotImplementedError("Please implement a getTasks method!")

    @abstractmethod
    def spider(self, chrome, target) -> dict :
        '''
            Abstract method
            input: chrome (selenium web driver object), target (str object)
            output: data (dict object)
        '''
        raise NotImplementedError("Please implement a crawler method!")

    def __crawl(self, thread, start, end, delay):

        time.sleep(thread * 1)
        self.startChrome(thread)
        for asin in self.targets[start:end]:

            try:
                # ------------------------ assure asin is a proper id ------------------------ #
                if self.validateAsin and not re.search(r"B[A-Z0-9]{9}", asin):
                    self.logError(asin, "ASINError: invalid asin format")
                    continue

                # # -------------------- skip asin if it was crawled before -------------------- #
                if self.db.exists(self.collection, asin):
                    continue

                if self.db.exists(f"{LOGGER}-{self.collection}", asin):
                    continue

                # --------------------- check if page loaded successfully -------------------- #
                if not self.navIndicator:
                    if not self.navigatePage(thread = thread, target = asin):
                        continue
                else:
                    if not self.navigatePageWithValidator(thread = thread, target = asin, indicator = self.navIndicator):
                        continue

                # ----------------------------- run spider script ---------------------------- #
                data = self.spider(chrome = self.chromes[thread][0], target = asin)
                # print(data)
                if type(data) != dict:
                    raise TypeError(f"Method 'spider' should return a dictionary or list object, instead got {type(data)}")

                # --------------- save result and print progress on the console -------------- #
                if type(data) == dict and data:
                    self.db.insert_one(self.collection, data)

                if self.verbose:
                    # progress = round((self.count() / self.total) * 100, VERBOSEDIGIT)
                    # print(f"Thread {thread + 1} ->", f"{asin} :", f"{progress}%", f"({self.chromes[thread][1]})")
                    print(f"Thread {thread + 1} ->", f"{asin} :", f"({self.chromes[thread][1]})")

                time.sleep(delay)
            
            except ServerSelectionTimeoutError:

                print(f"Thread {thread+1} terminated at {asin} due to connection lost to {self.db.address}")
                # break
                print(f"Thread {thread+1} end")
                return False

            except DuplicateKeyError as ex:
                print(ex)
                pass

            except Exception as ex:
                print(ex)
                if SKIPERROR:
                    self.logError(asin, ex.args[0])
                else:
                    print(f"An error occured at thread {thread+1} -> {asin}: {ex.args[0]}")
                    traceback.print_exc()
                    # break
                    print(f"Thread {thread+1} end")
                    return False

        print(f"Thread {thread+1} end safely")
        return True

    def start(self, delay=0):
        '''
            script start point
        '''
        end_flag = True

        while end_flag == True:

            # self.__prepare_tasks()
            if self.targets == []:
                break

            if self.initComplete:

                # print(self.targets)

                if self.threads == 1 or len(self.targets) < self.threads:
                    while end_flag:
                        end_flag = not self.__crawl(thread=0, start=0, end=len(self.targets), delay=delay)
                        print(f"end_flag: {end_flag}")
                else:
                    #split task
                    jobs = np.linspace(0, len(self.targets), self.threads+1, dtype=int)

                    spoon_list = []
                    with ThreadPoolExecutor(max_workers=self.threads) as executor:
                        for thread in range(len(jobs) - 1):
                            spoon = executor.submit(self.__crawl,
                                thread,
                                jobs[thread],
                                jobs[thread+1],
                                delay
                            )

                            spoon_list.append((spoon, thread))

                        end_flag = False

                        while not end_flag:
                            time.sleep(5) # time.sleep(300)

                            end_flag = None
                            # print(spoon_list)
                            for index, spoon in enumerate(spoon_list):
                                if spoon[0].done():
                                    # print(f"end_flag: {end_flag}, result: {spoon[0].result()}")
                                    end_flag = spoon[0].result() if end_flag is None else end_flag and spoon[0].result()
                                    if not spoon[0].result():
                                        thread = spoon[1]
                                        new_spoon = executor.submit(self.__crawl,
                                                thread,
                                                jobs[thread],
                                                jobs[thread+1],
                                                delay
                                            )
                                        spoon_list[index] = (new_spoon, thread)
                            # print("round failed")
                            if end_flag is None:
                                end_flag = False
                        if end_flag == True:
                            end_flag = False
        
        # print("all finished")                   
        # else:

            # raise TypeError("Cannot start script due to faulty initialization")
        return
    
    def count(self):
        return self.db.count(self.collection) + self.db.count(f'{LOGGER}-{self.collection}')

class mongoDB_id():
    def __init__(self):
        myclient = pymongo.MongoClient("mongodb://intern:intern@192.168.2.94:27017/")
        self.jsCol = myclient['junglescout']['junglescout_selection_database_us']
        self.productsCol = myclient['products']['data']
    def getTask_js(self):
        task = []
        for x in self.jsCol.find({}, {'_id':1}):
            task.append(x['_id'])
        return task
    def getTask_products(self):
        task = []
        for x in self.productsCol.find({}, {'_id':1}):
            task.append(x['_id'])
        return task
    #find difference between two tables and generate a list
    def find_diff(self):
        js_id = set(self.getTask_js())
        data_id = set(self.getTask_products())
        return list(js_id.difference(data_id))

class AmazonStaticCrawler(BaseCrawler):

    fURL = "https://www.amazon.com/dp/%s"
    navIndicator = "dp"
    validateAsin = True
    collection = "data"
    def __init__(self, targets, targets_signal = SELFDEFINED, threads=4, autoProxy=False, headless=False):
        super().__init__(
            targets = targets,
            threads = threads,
            autoProxy = autoProxy,
            headless = headless
        )

    def getTasks(self):
        url = 'http://192.168.2.94:8080/lizhi/'
        myobj = {'mode': 'static'}
        # myobj = {'label':'sports_outdoors'}

        x = requests.post(url, data = myobj)
        x.close()
        asin_pack = json.loads(x.text)
        return asin_pack

        # db = mongoDB_id()
        # tasks = db.find_diff()
        # return tasks

    def spider(self, chrome, target):
        
        data = {
            "_id":target,
            "title":None,
            "category":None,
            "seller":None,
            "sellerHref":None,
            "description":None,
            "featuresBullet":None,
        }
        
        # ----------------------------- find product title ---------------------------- #
        try:
            title = chrome.find_element_by_id("productTitle")
        except NoSuchElementException:
            pass
        else:
            data["title"] = title.text

        # ------------------------------- find category ------------------------------ #
        try:
            category = chrome.find_element_by_css_selector(".a-unordered-list.a-horizontal.a-size-small")
        except NoSuchElementException:
            pass
        else:
            category = category.text.replace("\n", " ")
            data['category'] = category

        # -------------------------------- find seller ------------------------------- #
        try:
            buybox = chrome.find_element_by_id("buybox")
        except NoSuchElementException:
            pass
        else:
            try:
                seller = buybox.find_element_by_css_selector(".tabular-buybox-text[tabular-attribute-name='Sold by']")
            except NoSuchElementException:
                pass
            else:
                data["seller"] = seller.text
                try:
                    sellerHref = seller.find_element_by_tag_name("a").get_attribute("href")
                except NoSuchElementException:
                    pass
                else:
                    data["sellerHref"] = sellerHref

        # ----------------------------- find description ----------------------------- #
        try:
            description = chrome.find_element_by_id("productDescription")
        except NoSuchElementException:
            pass
        else:
            data["description"] = description.text

        
        # --------------------------- find feature bullets --------------------------- #
        try:
            featuresBullet = chrome.find_element_by_id("feature-bullets")
        except NoSuchElementException:
            pass
        else:
            data["featuresBullet"] = featuresBullet.text

        # --------------------------- find product details --------------------------- #
        try:
            prodDetails = chrome.find_element_by_id("prodDetails")
        except NoSuchElementException:
            pass
        else:
            try:
                table = prodDetails.find_element_by_id("productDetails_detailBullets_sections1")
            except NoSuchElementException:
                table = prodDetails.find_element_by_id("productDetails_techSpec_section_1")
            try:
                rows = table.find_elements_by_tag_name("tr")
            except NoSuchElementException:
                pass
            else:
                for r in rows:
                    key = r.find_element_by_tag_name("th").text
                    value = r.find_element_by_tag_name("td").text
                    data[key] = value

        # ---------------------- exclude asin in product details --------------------- #
        try:
            data.pop("ASIN")
        except KeyError:
            pass

        # ----------------------------- save html source ----------------------------- #

        html =  { "_id":target, "source": chrome.page_source }
        self.db.insert_one(self.collection + "_html", html)

        return data

class AmazonSellerCrawler(BaseCrawler):

    fURL = 'https://www.amazon.com/gp/help/seller/at-a-glance.html/ref=dp_merchant_link?ie=UTF8&seller=%s&isAmazonFulfilled=1'
    navIndicator = "seller-profile-container"
    collection = "seller"


    def __init__(self, targets, targets_signal = SELFDEFINED, threads=4, autoProxy=False, headless=False):
        super().__init__(
            targets = targets,
            threads = threads,
            autoProxy = autoProxy,
            headless = headless
        )

    def getTasks(self):
        url = 'http://192.168.2.94:8080/lizhi/'
        myobj = {'mode': 'seller'}

        x = requests.post(url, data = myobj)
        seller_pack = json.loads(x.text)
        return seller_pack
    # def getTasks(self):

    #     targets = self.db.getAll(table="data", column={"sellerHref":1})

    #     tasks = []

    #     for target in targets:
    #         try:
    #             sellerId = re.search(r"(?<=seller=)\w+(?=\&)", target['sellerHref'])
    #         except TypeError:
    #             sellerId = None

    #         if sellerId:
    #             tasks.append(sellerId.group())

    #     return tasks

    def spider(self, chrome, target):
        res = {
            "_id":target,
            "amazonName":None,
            "companyName":None,
            "shopDescription":None,
            "companyAddress":None,
        }
        root = etree.HTML(chrome.page_source)
        try:
            amazonName = root.xpath("//h1[@id='sellerName-rd']/text()")
        except NoSuchElementException:
            pass
        else:
            if amazonName:
                res["amazonName"] = amazonName[0].strip()

        try:
            shopDescription = root.xpath("//div[contains(@class,' about-seller')]/div/div[contains(@class,'hide-content')]/text()")
            if not shopDescription:
                shopDescription = root.xpath("//div[contains(@class,' about-seller')]/div/text()")
        except NoSuchElementException:
            pass
        else:
            res["shopDescription"] = ' '.join(shopDescription).strip()

        try:
            companyName = root.xpath("//div[@id='page-section-detail-seller-info']/div/div/div/div[contains(@class, 'a-row a-spacing-none')]//text()")
        except NoSuchElementException:
            pass
        else:
            
            tmp = ' '.join(companyName).split('Business Name:')
            if len(tmp)>1:
                companyName = tmp[1].strip()
                companyAddress = companyName.split('Business Address:')
                if len(companyAddress)>1:
                    companyAddress = companyAddress[1].strip()
                companyName = companyName.split('Business Address:')[0].strip()
                res["companyName"] = companyName
                res["companyAddress"] = companyAddress
            # else:
            #     print(f"{target}: {companyName}")
        try:
            tmp = root.xpath("""//div[@id='page-section-feedback']//script[@type='a-state' and @data-a-state='{"key":"oneMonthRatingsData"}']/text()""")
        except NoSuchElementException:
            pass
        else:
            if tmp:
                tmp = json.loads(tmp[0])
                for k,v in tmp.items():
                    res[k+"_1month"] = v

        try:
            tmp = root.xpath("""//div[@id='page-section-feedback']//script[@type='a-state' and @data-a-state='{"key":"threeMonthRatingsData"}']/text()""")
        except NoSuchElementException:
            pass
        else:
            if tmp:
                tmp = json.loads(tmp[0])
                for k,v in tmp.items():
                    res[k+"_3months"] = v

        try:
            tmp = root.xpath("""//div[@id='page-section-feedback']//script[@type='a-state' and @data-a-state='{"key":"twelveMonthRatingsData"}']/text()""")
        except NoSuchElementException:
            pass
        else:
            if tmp:
                tmp = json.loads(tmp[0])
                for k,v in tmp.items():
                    res[k+"_12months"] = v
        try:
            tmp = root.xpath("""//div[@id='page-section-feedback']//script[@type='a-state' and @data-a-state='{"key":"lifetimeRatingsData"}']/text()""")
        except NoSuchElementException:
            pass
        else:
            if tmp:
                tmp = json.loads(tmp[0])
                for k,v in tmp.items():
                    res[k+"_lifetime"] = v 
        try:
            content = chrome.find_element_by_id("seller-profile-container")
        except NoSuchElementException:
            pass
        else:
            self.db.insert_one(self.collection + "_html", {
                "_id":target,
                "source":content.get_attribute("innerHTML"),
            })

        return res

# class AmazonReviewsCrawler(BaseCrawler):
    
#     fURL = "https://www.amazon.com/product-reviews/%s/"
#     navIndicator = "a-page"
#xp 添加
class AmazonSellerProductsCrawler(BaseCrawler):

    fURL = "https://www.amazon.com/s?me=%s&marketplaceID=ATVPDKIKX0DER"
    navIndicator = "s-skipLinkTargetForMainSearchResults"
    collection = "seller_products"

    def __init__(self, targets, targets_signal = SELFDEFINED, threads=4, autoProxy=False, headless=False):
        super().__init__(
            targets = targets,
            # slice = slice,
            threads = threads,
            autoProxy = autoProxy,
            headless = headless
        )

        
    def getTasks(self):
        url = 'http://192.168.2.94:8080/lizhi/'
        myobj = {'mode': 'sellerproducts'}

        x = requests.post(url, data = myobj)
        asin_pack = json.loads(x.text)
        return asin_pack

        # db = mongoDB_id()
        # tasks = db.find_diff()
        # return tasks
    

    # def getTasks(self):
    #     targets = self.db.getAll(table="seller")

    #     tasks = []

    #     for target in targets:
    #         tasks.append(target["_id"])

    #     return tasks


    def spider(self, chrome, target):
        data = {
            "_id":target,
            "products":[],
        }
        while True:
            time.sleep(3)
            # html = chrome.page_source
            # result = re.findall(r'(?:%2F|/)dp(?:%2F|/)(\w{10})(?:%2F|/)', html)
            # if result:
            #     for i in range(0, len(result)):
            #         asin = result[i]
            #         if asin not in data['products']:
            #             data['products'].append(asin)
            try:
                results_list = chrome.find_elements_by_xpath(".//*[@class='s-main-slot s-result-list s-search-results sg-row']/div")
                for result in results_list:
                    asin = result.get_attribute('data-asin')
                    if asin:
                        if asin not in set(data['products']):
                            data['products'].append(asin)
            except:
                # time.sleep(3)
                continue
                        
            # time.sleep(2)
            try:
                chrome.find_element_by_xpath('//*[@class="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"]').click()
                continue
            except Exception as e:
                print("next end")
                break

        return data
    # for seller products crawler, we do not need to check the 'g' element
    def navigatePageWithValidator(self, thread, target, indicator):

        while True:
            
            try:
                self.chromes[thread][0].get(self.fURL % target)
            except TimeoutException:
                self.chromes[thread][0].quit()
                #self.db.update("proxy", self.chromes[thread][1], {"status":"U"})
                self.startChrome(thread)  
                continue
            except WebDriverException:
                self.chromes[thread][0].quit()
                #self.db.update("proxy", self.chromes[thread][1], {"status":"U"})
                self.startChrome(thread)
                continue
            
            try:
                self.chromes[thread][0].find_element_by_id(indicator)
            except NoSuchElementException:
                self.chromes[thread][0].quit()
                #self.db.update("proxy", self.chromes[thread][1], {"status":"U"})

                # if not len(self.__proxies) > 0:
                #     time.sleep(BROWSER['waitInterval'])

                self.startChrome(thread)
                continue

                # try:
                #    self.chromes[thread][0].find_element_by_id('g')
                # except NoSuchElementException:

                #     self.chromes[thread][0].quit()
                #     #self.db.update("proxy", self.chromes[thread][1], {"status":"U"})

                #     if not len(self.__proxies) > 0:
                #         time.sleep(BROWSER['waitInterval'])

                #     self.startChrome(thread)
                #     continue

                # else:
                #     self.logError(target, 'URLError: page was not found or product was removed')
                #     return False

            else:
                return True

#xp 添加
class AmazonFeedbackCrawler(BaseCrawler):

    fURL = 'https://www.amazon.com/sp?ie=UTF8&seller=%s&isAmazonFulfilled=1'
    navIndicator = "feedback-content"
    collection = "feedback"

    def __init__(self, targets, targets_signal = SELFDEFINED, threads=4, autoProxy=False, headless=False):
        super().__init__(
            targets = targets,
            # slice = slice,
            threads = threads,
            autoProxy = autoProxy,
            headless = headless
        )
        self.path = 'data_feedback'
        if not os.path.exists(self.path):
            try:
                os.makedirs(self.path)
            except Exception as e:
                print("other created")

    #需要完善
    # def getTasks(self):
    #     tasks = ['A3GSQI3T41AKT', 'A3N7XBE78NPWG2']
    #     return tasks
    
    def getTasks(self):
        url = 'http://192.168.2.94:8080/hello/'
        myobj = {'mode': 'feedback'}

        x = requests.post(url, data = myobj)
        asin_pack = json.loads(x.text)
        return asin_pack

        # db = mongoDB_id()
        # tasks = db.find_diff()

    def spider(self, chrome, target):
        data = {
            "_id":target,
            "data": None,
        }

        #用js实现post数据
        fbUrl = 'https://www.amazon.com/sp/ajax/feedback'
        fData = "seller=%s&marketplaceID=ATVPDKIKX0DER&pageNumber=%s"
        js = '''
            var x_url = arguments[0];
            var x_data = arguments[1];
            var x_xhr = new XMLHttpRequest();            
            x_xhr.open('POST', x_url, false);
            x_xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');                   
            x_xhr.send(x_data);          
            return x_xhr.response;
        '''
        page = 0
        feedbacks = {
            "pages": []
        }
        while True:
            fbData = fData % (target, page)
            try:
                html = chrome.execute_script(js, fbUrl, fbData)
                cjson = json.loads(html)
            except Exception as e:
                page += 1
            else:
                if 'actionParams' not in feedbacks.keys():
                    feedbacks['actionParams'] = cjson['actionParams']
                feedbacks['pages'].append(cjson['details'])
                #print(cjson['hasNextPage'], fbData)
                if not cjson['hasNextPage']: #判断是否有下一页
                    break
                page += 1

            '''
            #用界面元素判断是否有下一页
            nextBtn = WebDriverWait(chrome, 10).until(
                lambda x: x.find_element_by_id('feedback-next-link')
            )
            if nextBtn.is_displayed():
                nextBtn.click()
                page += 1
            else:
                break
            '''

        # #wirte to json file
        # file = "%s/%s.json" % (self.path, target)
        # with open(file, "w+") as f:
        #     f.write(json.dumps(feedbacks))

        #wirte to mongodb
        data['data'] = feedbacks #这里采用写文件的方式存储，因此没有存mongodb

        return data
    
class AmazonInventoryCrawler(BaseCrawler):

    fURL = "https://www.amazon.com/dp/%s"
    navIndicator = "dp"
    validateAsin = True
    collection = "stock"
    
    def __init__(self, targets, targets_signal = SELFDEFINED, threads=4, autoProxy=False, headless=False):
        super().__init__(
            targets = targets,
            threads = threads,
            autoProxy = autoProxy,
            headless = headless
        )
    # def getTasks(self):
    #     df = pd.read_csv("./dump/demo_target.csv")
    #     asin_list = list(df["asin"])
    #     return asin_list
    
    def getTasks(self):
        url = 'http://192.168.2.94:8080/hello/'
        myobj = {'mode': 'inventory'}

        x = requests.post(url, data = myobj)
        asin_pack = json.loads(x.text)
        return asin_pack

        # db = mongoDB_id()
        # tasks = db.find_diff()
        # return tasks
        
    def spider(self, chrome, target):
        
        data = {
            "_id": target,
            "stock": None,
        }

        # ---------------------------- add product to cart --------------------------- #

        try:
            addToCart = chrome.find_element_by_id("add-to-cart-button")
        except NoSuchElementException:
            return data
        else:
            addToCart.click()

        time.sleep(1.5)

        chrome.get("https://www.amazon.com/gp/cart/view.html?ref_=nav_cart")

        # ------------------------------ set qty to 999 ------------------------------ #
        while True:
            try:
                chrome.find_element_by_id("a-autoid-0-announce").click()
                chrome.find_element_by_css_selector("li[aria-labelledby='quantity_10']").click()
                chrome.find_element_by_css_selector("input[name='quantityBox']").send_keys("999")
                chrome.find_element_by_id("a-autoid-1-announce").click()
            except NoSuchElementException:
                return data
            except:
                continue
            else:
                break

        # ------------------------------- locate target ------------------------------ #

        try:
            messageBx = chrome.find_element_by_css_selector(".sc-quantity-update-message.a-spacing-top-mini")
            message = messageBx.find_element_by_class_name("a-alert-content").text
        except NoSuchElementException:
            data['stock'] = "999+"
        else:
            if "This seller has a limit of " in message:
                data['stock'] = f'Limitation:{message.split(" ")[6]}'
            elif "This seller has only " in message:
                data['stock'] = message.split(" ")[4]

        # -------------------------------- clear cart -------------------------------- #
        while True:
            try:
                delete = chrome.find_element_by_css_selector("span[data-action='delete']")
                delete = delete.find_element_by_tag_name("input")
                delete.click()
            except:
                continue
            else:
                break

        return data

class AmazonReviewsCrawler(BaseCrawler):
    fURL = "https://www.amazon.com/product-reviews/%s/?sortBy=recent&pageNumber=1&language=en_US"
    navIndicator = "cm_cr-review_list"
    collection = "reviews"

    def __init__(self, targets, targets_signal = SELFDEFINED, threads=4, autoProxy=False, headless=False, timeline=2020):
        super().__init__(
            targets = targets,
            # slice = slice,
            threads = threads,
            autoProxy = autoProxy,
            headless = headless
        )
        self.timeline = timeline
    
    def transformInt(self, text):
        return text.replace(',', '')
        
    def getTasks(self):
        url = 'http://192.168.2.94:8080/hello/'
        myobj = {'mode': 'reviews'}

        x = requests.post(url, data = myobj)
        asin_pack = json.loads(x.text)
        return asin_pack

        # db = mongoDB_id()
        # tasks = db.find_diff()
        # return tasks
    

    # def getTasks(self):
    #     df = pd.read_csv("./dump/selected_asin_list.csv")
    #     asin_list = list(df["selected_asin"])
    #     return asin_list
    
    def spider(self, chrome, target):
        datas = []
        before_timeline = False

        url = "https://www.amazon.com/product-reviews/%s/?sortBy=recent&pageNumber=%s&language=en_US"
        page = 1

        chrome.get(url % (target, page))
        # print(f"\n# -------------------------- reviews about {target} -------------------------- #")

        # ----------------------------- review-rating-count ----------------------------- #
        try:
            review_rating_count = chrome.find_element_by_id("filter-info-section")
            review_rating_count_group = review_rating_count.text.strip().split(' ')
            rating_count = review_rating_count_group[0]
            if 'with' in review_rating_count_group:
                review_count = int(self.transformInt(review_rating_count_group[3]))
            else:
                review_count = int(self.transformInt(review_rating_count_group[4]))
            # print(f"rating: {rating_count}, review: {review_count}")

        except NoSuchElementException:
            pass
        except Exception as e:
            traceback.print_exc()
            error_info = f"error happend in line {e.__traceback__.tb_lineno}: {e}"
            print(error_info)
            self.logError(target, error_info)
            return {}
        else:
            page_amount = review_count // 10 + 1 if review_count%10 != 0 else review_count // 10

        # -------------------------------- review-rating -------------------------------- #
        while page <= page_amount:
            # print(f"# -------------- page {page} -------------- #")
            review_list = chrome.find_element_by_id("cm_cr-review_list")
            review_parts = review_list.find_elements_by_xpath(".//*[@data-hook='review']")
            for review_part in review_parts:
                data = {}
                try:
                    # ---------------------------- review info ------------------------------ #
                    review_info = review_part.find_element_by_xpath(".//*[@data-hook='review-date']").text

                    # ---------------------------- review date ------------------------------ #
                    # only get reviews after the timeline
                    if int(review_info.strip().split(' ')[-1]) < self.timeline:
                        before_timeline = True
                        break

                    review_date = ' '.join(review_info.strip().split(' ')[-3:])
                    review_date = datetime.strptime(review_date, "%B %d, %Y")
                    review_date = datetime.strftime(review_date, "%Y/%m/%d")
                    # print(f"review date: {review_date}")
                    data['review date'] = review_date

                    # -------------------------- review location ---------------------------- #
                    review_location = ' '.join(review_info.strip().split(' ')[2:-4])
                    # print(f"review location: {review_location}")
                    data['review location'] = review_location

                    # ------------------------------- reviewer ------------------------------ #
                    reviewer = review_part.find_element_by_xpath(".//*[@class='a-profile-name']").text
                    # print(f"reviewer: {reviewer}")
                    data['reviewer'] = reviewer

                    # ------------------------------- rating -------------------------------- #
                    rating = review_part.find_element_by_xpath(".//*[@class='a-link-normal']").get_attribute("title")
                    # print(f"rating: {rating}")
                    rating = rating.strip().split(' ')[0]
                    data['rating'] = rating

                    # ---------------------------- review title ----------------------------- #
                    review_title = review_part.find_element_by_xpath(".//*[@data-hook='review-title']").text
                    # print(f"review title: {review_title}")
                    data['review title'] = review_title
                        
                    # --------------------------- purchase state ---------------------------- #
                    try:
                        purchase_state = review_part.find_element_by_xpath(".//*[@data-hook='avp-badge']").text
                        # print(f"purchase state: {purchase_state}")
                        data['purchase state'] = purchase_state
                    except NoSuchElementException:
                        # print("No purchase state in this review")
                        data['purchase state'] = None

                    # ---------------------------- review body ------------------------------ #
                    review_body = review_part.find_element_by_xpath(".//*[@data-hook='review-body']").text
                    # print(f"review body: {review_body}")
                    data['review body'] = review_body

                    # ----------------------- helpful vote statement ------------------------ #
                    try:
                        helpful_vote_statement = review_part.find_element_by_xpath(".//*[@data-hook='helpful-vote-statement']").text
                        # print(f"helpful vote statement: {helpful_vote_statement}\n")
                        data['helpful vote statement'] = helpful_vote_statement
                    except NoSuchElementException:
                        # print("No helpful vote statement in this review\n")
                        data['helpful vote statement'] = None
                except NoSuchElementException:
                    pass
                else:
                    # print(data)
                    # time.sleep(2)

                    datas.append(data)
                    # print(datas)
                    time.sleep(0.5)

            if before_timeline:
                    break

            # turn to next page
            page += 1

            if page > page_amount:
                break
            chrome.get(url % (target, page))
            time.sleep(3)
        
        time.sleep(3)

        return {"_id": target, "reviews": datas}



#endregion

# %%

