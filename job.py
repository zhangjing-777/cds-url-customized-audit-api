from apscheduler.schedulers.background import BackgroundScheduler
from gys_travelsky_com_cn.gys_travelsky_com_cn import *
from travelskyir_com.travelskyir_com import *
from travelsky_cn.travelsky_cn import *
from hx_client import *
import threading
import time

def job1():
    TravelskyCn(thread_count=thread_count).start()
    try:
        while True:
            if len(threading.enumerate()) == 1:
                meta_json_path = os.path.join(date_path, 'meta.json')
                with open(meta_json_path, 'w', encoding='utf8') as f:
                    json.dump(meta_json, f, ensure_ascii=False, indent=4)
                break
            time.sleep(5)
    except Exception as e:
        print(str(e))
        return 
    time_start = time.time()     
    process_site("/home/spider/travelsky_cn/data")
    time_end = time.time()
    time_diff = time_end - time_start
    logger.info("处理网站内容用时: %d 秒" %int(time_diff))
 
def job2():
    GysTravelskyComCn(thread_count=thread_count).start()
    try:
        while True:
            if len(threading.enumerate()) == 1:
            
                meta_json_path = os.path.join(date_path, 'meta.json')
                with open(meta_json_path, 'w', encoding='utf8') as f:
                    json.dump(meta_json, f, ensure_ascii=False, indent=4)
                break
            
            time.sleep(5)
    except Exception as e:
        print(str(e))
        return 
    time_start = time.time()     
    process_site("/home/spider/gys_travelsky_com_cn/data")
    time_end = time.time()
    time_diff = time_end - time_start
    logger.info("处理网站内容用时: %d 秒" %int(time_diff))

def job3():
    TravelskyirCom(thread_count=thread_count).start()
    try:
        while True:
            if len(threading.enumerate()) == 1:
                meta_json_path = os.path.join(date_path, 'meta.json')
                with open(meta_json_path, 'w', encoding='utf8') as f:
                    json.dump(meta_json, f, ensure_ascii=False, indent=4)
                break
            time.sleep(5)
    except Exception as e:
        print(str(e))
        return
    time_start = time.time()     
    process_site("/home/spider/travlskyir_com/data")
    time_end = time.time()
    time_diff = time_end - time_start
    logger.info("处理网站内容用时: %d 秒" %int(time_diff))



def delete_folder(path):	
   
    current_time = datetime.now()
    for folder in os.listdir(path):
        folder_path = os.path.join(path, folder)
        if os.path.isdir(folder_path):
            print(folder)
            folder_creation_time = datetime.strptime(folder, "%Y-%m-%d_%H_%M_%S")
            if folder_creation_time < current_time:
                shutil.rmtree(folder_path)
                print(f"Deleted folder: {folder_path}")

def deletejob():
    print("start delete job")
    print(datetime.now())
    delete_folder("/home/spider/gys_travelsky_com_cn/data")
    delete_folder("/home/spider/travelsky_cn/data")
    delete_folder("/home/spider/travelskyir_com/data")
    
#scheduler = BackgroundScheduler()
#scheduler.add_job(job1, 'cron', seconds = 10)
#scheduler.add_job(job2, 'interval', seconds = 20)
#scheduler.add_job(job3, 'interval', seconds = 15)
#scheduler.start()

#while True:
#    time.sleep(1)

while True:
    job1()
    job2()
    job3()
    deletejob()
    time.sleep(2400)