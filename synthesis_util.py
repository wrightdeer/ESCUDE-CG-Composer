import os

import cv2
import numpy as np

from lsfInfo import LSFFile


def CG_synthesis_opencv(image, operation_block, dir_path, mode=0):
    op_path = os.path.join(dir_path, operation_block.name + '.png')
    if os.path.exists(op_path):
        op_image = cv2.imread(op_path, cv2.IMREAD_UNCHANGED)
        if op_image is not None:
            if image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)

            op_h, op_w, op_c = op_image.shape

            x, y = operation_block.x, operation_block.y

            if x + op_w > image.shape[1] or y + op_h > image.shape[0]:
                print("操作块图像超出主图像范围")
                return image

            if op_c == 4:
                op_alpha = op_image[:, :, 3] / 255.0
                op_rgb = op_image[:, :, :3]
            else:
                op_alpha = np.ones((op_h, op_w), dtype=np.float32)
                op_rgb = op_image

            roi = image[y:y + op_h, x:x + op_w]
            roi_rgb = roi[:, :, :3]
            roi_alpha = roi[:, :, 3] / 255.0

            composite_rgb = op_rgb * op_alpha[:, :, np.newaxis] + roi_rgb * (1 - op_alpha[:, :, np.newaxis])
            composite_alpha = op_alpha + roi_alpha * (1 - op_alpha)

            image[y:y + op_h, x:x + op_w, :3] = composite_rgb
            image[y:y + op_h, x:x + op_w, 3] = composite_alpha * 255


    return image


def synthesis(x,y,operation_blocks, dir_path):
    # image_filename = operation_blocks[0].name + '.png'
    # image = cv2.imread(os.path.join(dir_path, image_filename), cv2.IMREAD_UNCHANGED)
    image = np.zeros((y, x, 4),dtype=np.uint8)
    for block in operation_blocks:
        image = CG_synthesis_opencv(image, block, dir_path, 1)
    return image
