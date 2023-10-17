from datetime import date
from sqlalchemy import create_engine
import pandas as pd

today = date.today()

# DATABASE = {
#     'host': '192.168.2.94',
#     'port': '27017',
#     'username': "readwrite", #'data'
#     'password': "password1", #'cafl-2021'
#     'db':'products_2302',
#     'source':'admin'
#     # 'db': f'products_{today.strftime("%Y%m")[2:]}'
# }

task_sql = {
    "dbname":"Amazon_Progress_Meta",
    "host":"192.168.2.94",
    "port":3306,
    "username":"changliu",
    "password":"CHANGliu_94"
}

# try:
#     engine = create_engine(f'mysql+pymysql://{task_sql["username"]}:{task_sql["password"]}@{task_sql["host"]}:{task_sql["port"]}/Spider_Meta')
#     df = pd.read_sql("SELECT period from period")
#     period = df['period'].iloc[0].dt.strftime("%Y%m")
# except:
#     period = "2306" #time.strftime("%Y%m", time.localtime(time.time()))

period = "2310"

DATABASE = {
    'host': '192.168.2.108',
    'port': '27017',
    'username': "writer", #'data'
    'password': "writerof108", #'cafl-2021'
    'db':f'products_{period}',
    'source':'test'
    # 'db': f'products_{today.strftime("%Y%m")[2:]}'
}


PROXY = {
    'username': "kentwu@hkaift.com",
    'password': "scgx4a"
}

BROWSER = {
    #broswer settings
    'options': [
        # r"user-data-dir=C:\Users\lukemai\AppData\Local\Google\Chrome\User Data",
        "--no-sandbox",
        "blink-settings=imagesEnabled=false",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "--dns-prefetch-disable",
        "--disable-browser-side-navigation",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        "enable-automation"
    ],
    #waiting time to restart chrome after blocked by Amazon
    'waitInterval': 20,
    #wait for web element
    'elementTimeout': 1,
    #browser loading timeout
    'browserTimeout': 180,
}

privateProxy = {
    'username': 'helenovang',
    'password': 'F9JGauUE',
}

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" #% (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

#logging collection name
LOGGER = "ERROR"

#do not stop execution when runs into error (instead log error)
SKIPERROR = False

#format progress decimal places
VERBOSEDIGIT = 4

#fetch more proxies if running out (autoProxy)
REFRESH_PROXY = False

PROXYROTATE = True

AUTOCOOKIES = True

SELFDEFINED = "selfDefined"
AUTO = "auto"