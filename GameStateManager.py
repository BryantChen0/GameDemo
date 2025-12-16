import re
import math
# --------------------------------------------------
# 更新状态的工具类
# --------------------------------------------------
class GameStateManager:
    def __init__(self, player_state, world_state, event_state):
        self.player = player_state
        self.world = world_state
        self.event = event_state

    def apply_change(self, event):
        #更新属性变化
        self.apply_property_change(event.get("property_change", []))
        #更新状态变化
        self.apply_state_change(event.get("state_change", []))
        #更新物品或能力变化
        self.apply_object_change(event.get("object_change", []))
        #根据当前属性，更新状态上限
        self.update_max_state()
        #根据总结将其放入当前状态
        self.event["当前状态"] = event.get("conclusion", "")

    def update_max_state(self):
        #随着属性的变化来进行状态的变化，同时检查是否合法
        CON = math.log1p(math.exp(self.player["体质"] - 1))
        INT = math.pow((self.player["智力"] - 1), 1.2)
        AVG = max(0, (
            self.player["体质"] +
            self.player["力量"] +
            self.player["敏捷"] - 3
        ) / 3)

        #血量上限随着体质属性的变化来变化，其收益会随着体质的增长而递减
        self.player["生命上限"] = max(1, int(100 + 2 * CON))

        #法力上限随着智力属性的变化来变化，其收益会随着智力的增长而增长
        self.player["法力上限"] = max(1, int(50 + 2 * INT))

        #体力上限随着敏捷，力量，体质的平均数来变化，其收益平均化，但是较低
        self.player["体力上限"] = max(1, int(100 + AVG))

        # 防止当前值超过最大值
        self.player["生命"] = min(self.player["生命"], self.player["生命上限"])
        self.player["法力"] = min(self.player["法力"], self.player["法力上限"])
        self.player["体力"] = min(self.player["体力"], self.player["体力上限"])

        # 当前状态下限 0，上限对应最大值
        for k, max_k in [
            ("生命", "生命上限"),
            ("法力", "法力上限"),
            ("体力", "体力上限")
        ]:
            self.player[k] = max(0, min(self.player[k], self.player[max_k]))

    def apply_state_change(self, states):
        #状态变化
        for text in states:
            text = text.replace(" ", "")
            match = re.match(r"(.+?)([+-]\d+)", text)
            if match:
                key = match.group(1).strip()
                value = int(match.group(2))
                if key in self.player:
                    self.player[key] += value
            else:
                print("无法解析状态变动： ", text)
                return

    def apply_property_change(self, props):
        # 属性变动
        for text in props:
            text = text.replace(" ", "")
            match = re.match(r"(.+?)([+-]\d+)", text)
            if match:
                key = match.group(1).strip()
                value = int(match.group(2))
                if key in self.player:
                    self.player[key] = max(0, self.player[key] + value)
            else:
                print("无法解析属性变动： ", text)
                return

    def apply_object_change(self, objs):
        #物品变动
        for text in objs:
            text = text.strip()
            text = re.sub(r"\s+", " ", text)
            match = re.match(r"(获取|失去)\s*(装备|物品|能力)\s*[:：]\s*([^\s，,]+)[，,]\s*(?:介绍|说明|描述)\s*[:：]\s*(.+)", text)
            if match:
                action, object_type, object_name, description = match.groups()

                if action == "获取":
                    self.player[object_type].append({"名字": object_name, "介绍": description})
                elif action == "失去":
                    self.player[object_type] = [
                        i for i in self.player[object_type]
                        if i["名字"] != object_name
                    ]
            else:
                print("无法解析物品变动： ", text)
                return

    def apply_task_change(self, tasks):
        #任务变动
        for text in tasks:
            text = text.replace(" ", "")
            match = re.match(r"(完成|接取)\S+\s*：\s*(\S+)", text)
            if match:
                action, task = match.groups()

                if action == "接取":
                    self.event["任务"] = task
                elif action == "完成":
                    self.event["任务"] = "无"
            else:
                print("无法解析任务变动： ", text)
                return