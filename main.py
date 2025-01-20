import cv2
import numpy as np  # 添加numpy库导入
import os  # 添加os库导入，用于文件操作

from lsfInfo import LSFFile

if __name__ == '__main__':
    # dir_path = 'data'
    # lif_path = dir_path+'/EV_G05.lsf'
    # lsf = LSFFile(lif_path)
    # print(lsf.get_base_images_keys())

    dir_path_0 = 'data/ev_0'
    dir_path_1 = 'data/st_1'
    for file_0, file_1 in zip(os.listdir(dir_path_0), os.listdir(dir_path_1)):
        if file_0.endswith('.lsf') and file_1.endswith('.lsf'):
            file_path = os.path.join(dir_path_0, file_0)
            with open(file_path, 'rb') as f:
                data_0 = f.read()
            data_0 = [int(i) for i in data_0]
            print(f"0:\t{data_0[:28]}")
            file_path = os.path.join(dir_path_1, file_1)
            with open(file_path, 'rb') as f:
                data_1 = f.read()

            data_1 = [int(i) for i in data_1]
            print(f"1:\t{data_1[:28]}")
            for index, (d0, d1) in enumerate(zip(data_0[:28], data_1[:28])):
                if d0 != d1:
                    print(f"{index}:\t{d0}\t{d1}")