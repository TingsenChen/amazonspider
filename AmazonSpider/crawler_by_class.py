import os
from scipy import rand
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
import time
import traceback
import random
import sys
import re
sys.path.append(os.getcwd())
from AmazonSpider.Server import DBMongo
import pandas as pd
from lxml import etree
import requests
import ddddocr
import copy,zipfile

from Config.settings import background_js, privateProxy, manifest_json

working_directory = os.getcwd()
if not os.path.exists(working_directory + "/fig"):
    os.mkdir(working_directory + "/fig")

def start_chrome(PROXY = None):
    options = webdriver.ChromeOptions()
    if PROXY:
        db = DBMongo(database="products_2306")
        collection = "proxy"
        proxies = db.getAll(collection, filter={'region':"Hong Kong"}, column={})
        candidateProxy = random.choice(proxies)['_id']

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

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    # driver = webdriver.Edge(executable_path="C:/Users/zhili/AmazonSpider/msedgedriver.exe")
    driver.get("https://www.amazon.com")
    driver.maximize_window()
    driver = decaptcha(driver)
    time.sleep(5)
    return driver

def parse_asin(html, path):
    root = etree.HTML(html)
    ret = []
    # print(root.xpath(".//div[@data-asin]/@data-asin"))
    results = root.xpath(".//div[@data-asin]")
    if results:
        for result in results:
            if result.xpath("./@data-asin") and result.xpath("./@data-asin")[0]:
                data = {
                    "_id": None,
                    "class_path": path,
                    "if_sponsored": False
                    }
                data["_id"] = result.xpath("./@data-asin")[0]
                if "Sponsored" in ''.join(result.xpath(".//text()")):
                    data["if_sponsored"] = True
                ret.append(data)
    return ret

def get_nodes_data(driver, path, node):
    data = {
        "_id": node,
        "class_path": path,
        "_timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        }
    # data = parse_node(path, node)
    step = 1
    if db.exists(node_collection, data["_id"]):
        tmp_data = db.getOne(node_collection, data["_id"])
        for i in range(10):
            if data["class_path"] != (tmp_data[f"class_path_{i}"] if i>0 else tmp_data[f"class_path"]):
                data[f"class_path_{i+step}"] = tmp_data[f"class_path_{i}"] if i>0 else tmp_data[f"class_path"]
                data[f"_timestamp_{i+step}"] = tmp_data[f"_timestamp_{i}"] if i>0 else tmp_data[f"_timestamp"]
            else:
                step -= 1
            if f"class_path_{i+1}" not in tmp_data:
                break
        db.update(node_collection, data['_id'], data)
    else:
        db.insert_one(node_collection, data)
    print(data)
    time.sleep(2+2*random.random())
    return

def get_products_data(driver, path, node):
    base_url = driver.current_url
    start_page = 1
    # crawled_paths = pd.read_csv(f"./tmp/finished_paths_{period}.csv") if os.path.exists(f"./tmp/finished_paths_{period}.csv") else pd.DataFrame({'path':[], 'page':[]})
    # current_progress = crawled_paths[crawled_paths['path'] == path]
    current_progress = db.getOne(f"PROGRESS-{collection}-{period}", path)
    if current_progress:
        if current_progress['page'] == "FINISHED":
            return 
        start_page = current_progress['page']
    if start_page > 1:
        page_counter = start_page
        # "https://www.amazon.com/s?i=toys-and-games-intl-ship&bbn=16225015011&rh=n%3A165993011%2Cn%3A2514571011&dc&ds=v1%3Av7L1nW1oTKqJWz2LzjilRMiVG5QnjfJ9q9dRMZtUBJU&qid=1672797779&rnid=165993011&ref=sr_nr_n_1"
        #"https://www.amazon.com/s?i=toys-and-games-intl-ship&bbn=16225015011&rh=n%3A165993011%2Cn%3A2514571011&dc&page=2&qid=1672797874&rnid=165993011&ref=sr_pg_2"
        url = base_url.replace("ref=sr_nr_n_1",f"ref=sr_pg_{start_page}")
        url += f"&page={start_page}"
        driver.get(url)
    else:
        page_counter = 1
    end_flag = False
    while True:
        result_list = WebDriverWait(driver, 16).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='s-main-slot s-result-list s-search-results sg-row']/div")))
        print(f"\npage {page_counter}")
        html = driver.page_source
        data = parse_asin(html, path)
        add_count = 0
        N = len(data)
        for d in data:
            d['_timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            if db.exists(collection, d["_id"]):
                continue
            print(d)
            db.insert_one(collection, d)
            add_count += 1
        print(f"Added {add_count}/{N}")
        try:
            next_button = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.XPATH, "//span[@class='s-pagination-strip']/a[contains(@aria-label, 'Go to next page')]")))
            if next_button.get_attribute("aria-disabled") == "true":
                break
            next_button.click()
        except TimeoutException:
            print("End of page! Skip to next category!")
            end_flag=True
            break
        except WebDriverException as e:
            print(e)
            traceback.print_exc()
            if "out of memory" in str(e).lower():
                print("Out of memory error detected!")
                driver.refresh()
                page_counter -= 1
            if "no such element" in str(e).lower():
                print("End of page! Skip to next category!")
                break
        update_progress(path, int(page_counter))
        page_counter += 1         
        # sleep 2 seconds minimum #
        time.sleep(2+2*random.random())
    if end_flag:
        update_progress(path, "FINISHED")
    return

