import re
import math

# --------------------------------------------------
# 更新游戏状态的模块
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
        # 更新物品变化
        self.apply_object_change(event.get("object_change", []))
        # 更新能力变化
        self.apply_ability_change(event.get("ability_change", []))
        # 根据当前属性，更新状态上限
        self.update_max_state()
        # 更新世界变化
        self.apply_world_change(event.get("world_change", {}))
        # 更新任务变化
        self.apply_task_change(event.get("task_change", {}))
        # 根据总结将其放入当前状态
        self.apply_event_change(event.get("conclusion", ""))

    #属性变更模块
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

    #技能变更模块
    #计算数值
    def calculate_ability_value(self, quality, strength, attr):
        #技能品质系数
        QUALITY_MULTIPLIER = {
            "普通": 1.0,
            "优秀": 1.2,
            "稀有": 1.5,
            "史诗": 2.0,
            "传说": 3.0
        }

        #强度基础数值
        BASE_VALUE_TABLE = {
            "弱": 10,
            "中": 20,
            "强": 35,
            "极强": 60
        }

        return (self.player.get(attr, 0) + BASE_VALUE_TABLE.get(strength, 0)) * QUALITY_MULTIPLIER.get(quality, 1.0)

    def apply_ability(self, ability_name, target=None):
        ability = next((a for a in self.player["ability"] if a["ability_name"] == ability_name), None)

        if not ability:
            return {"error": "技能不存在"}

        # 消耗检查
        for k, v in ability.get("cost", {}).items():
            if self.player.get(k, 0) < v:
                return {"error": f"{k}不足"}

        for k, v in ability.get("cost", {}).items():
            self.player[k] -= v

        return {"success": True}

    def apply_ability_change(self, abilities):
        if not isinstance(abilities, list):
            return
        for ability in abilities:
            if not isinstance(ability, dict):
                continue

            action = ability.get("action")
            ability_type = ability.get("type")
            ability_cost = ability.get("cost")
            quality = ability.get("quality")
            ability_name = ability.get("ability_name")
            ability_desc = ability.get("ability_description")
            effect = ability.get("effect")
            strength = effect.get("strength")
            attr = effect.get("attr")

            if action == "获取":
                value = self.calculate_ability_value(quality, strength, attr)
                effect["value"] = value
                self.player["ability"].append({"type": ability_type, "cost": ability_cost, "quality": quality, "ability_name": ability_name, "ability_description": ability_desc, "effect": effect})
                matches = re.findall(r"(体质|力量|敏捷|智力|魅力)([+\-*/])(\d+(\.\d+)?)", ability_desc)
                for stat, op, val, _ in matches:
                    val = float(val)
                    current = self.player.get(stat, 0)

                    if op == "+":
                        current += val
                    elif op == "-":
                        current -= val
                    elif op == "*":
                        current *= val
                    elif op == "/":
                        if val != 0:
                            current /= val

                    self.player[stat] = current
            elif action == "失去":
                self.player["ability"] = [i for i in self.player["ability"] if i.get("ability_name") != ability_name]

    #物品变更模块

    def apply_object_change(self, objs):
        if not isinstance(objs, list):
            return
        for item in objs:
            if not isinstance(item, dict):
                continue

            action = item.get("action")
            obj_type = item.get("type")
            name = item.get("object_name")
            desc = item.get("object_description", "")
            effects = item.get("effect")


            if not obj_type or obj_type not in self.player:
                continue

            if action == "获取":
                self.player[obj_type].append({"object_name": name, "object_description": desc})
                for effect in effects:
                    stat = effect.get("name")
                    mode = effect.get("mode")
                    val = effect.get("delta")

            elif action == "失去":
                self.player[obj_type] = [i for i in self.player[obj_type] if i.get("object_name") != name]

    #事件变更模块
    def apply_world_change(self, world):
        if not isinstance(world, dict):
            return
        action = world.get("action")
        world_name = world.get("world_name")
        desc = world.get("world_description", "")

        if action == "进入" and world_name:
            self.world.clear()
            self.world.update({"world_name": world_name, "world_description": desc})
        elif action == "退出":
            self.world.clear()
            self.world.update({"world_name": "起源空间", "world_description": "一切的开始，绝对安全的空间，玩家不会在这里受到任何伤害。玩家需求的一切都能在这里得到，但是需要花费积分购买。这里的空间意志会发布任务让玩家来获取奖励（包括但不限于积分，技能，装备或者其他东西）"})

    #任务变更模块
    def apply_task_change(self, task):
        if not isinstance(task, dict):
            return
        action = task.get("action")
        task_name = task.get("task_name")
        desc = task.get("task_description", "")
        reward = task.get("reward")

        if action == "接取" and task_name:
            self.task.clear()
            self.task.update({"task_name": task_name, "task_description": desc, "reward": reward})
        elif action == "完成":
            self.task.update({"task_name": "无", "task_description": "无", "reward": "无"})

    #事件变更模块
    def apply_event_change(self, event):
        if not isinstance(self.event, dict):
            return
        # 确保历史记录列表存在
        self.event.setdefault("history", [])
        self.event["current_status"] = event
        self.event["history"].append(event)
