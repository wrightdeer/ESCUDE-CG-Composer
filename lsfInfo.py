import os


class BlockInfo:
    def __init__(self, name, x, y, type, id, mode):
        self.name = name
        self.x = x
        self.y = y
        self.type = type
        self.id = id
        self.mode = mode


class LSFFile:
    def __init__(self, file_path):
        self.file_path = file_path
        self.x = 0
        self.y = 0
        self.name = os.path.splitext(os.path.basename(self.file_path))[0]
        self.naked_image = None
        self.blocks = self._parse_file()
        self.base_images = {}
        self.face_differences = {}
        self.face_effects = {}
        self.holy_light = {}

        self._process_blocks()

    def _parse_file(self):
        blocks = []
        with open(self.file_path, 'rb') as file:
            datas = file.read()
        datas = [int(d) for d in datas]
        num = datas[10]
        self.x = datas[12] + datas[13] * 256
        self.y = datas[16] + datas[17] * 256
        self.type = datas[25]
        for i in range(num):
            name = ""
            for j in range(20):
                if datas[28 + i * 164 + j] != 0:
                    name += chr(datas[28 + i * 164 + j])
                else:
                    break
            x = datas[28 + i * 164 + 128] + datas[28 + i * 164 + 129] * 256
            y = datas[28 + i * 164 + 132] + datas[28 + i * 164 + 133] * 256
            type = datas[28 + i * 164 + 152]
            id = datas[28 + i * 164 + 153]
            mode = datas[28 + i * 164 + 154]
            blocks.append(BlockInfo(name, x, y, type, id, mode))
        return blocks

    def _process_blocks(self):
        for block in self.blocks:
            if block.type == 0 and self.name[0] == '0':
                self.naked_image = block
            if block.mode != 0:
                continue
            if block.type == 0 or block.type == 3:
                if block.id not in self.base_images:
                    self.base_images[block.id] = []
                    if self.blocks[0].id == 0:
                        self.base_images[block.id].append(self.blocks[0])
                self.base_images[block.id].append(block)
            elif block.type % 10 == 0 or block.type == 1:
                n = block.type // 10
                if n not in self.face_differences:
                    self.face_differences[n] = {}
                if block.id not in self.face_differences[n]:
                    self.face_differences[n][block.id] = block
            elif block.type % 10 == 1 or block.type == 2:
                n = (block.type - 1) // 10
                if n not in self.face_effects:
                    self.face_effects[n] = {}
                self.face_effects[n][block.id] = block
            elif block.type == 255:
                self.holy_light[block.id] = block

    def get_name(self):
        return self.name

    def get_base_images_keys(self):
        return list(self.base_images.keys())

    def get_face_differences_keys(self):
        keys = {}
        for n in self.face_differences:
            keys[n] = list(self.face_differences[n].keys())
        return keys

    def get_face_effects_keys(self):
        keys = {}
        for n in self.face_effects:
            keys[n] = list(self.face_effects[n].keys())
        return keys

    def get_holy_light_keys(self):
        return list(self.holy_light.keys())

    def get_operation_blocks(self, bi_key, fd_keys, fe_keys, hl_key):
        blocks = []
        # 初始化键值
        if bi_key not in self.base_images:
            bi_key = min(self.base_images)

        for face_differences in self.face_differences:
            if face_differences not in fd_keys:
                fd_keys[face_differences] = 1
            else:
                if fd_keys[face_differences] not in self.face_differences[face_differences]:
                    fd_keys[face_differences] = 1

        for face_effects in self.face_effects:
            if face_effects not in fe_keys:
                fe_keys[face_effects] = 0
            else:
                if fe_keys[face_effects] not in self.face_effects[face_effects]:
                    fe_keys[face_effects] = 0

        if hl_key not in self.holy_light:
            hl_key = 0

        # 添加块
        for base_image in self.base_images[bi_key]:
            blocks.append(base_image)

        for face_effects in fe_keys:
            if face_effects in self.face_effects and fe_keys[face_effects] != 0:
                blocks.append(self.face_effects[face_effects][fe_keys[face_effects]])

        for face_differences in fd_keys:
            if face_differences in self.face_differences:
                blocks.append(self.face_differences[face_differences][fd_keys[face_differences]])

        if self.naked_image is not None:
            blocks.append(self.naked_image)

        if hl_key != 0:
            blocks.append(self.holy_light[hl_key])

        # 将blocks按block.name排序
        blocks.sort(key=lambda block: block.name)

        return blocks


if __name__ == '__main__':
    lsf_file = LSFFile('data/EV_A02.lsf')
    bi_key = 3  # 基础图片的ID
    fd_keys = {1: 3, 2: 2, 3: 1}  # 脸部差分的启用情况
    fe_keys = {1: 2}  # 脸部特效的启用情况
    hl_key = 0  # 圣光效果的ID

    main_base_image, operation_blocks = lsf_file.get_operation_blocks(bi_key, fd_keys, fe_keys, hl_key)
    print(main_base_image)
    for block in operation_blocks:
        print(block)
