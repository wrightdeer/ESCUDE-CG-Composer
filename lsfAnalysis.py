import os
from PIL import Image  # 添加PIL库用于图像处理


def parse_coordinates(dir_path):
    for file in os.listdir(dir_path):
        if file.endswith('.lsf'):
            file_path = os.path.join(dir_path, file)
            parse_coordinate(file_path)


def parse_coordinate(file_path):
    with open(file_path, 'rb') as file:
        datas = file.read()
    datas = [int(d) for d in datas]

    num = datas[10]
    for i in range(num):
        if datas[28 + i * 164] != 0x30:
            break
        name = ""
        for j in range(20):
            if datas[28 + i * 164 + j]!=0:
                name+=chr(datas[28 + i * 164 + j])
            else:
                break
        print(f"{name}\t{datas[28 + i * 164 + 128:28 + i * 164 + 164]}")
        # name = "".join(chr(datas[28 + i * 164 + j]) for j in range(10))



if __name__ == '__main__':
    dir_path = 'data/st_0'
    a = 30
    print(chr(a))
    parse_coordinates(dir_path)
