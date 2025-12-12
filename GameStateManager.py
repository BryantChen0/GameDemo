import re
# --------------------------------------------------
# 更新状态的工具类
# --------------------------------------------------
class GameStateManager:
    def __init__(self, player_state, world_state):
        self.player = player_state
        self.world = world_state

    def apply_change(self, event):
        self.apply_property_change(event.get("property_change", []))
        self.apply_object_change(event.get("object_change", []))

        # 更新世界状态
        self.world["当前状态"] = event.get("conclusion", "")

    def apply_state_change(self, state):
        #状态变化


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