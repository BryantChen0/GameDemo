import re
import math
# --------------------------------------------------
# 更新状态的工具类
# --------------------------------------------------
class GameStateManager:
    def __init__(self, player_state, world_state):
        self.player = player_state
        self.world = world_state

    def apply_change(self, event):
        self.apply_property_change(event.get("property_change", []))
        self.apply_state_change(event.get("state_change", []))
        self.apply_object_change(event.get("object_change", []))

        # 更新世界状态
        self.world["当前状态"] = event.get("conclusion", "")

    def update_max_state(self):
        CON = max(0, self.player["体质"] - 1)
        INT = max(0, self.player["智力"] - 1)
        AVG = max(0, (
            self.player["体质"] +
            self.player["力量"] +
            self.player["敏捷"] - 3
        ) / 3)

        #血量上限随着体质属性的变化来变化，其收益会随着体质的增长而递减
        self.player["生命上限"] = int(100 + 1.2 * sqrt(CON))

        #法力上限随着智力属性的变化来变化，其收益会随着智力的增长而增长
        self.player["法力上限"] = int(50 + (INT ** 1.2))

        #体力上限随着敏捷，力量，体质的平均数来变化，其收益平均化，但是较低
        self.player["体力上限"] = int(100 + AVG)

        # 防止当前值超过最大值
        self.player["生命"] = min(self.player["生命"], self.player["最大生命"])
        self.player["法力"] = min(self.player["法力"], self.player["最大法力"])
        self.player["体力"] = min(self.player["体力"], self.player["最大体力"])

    def apply_state_change(self, states):
        #状态变化
        for text in states:
            match = re.match(r"(.+?)([+-]\d+)", text)
            if match:
                key = match.group(1).strip()
                value = int(match.group(2))
                if key in self.player:
                    self.player[key] += value
                    # 当前状态下限 0，上限对应最大值
                    if key == "生命":
                        self.player[key] = max(0, min(self.player[key], self.player["最大生命"]))
                    elif key == "法力":
                        self.player[key] = max(0, min(self.player[key], self.player["最大法力"]))
                    elif key == "体力":
                        self.player[key] = max(0, min(self.player[key], self.player["最大体力"]))

    def apply_property_change(self, props):
        # 属性变动
        for text in props:
            match = re.match(r"(.+?)([+-]\d+)", text)
            if match:
                key = match.group(1).strip()
                value = int(match.group(2))
                if key in self.player:
                    self.player[key] += value

    def apply_object_change(self, objs):
        #物品变动
        for text in objs:
            match = re.match(r"(获取|失去)\s*(\S+)\s*：\s*(\S+)，\S+：[^：]+：\s*(.+)", text)
            if match:
                action, object_type, object_name, description = match.groups()

                if action == "获取":
                    self.player[object_type].append({"名字": object_name, "介绍": description})
                elif action == "失去":
                    self.player[object_type] = [
                        i for i in self.player[object_type]
                        if i["名字"] != object_name
                    ]