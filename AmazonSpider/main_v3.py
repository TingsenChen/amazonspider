#%%
from crawler_v2 import *

import socket, psutil, random
# from Helium.crawler import *
# from AmazonSpider.Crawler import *
# from Helium.big_crawler import *
#%%
# amazonSellerBot = AmazonSellerCrawler(threads=4, headless=False)
# amazonSellerBot.setProxies()
# amazonSellerBot.start()

# amazonReviewsBot = AmazonReviewsCrawler(targets=AUTO, threads=3)
# amazonReviewsBot.setProxies()
# amazonReviewsBot.start()

# helium_bot = HeliumTargetSearchCrawler(targets=SELFDEFINED)
# helium_bot.start()
environment_exe_path = "D:\Anaconda3\python.exe"
def kill_process(pid):
    if psutil.pid_exists(pid):
        process = "taskkill /f /pid %d"%pid
        os.system(process)
    else:
        pass

def kill_redundant_process():
    for pid in psutil.pids():
        try:
            if psutil.pid_exists(pid) and pid != os.getpid() and pid != os.getppid():
                p = psutil.Process(pid)
                    
                if p.exe() == environment_exe_path:
                    continue
        except:
            pass
    
    for pid in psutil.pids():
        try:
            if psutil.pid_exists(pid):
                p = psutil.Process(pid)

                name = p.name().lower()
                if 'chrome' in name:
                    # print(name)
                    kill_process(pid)
                    # print(p.exe())
                    # print(p.cwd())
                    # print("pid-%d, pname-%s" %(pid, p.name()))
        except:
            pass

class Manager():
    # def __init__(self):
    #     self.mode_unlabel = ['static','seller','sellerproducts','reviews','feedback','inventory']
    
    def get_task(self, task, mode):
        url = 'http://192.168.2.94:8080/v3/'
        hostname=socket.gethostname()
        IPAddr=socket.gethostbyname(hostname)
        myobj = {"task": task,"mode":mode, 'IP':IPAddr}
        x = requests.post(url, data = myobj)
        targets = []
        try:
            targets = json.loads(x.text)
        except:
            pass
        print(myobj, targets[0] if targets else [])
        return targets

    def get_bots(self, mode, targets, nthread):
        if mode == 'static':
            return AmazonStaticCrawler(targets = targets, threads=nthread)
        elif mode == 'seller':
            return AmazonSellerCrawler(targets = targets, threads=nthread)
        elif mode == 'seller_products':
            return AmazonSellerProductsCrawler(targets = targets, threads=nthread)
        elif mode == 'reviews': 
            return AmazonReviewsCrawler(targets = targets, threads=nthread)
        elif mode == 'feedback': 
            return AmazonFeedbackCrawler(targets = targets, threads=nthread)
        elif mode == 'inventory': 
            return AmazonInventoryCrawler(targets = targets, threads=nthread)

    def run(self, task, mode):
        tasks = self.get_task(task, mode)
        if tasks:
            print(f"This round has collected {len(tasks)} targets from allocator.")
            print(f"task: {task}, mode: {mode}, target: {tasks[:4]}")
            nthread = 4
            mybot = self.get_bots(mode, tasks, nthread)
            mybot.setProxies(proxies=AUTO)
            mybot.start()
        else:
            print("Please input valid mode !!")
            return False 

if __name__ == "__main__":
    manager = Manager()
    task = "amazon"
    mode_unlabel = ['seller_products'] #['seller', 'static', 'sellerproducts'] #'seller','sellerproducts', ,'reviews','feedback','inventory']
    while True:
        for mode in mode_unlabel:
            print(f"starting {mode}")
            manager.run(task, mode)
            print(f"finished {mode}")
            time.sleep(10)
            kill_redundant_process()
