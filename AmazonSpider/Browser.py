#%%
import json
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

#%%
class ChromeWithHelium(webdriver.Chrome):

    def __init__(self, *args, **kwargs):
        super(ChromeWithHelium, self).__init__(*args, **kwargs)
        self.close()
        self.switch_to.window(self.window_handles[0])

        with open("AmazonSpider/Config/heliumAuth.json", "r") as f:
            hcookies = json.load(f)
        with open('AmazonSpider/Config/localStorage.json', 'r') as f:
            lstorage = json.load(f)

        for hcookie in hcookies:
            self.add_cookie(hcookie)
        for key in lstorage.keys():
            self.add_localStorage(key, lstorage[key])

        self.get("chrome://extensions/")

        extensionsManager = self.get_shadowRoot(self, By.TAG_NAME, 'extensions-manager')
        extensionsList = self.get_shadowRoot(extensionsManager, By.ID, 'items-list')
        extensionItem = self.get_shadowRoot(extensionsList, By.ID, 'njmehopjdpcckochcggncklnlmikcbnb')
        crreload = self.get_shadowRoot(extensionItem, By.ID, 'dev-reload-button')
        crreload.find_element_by_id("icon").click()

    def get_localStorage(self):
        return self.execute_script( \
            "var ls = window.localStorage, items = {}; " \
            "for (var i = 0, k; i < ls.length; ++i) " \
            "  items[k = ls.key(i)] = ls.getItem(k); " \
            "return items; ")

    def add_localStorage(self, key, value):
        self.execute_script("window.localStorage.setItem(arguments[0], arguments[1]);", key, value)

    def get_shadowRoot(self, driver, selector, tag):
        e = driver.find_element(selector, tag)
        shadowRootID = list(self.execute_script("return arguments[0].shadowRoot", e).values())[0]
        return WebElement(self, shadowRootID, w3c=True)