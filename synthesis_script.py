import os
import random

import cv2

from lsfInfo import LSFFile
from synthesis_util import synthesis

file_dir = 'data/ev_0'  # 换成解包的lsf文件与其他素材图片的路径
out_dir = 'output'  # 输出路径
files = os.listdir(file_dir)
for file in files:
    if file.endswith('.lsf'):
        file_path = os.path.join(file_dir, file)
        lsf = LSFFile(file_path)
        df_keys = lsf.get_face_differences_keys()
        for fds in df_keys:
            for fd in df_keys[fds]:
                for id in lsf.get_base_images_keys():
                    operation_blocks = lsf.get_operation_blocks(id, {fds: fd}, {}, 0)
                    result_image = synthesis(lsf.x, lsf.y,operation_blocks, file_dir)
                    if not os.path.exists(out_dir):
                        os.mkdir(out_dir)
                    cv2.imwrite(os.path.join(out_dir, lsf.name + f'_{id}_{fds}_{fd}.png'), result_image)
