from tool import *

if __name__ == '__main__':

    keywords = "amazon"
    try:
        if sys.argv[1] in ['check', 'kill']:
            mode = sys.argv[1] 
    except:
        logging.info("#################################################")
        logging.info("usage: python $(pwd)/tool.py check/kill keywords#")
        logging.info("keywords should be within: 'amazon' (default),  #")
        logging.info(" 'amazon_asin', 'js_database', 'js_opportunity' #")
        logging.info("check for the monitoring crawler mode           #")
        logging.info("kill for the killing redundant process          #")
        logging.info("#################################################")
        pass
    try:
        if sys.argv[2] in ['amazon', 'amazon_asin', 'amazon_node', 'js_database', 'js_opportunity']:
            keywords = sys.argv[2]
    except:
        logging.info("#################################################")
        logging.info("usage: python $(pwd)/tool.py check/kill keywords#")
        logging.info("keywords should be within: 'amazon' (default),  #")
        logging.info(" 'amazon_asin', 'js_database', 'js_opportunity' #")
        logging.info("check for the monitoring crawler mode           #")
        logging.info("kill for the killing redundant process          #")
        logging.info("#################################################")
        pass
    try:
        args = sys.argv[3]
    except:
        args = ''
    manager = controller()
    worker = executor() 
    ## must write func outside the class having mp.process(func)
    if mode == 'check':
        try:
            manager.check(worker.restart, keywords)
        except KeyboardInterrupt:
            logging.info("checking end by keyboard interrupt")
            pass
    elif mode == "kill":
        manager.massacre()
    else:
        print("##############################################")
        print("usage: python $(pwd)/run_tool.py  check/kill #")
        print("check for the monitoring crawler mode        #")
        print("kill for the killing redundant process       #")
        print("##############################################")
