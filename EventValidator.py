# 检查AI的输出是否合法并且修复不合法的模块

class EventValidator:
    def __init__(self, event: dict):
        self.event = event

    def validate(self):
        if not isinstance(self.event, dict):
            return EventValidator.default_event()

        clean = {}
        clean["outcome"] = str(self.event.get("outcome", "failure"))
        clean["description"] = str(self.event.get("description", ""))
        clean["conclusion"] = str(self.event.get("conclusion", ""))
        clean["property_change"] = EventValidator.validate_property_change(
        )
        clean["ability_use"] = EventValidator.validate_ability_use(
            self.event.get("ability_use", [])
        )
        clean["task_options"] = self.event.get("task_options", [])
        clean["task_change"] = self.event.get("task_change", {})
        clean["world_change"] = self.event.get("world_change", {})
        clean["object_change"] = self.event.get("object_change", [])
        clean["ability_change"] = self.event.get("ability_change", [])

        return clean

    @staticmethod
    def validate_property_change(data):
        # 合法属性名称
        valid_properties = {"生命", "生命上限", "法力", "法力上限", "体力", "体力上限", "护盾", "体质", "敏捷", "力量", "智力", "魅力", "积分"}
        if not isinstance(data, list):
            return []

        result = []

        for item in data:
            if not isinstance(item, dict):
                continue

            name = item.get("name")
            delta = item.get("delta")

            if name not in valid_properties:
                continue

            try:
                delta = int(delta)
            except:
                continue

            result.append({
                "name": name,
                "delta": delta
            })

            return result

    @staticmethod
    def validate_ability_use(self, data):
        if not isinstance(data, list):
            return []

        result = []

        for item in data:
            if not isinstance(item, dict):
                continue

            name = item.get("ability_name")
            if not name:
                continue

            result.append({"ability_name": str(name)})

        return result

    @staticmethod
    def default_event():
        return {
            "outcome": "failure",
            "description": "系统未能解析事件。",
            "conclusion": "什么也没有发生。",
            "property_change": [],
            "ability_use": [],
            "task_options": [],
            "task_change": {},
            "world_change": {},
            "object_change": [],
            "ability_change": []
        }