def update_progress(path, status):
    if db.exists(f"PROGRESS-{collection}-{period}", path):
        db.update(f"PROGRESS-{collection}-{period}", path, {'page':status})
    else:
        db.insert_one(f"PROGRESS-{collection}-{period}", {'_id': path, 'page':status})

def traverse_sub_kinds(driver, path, node):
    try:
        departments = driver.find_element_by_id("departments")
    except:
        db.insert_one(f"ERROR-{collection}", {"path": path})
        print(f"something error with the {path} related webpages...")
        return
        
    li_group = departments.find_elements_by_tag_name("li")
    # if current sub_kind can not be divided any more, get data from the webpage
    if li_group[-1].get_attribute("class")[-1] == '1':
        get_nodes_data(driver, path, node)
        get_products_data(driver, path, node)
        time.sleep(random.random())
        return

    # otherwise, traverse until the sub_kind can not be divided any more
    original_window = driver.current_window_handle
    random.shuffle(li_group)
    for li in li_group:
        if li.get_attribute("class")[-1] == '2':
            child_kind = li.text
            child_node = li.get_attribute("id")
            original_path = path
            original_node = node
            print(f"turn to {child_kind}/{child_node}...")
            path += f"/{child_kind}"
            node += f"/{child_node}"
            print(f"current path: {path}/{node}")
            # if path not in finished_paths:
            if not db.getAll(f"PROGRESS-{collection}-{period}", filter = {'_id':path,"page":"FINISHED"}):
                a = li.find_element_by_tag_name("a")
                link = a.get_attribute("href")
                driver.execute_script(f'window.open("{link}", "_blank");')

                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(random.random())
                traverse_sub_kinds(driver, path, node)
                print(f"\nall sub-kinds of the {path} have been traversed\n")
                driver.close()
                # update_progress(path, "FINISHED")
            path = original_path
            node = original_node
            driver.switch_to.window(driver.window_handles[-1]) # original window
            
        # time.sleep(1)

def spider(driver, kind, node):
    cur_path = kind
    cur_node = node
    # find and click the menu button 'all'
    all_button = driver.find_element_by_id("nav-hamburger-menu")
    all_button.click()
    time.sleep(2)
    # find the menu and click 'see all' button, then get to the expected kind of products
    menu = driver.find_element_by_id("hmenu-content")
    if kind in pre_kinds:
        li_group = menu.find_elements_by_xpath("*[@class='hmenu hmenu-visible']/li")
        for li in li_group[6:10]:
            if li.text == kind:
                li.click()
                break
    else:        
        compress_button = menu.find_element_by_xpath(".//*[@class='hmenu-item hmenu-compressed-btn']")
        compress_button.click()
        time.sleep(2)
        li_group = driver.find_elements_by_xpath("//*[@class='hmenu-compress-section']/li")
        for li in li_group[1:]:
            if li.text == kind:
                li.click()
                break
            
    time.sleep(2)
    # traverse all child kinds of the expected kind
    original_window = driver.current_window_handle
    a_group = driver.find_elements_by_xpath("//*[@class='hmenu hmenu-visible hmenu-translateX']/li/a[@class='hmenu-item']")
    random.shuffle(a_group)
    for a in a_group:
        # get sub_kind of the expected kind and print its class_path
        child_kind = a.text
        tmp_node = re.search(r"%3A([0-9]+?)&ref",a.get_attribute("href"))
        print(cur_path, child_kind, a.get_attribute("href"))
        child_node = "n/" + tmp_node.group(1)
        if not child_kind:
            continue
        original_path = cur_path
        original_node = cur_node
        print(f"turn to {child_kind} / {child_node}...")
        cur_path += f"/{child_kind}"
        cur_node += f"/{child_node}"
        print(f"current path: {cur_path} / {cur_node}")
        # if cur_path not in finished_paths:
        if not db.getAll(f"PROGRESS-{collection}-{period}", filter = {'_id':cur_path,"page":"FINISHED"}):
        # jump to the sub_kind webpage
            # a = li.find_element_by_tag_name("a")
            link = a.get_attribute("href")
            driver.execute_script(f'window.open("{link}", "_blank");')

            # switch the target window of the driver and traverse all the sub_kinds
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
            traverse_sub_kinds(driver, cur_path, cur_node)
            print(f"\nall sub-kinds of the {cur_path}/{cur_node} have been traversed\n")
            driver.close()
            # update_progress(cur_path, "FINISHED")
        # switch back and reset the class_path
        cur_path = original_path
        cur_node = original_node
        driver.switch_to.window(driver.window_handles[0]) ## original_window

