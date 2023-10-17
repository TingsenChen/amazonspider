from py import process
import pymongo
import time
import psutil
import os
import multiprocessing as mp
import datetime
import sys
import msvcrt
from threading import Timer
import logging
if not os.path.exists("./log"):
    os.mkdir("./log")
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", datefmt="%Y-%m-%d %H:%M:%S", handlers = [logging.FileHandler('./log/tool.log','a','utf-8'), logging.StreamHandler()])

### change the target to monitor


# get your anaconda python.exe here
environment_exe_path = "D:\Anaconda3\python.exe"

# set check period time(s)
check_interval = 60*2
reboot_interval = 3600*2
max_chrome_process = 160

class executor():
    def __init__(self) -> None:
        pass

    def restart(self, keywords):
        if keywords == "amazon":
            process = rf"python {os.path.expanduser('~')}\AmazonSpider\AmazonSpider\main_v3.py"
        if keywords == "amazon_asin":
            process = rf"python {os.path.expanduser('~')}\AmazonSpider\AmazonSpider\crawler_by_class.py"
        if keywords == "amazon_node":
            process = rf"python {os.path.expanduser('~')}\AmazonSpider\AmazonSpider\crawler_by_class_get_node_id.py"
        elif keywords == "js_database":
            process = rf"python {os.path.expanduser('~')}\AmazonSpider\JungleScout\crawler_v2.py"
        elif keywords == "js_opportunity":
            process = rf"python {os.path.expanduser('~')}\AmazonSpider\JungleScout\oppotunity_crawler_v2.py"
        os.system(process)

class controller():
    def __init__(self) -> None:
        self.processes = []
        pass
    
    def input_with_timeout(self, prompt, timeout, timer=time.monotonic):
        sys.stdout.write(prompt)
        sys.stdout.flush()
        endtime = timer() + timeout
        result = []
        while timer() < endtime:
            if msvcrt.kbhit():
                result.append(msvcrt.getwche()) #XXX can it block on multibyte characters?
                if result[-1] == '\r':
                    return ''.join(result[:-1])
            time.sleep(0.04) # just to yield to other processes/threads
        return ""
    
    def count_chrome_process(self, ):
        counter = 0
        for pid in psutil.pids():
            try:
                if psutil.pid_exists(pid):
                    p = psutil.Process(pid)
                    name = p.name().lower()
                    if 'chrome' in name:
                        counter+=1
            except:
                pass
        return counter
    
    def pause_to_add_counter(self, timeout = 10):
        clutch = -1
        prompt = "You have %d seconds to decide whether restart the program \n" % timeout
        try:
            clutch = int(self.input_with_timeout(prompt, timeout))
        except:
            logging.info('Sorry, times up')
        else:
            logging.info(f'clutch: {clutch}')
        return clutch

    # def get_all_children(self, proc: psutil.Process):
    #     try:
    #         if len(proc.children()) == 0:
    #             return []
    #         else:
    #             returned_list = []
    #             for item in proc.children():
    #                 returned_list.append(item)
    #                 returned_list.extend(self.get_all_children(item))
    #             return returned_list
    #     except psutil.NoSuchProcess:
    #         return []

    # def terminate_subprocess(self, procs):
    #     for t in procs:
    #         logging.info(f"killing {t.name}")
    #         children = self.get_all_children(psutil.Process(pid=t.pid))
    #         try:
    #             t.terminate()
    #         except:
    #             pass # in case the process was already dead
    #         for child in children:
    #             try:
    #                 child.terminate()
    #             except psutil.NoSuchProcess:
    #                 pass  # in case child was already dead
    
    def kill_process(self, pid):
        if psutil.pid_exists(pid):
            process = "taskkill /f /pid %d"%pid
            os.system(process)
        else:
            pass

    def kill_redundant_process(self, ):
        for pid in psutil.pids():
            try:
                if psutil.pid_exists(pid) and pid != os.getpid() and pid != os.getppid():
                    p = psutil.Process(pid)
                        
                    if p.exe() == environment_exe_path:
                        continue

                    name = p.name().lower()
                    if 'python' in name:
                        self.kill_process(pid)
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
                        self.kill_process(pid)
                        # print(p.exe())
                        # print(p.cwd())
                        # print("pid-%d, pname-%s" %(pid, p.name()))
            except:
                pass

    def massacre(self, counter=40):
        kill_start = time.time()
        while time.time()-kill_start<5+counter*0.5 or self.count_chrome_process()>0:
            self.kill_redundant_process()
            print("PROCESS MASSACRE!!!!")
    
    def check(self, func, keywords):        
        cur_process = None
        last_reboot_time = time.time()
        REBOOT = False
        while True:
            clutch = self.pause_to_add_counter(check_interval)
            counter = self.count_chrome_process()
            time_since_last_reboot = time.time()-last_reboot_time
            logging.info(f'# chrome process: {counter}, # seconds since last reboot: {time_since_last_reboot:.2f}')
            REBOOT = counter > max_chrome_process or clutch == 1 or clutch == 0 or time_since_last_reboot > reboot_interval
            logging.debug(f"REBOOT: {REBOOT}")
            if REBOOT:
                logging.info(str(datetime.datetime.now()))
                logging.info("killing and restart begin...")
                self.massacre(counter)
                
                if cur_process:
                    cur_process.kill()
                    logging.debug("REBOOTING")
                    # try:
                    #     self.terminate_subprocess(self.processes)
                    # except Exception as e:
                    #     print(e)
                    #     pass
                    time.sleep(5) 
                if clutch == 0:
                    logging.debug("EXITING")
                    try:
                        self.massacre(counter)
                    except Exception as e:
                        print(e)
                        pass
                    time.sleep(5)  
                    logging.info("EXIT")
                    return False
                    break
                # ctx = mp.get_context("spawn")
                # (child, pipe) = ctx.Pipe(duplex=True)
                while True:
                    try:
                        cur_process = None
                        cur_process = mp.Process(target=func, args = (keywords,), name = f"{keywords}_{time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))}")
                        cur_process.start()
                        cur_process.join(1) 
                    except Exception as e:
                        print("process fail to start")
                        print(e)
                        time.sleep(5)
                    else:
                        self.processes.append(cur_process)
                        break
                logging.info(f"{time.time()-last_reboot_time:.2f} seconds since last restart...")
                clutch = -1
                last_reboot_time = time.time()

            else:
                ## monitor database
                continue


