#%%
from crawler_v2 import *

import socket, psutil
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

                name = p.name().lower()
                if 'python' in name:
                    kill_process(pid)
                    # print(p.exe())
                    # print(p.cwd())
                    # print("pid-%d, pname-%s" %(pid, p.name()))
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
    
    def get_task(self, mode):
        for priority in ['urgent','normal']:
            url = 'http://192.168.2.94:8080/v2/'
            hostname=socket.gethostname()
            IPAddr=socket.gethostbyname(hostname)
            myobj = {priority: mode,'IP':IPAddr}
            x = requests.post(url, data = myobj)
            targets = []
            try:
                targets = json.loads(x.text)
                if targets:
                    print(priority, mode,targets[0])
                    return {mode:targets}
            except:
                continue
            if targets:
                print(priority, mode,targets[0])
                return targets
        return False

    def get_bots(self, mode, targets, nthread):
        if mode == 'static':
            return AmazonStaticCrawler(targets = targets, threads=nthread)
        elif mode == 'seller':
            return AmazonSellerCrawler(targets = targets, threads=nthread)
        elif mode == 'sellerproducts':
            return AmazonSellerProductsCrawler(targets = targets, threads=nthread)
        elif mode == 'reviews': 
            return AmazonReviewsCrawler(targets = targets, threads=nthread)
        elif mode == 'feedback': 
            return AmazonFeedbackCrawler(targets = targets, threads=nthread)
        elif mode == 'inventory': 
            return AmazonInventoryCrawler(targets = targets, threads=nthread)

    def run(self, mode):
        tasks = self.get_task(mode)
        if tasks:
            mode = list(tasks.keys())[0]
            targets = list(tasks.values())[0]
            print(f"This round has collected {len(targets)} targets from allocator.")
            print(f"{mode}: {targets[:1]}")
            nthread = 6
            mybot = self.get_bots(mode, targets, nthread)
            mybot.setProxies(proxies=AUTO)
            mybot.start()
        else:
            print("Please input valid mode !!")
            return False 

if __name__ == "__main__":
    manager = Manager()
    mode_unlabel = ['static'] #['seller', 'static', 'sellerproducts'] #'seller','sellerproducts', ,'reviews','feedback','inventory']
    while True:
        for mode in mode_unlabel:
            print(f"starting {mode}")
            manager.run(mode)
            print(f"finished {mode}")
            time.sleep(10)
            kill_redundant_process()