def decaptcha(driver):
    ocr = ddddocr.DdddOcr()
    while True:
        captcha = None
        try:
            captcha = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//form[@action='/errors/validateCaptcha']//div[@class='a-row a-text-center']/img")))
        except Exception as e:
            break
            pass
        else:
            if captcha is not None:
                url = captcha.get_attribute('src')
                response = requests.get(url)
                filename = 'amz_captcha.png'
                with open(f"./fig/{filename}", 'wb') as f:
                    f.write(response.content)

                with open(f"./fig/{filename}", 'rb') as f:
                    img_bytes = f.read()
                res = ocr.classification(img_bytes).upper()
                if len(res) != 6:
                    driver.refresh()
                    time.sleep(10)
                    continue
                captcha_input_box = driver.find_element(By.XPATH, "//input[@id='captchacharacters']")
                for p in str(res):
                    captcha_input_box.send_keys(p)
                    time.sleep(0.5) 
                sumbit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                sumbit_button.click()
            else:
                break
        time.sleep(10)
    return driver

if __name__ == "__main__":
    pre_kinds = {"Electronics", "Computers", "Smart Home", "Arts & Crafts"}
    db = DBMongo(database="control_db")
    collection = "asins_by_class"
    node_collection = "nodes"
    driver = start_chrome(PROXY = True)
    f = None
    # change the parameter as the expected kind
    period = "2307"
    categories = ["Home and Kitchen", "Automotive","Beauty and personal care","Pet supplies", "Sports and Outdoors", "Tools & Home Improvement", "Toys and Games", "Video Games"]
    # ["Luggage", "Industrial and Scientific", "Health and Household", "Baby", "Men's Fashion", "Women's Fashion", "Girls' Fashion", "Boys' Fashion", ]
    # ["Electronics", "Computers", "Smart Home", "Arts & Crafts"]
    ## Computers belong to electronics
    categories_nodes = [
        ("Electronics", "172282"), 
        # ("Computers", "172282/n/541966"), 
        ("Home and Kitchen", "1055398"),
        ("Automotive", "15684181"), 
        ("Baby", "165796011"),
        ("Beauty and personal care", "3760911"), 
        ("Health and Household", "3760901"),
        ("Industrial and Scientific", "16310091"), 
        ("Pet supplies", "2619533011"), 
        ("Sports and Outdoors", "3375251"),  
        ("Tools & Home Improvement", "228013"), 
        ("Toys and Games", "165793011"), 
        ("Video Games", "468642")
                        ]
    random.shuffle(categories_nodes)
    for category, node in categories_nodes:
        print(f"current category: {category}/{node}")
        if db.getAll(f"PROGRESS-{collection}-{period}", filter={"_id":category,'page':"FINISHED"}, column={}):
            print(f"{category}: FINISHED")
            continue
        try:
            spider(driver, category, node)
        except Exception as e:
            print("RESTART!!")
            traceback.print_exc()
            print(e)
            time.sleep(5)
            try:
                driver.close()
            except:
                pass 
            driver = start_chrome()
        else:
            print(category, "FINISHED")
            # update_progress(category, "FINISHED")                
