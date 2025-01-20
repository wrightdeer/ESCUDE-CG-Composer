import os

import cv2
import numpy as np

from lsfInfo import LSFFile


def CG_synthesis_opencv(image, operation_block, dir_path, mode=0):
    op_path = os.path.join(dir_path, operation_block.name + '.png')
    if os.path.exists(op_path):
        # 读取操作块图像并确保它是 RGB 格式
        op_image = cv2.imread(op_path, cv2.IMREAD_UNCHANGED)
        if op_image is not None:
            # 确保主图像是 RGBA 格式
            if image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2RGBA)

            # 获取操作块图像的尺寸
            op_h, op_w, op_c = op_image.shape

            # 计算粘贴位置
            x, y = operation_block.x, operation_block.y

            # 确保操作块图像在主图像范围内
            if x + op_w > image.shape[1] or y + op_h > image.shape[0]:
                print("操作块图像超出主图像范围")
                return image

            # 提取操作块图像的 alpha 通道
            if op_c == 4:
                op_alpha = op_image[:, :, 3] / 255.0
                op_rgb = op_image[:, :, :3]
            else:
                op_alpha = np.ones((op_h, op_w), dtype=np.float32)
                op_rgb = op_image

            # 提取主图像的对应区域
            roi = image[y:y + op_h, x:x + op_w]
            roi_rgb = roi[:, :, :3]
            roi_alpha = roi[:, :, 3] / 255.0

            # 计算合成后的颜色和 alpha 通道
            composite_rgb = op_rgb * op_alpha[:, :, np.newaxis] + roi_rgb * (1 - op_alpha[:, :, np.newaxis])
            composite_alpha = op_alpha + roi_alpha * (1 - op_alpha)

            # 更新主图像的对应区域
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


if __name__ == '__main__':
    dir_path = 'D:\\program\\data\\bag\\0'
    lsf_file = LSFFile('D:\\program\\data\\bag\\0/EV_B09.lsf')
    bi_key = 5  # 基础图片的ID
    fd_keys = {1: 2, 2: 2, 3: 1}  # 脸部差分的启用情况
    fe_keys = {1: 1}  # 脸部特效的启用情况
    hl_key = 0  # 圣光效果的ID

    operation_blocks = lsf_file.get_operation_blocks(bi_key, fd_keys, fe_keys, hl_key)

    result_image = synthesis(operation_blocks, dir_path)
    out_dir = 'output'
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    cv2.imwrite(os.path.join(out_dir, 'output.png'), result_image)