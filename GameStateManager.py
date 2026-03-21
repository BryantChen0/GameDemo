import re
import math

# --------------------------------------------------
# 更新状态的工具类
# --------------------------------------------------
class GameStateManager:
    def __init__(self, player_state, world_state, task_state, event_state):
        self.player = player_state
        self.world = world_state
        self.task = task_state
        self.event = event_state

    def apply_change(self, event):
        # 安全解析 event 字段
        if not isinstance(event, dict):
            return

        # 更新属性变化
        self.apply_property_change(event.get("property_change", {}))
        # 更新物品或能力变化
        self.apply_object_change(event.get("object_change", {}))
        # 根据当前属性，更新状态上限
        self.update_max_state()
        # 更新世界变化
        self.apply_world_change(event.get("world_change", {}))
        # 更新任务变化
        self.apply_task_change(event.get("task_change", {}))
        # 根据总结将其放入当前状态
        self.apply_event_change(event.get("conclusion", ""))

    def update_max_state(self):
        CON = math.log1p(math.exp(self.player.get("体质", 0) - 1))
        INT = math.pow(max(0, self.player.get("智力", 0) - 1), 1.2)
        AVG = max(0, (
            self.player.get("体质", 0) +
            self.player.get("力量", 0) +
            self.player.get("敏捷", 0) - 3
        ) / 3)

        # 血量上限
        self.player["生命上限"] = max(1, int(100 + 2 * CON))
        # 法力上限
        self.player["法力上限"] = max(1, int(50 + 2 * INT))
        # 体力上限
        self.player["体力上限"] = max(1, int(100 + AVG))

        # 防止当前值超过最大值
        for k, max_k in [("生命", "生命上限"), ("法力", "法力上限"), ("体力", "体力上限")]:
            self.player[k] = max(0, min(self.player.get(k, 0), self.player[max_k]))

    def apply_property_change(self, props):
        if not isinstance(props, list):
            return
        for item in props:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            delta = item.get("delta", 0)
            if name in self.player:
                self.player[name] = self.player.get(name, 0) + delta

    def apply_object_change(self, objs):
        if not isinstance(objs, list):
            return
        for item in objs:
            if not isinstance(item, dict):
                continue
            action = item.get("action")
            obj_type = item.get("type")
            name = item.get("name")
            desc = item.get("description", "")

            if not obj_type or obj_type not in self.player:
                continue

            if action == "获取":
                self.player[obj_type].append({"名字": name, "介绍": desc})
                matches = re.findall(r"(体质|力量|敏捷|智力|魅力)[+](\d+)", desc)
                for stat, val in matches:
                    self.player[stat] = self.player.get(stat, 0) + int(val)
            elif action == "失去":
                self.player[obj_type] = [i for i in self.player[obj_type] if i.get("名字") != name]

    def apply_world_change(self, world):
        if not isinstance(world, dict):
            return
        action = world.get("action")
        world_name = world.get("name")
        desc = world.get("description", "")

        if action == "进入" and world_name:
            self.world = {"世界名字": world_name, "世界介绍": desc}
        elif action == "退出":
            self.world = {"世界名字": "起源空间", "世界介绍": "一切的开始"}

    def apply_task_change(self, task):
        if not isinstance(task, dict):
            return
        action = task.get("action")
        task_name = task.get("task")
        desc = task.get("description", "")

        if action == "接取" and task_name:
            self.task = {"任务": task_name, "介绍": desc}
        elif action == "完成":
            self.task = {"任务": "无", "介绍": "无"}

    def apply_event_change(self, event):
        if not isinstance(self.event, dict):
            return
        # 确保历史记录列表存在
        self.event.setdefault("历史", [])
        self.event["当前状态"] = event
        self.event["历史"].append(event)
