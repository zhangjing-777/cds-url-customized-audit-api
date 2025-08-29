import os
import shutil
from datetime import datetime


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



delete_folder("/home/spider/gys_travelsky_com_cn/data")
delete_folder("/home/spider/travelsky_cn/data")
delete_folder("/home/spider/travelskyir_com/data")
