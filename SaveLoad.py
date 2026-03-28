import json

#存档读档的模块
class SaveLoad:
    def __init__(self, json_data):
        self.json_data = json_data

    # --------------------------------------------------
    # 存档
    # --------------------------------------------------
    def save(self, data, player_state, world_state, task_state, event_state):
        data["player_state"] = player_state
        data["world_state"] = world_state
        data["task_state"] = task_state
        data["event_state"] = event_state
        with open(self.json_data, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    # --------------------------------------------------
    # 读档
    # --------------------------------------------------
    def load(self):
        with open(self.json_data, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"player_state": data["player_state"],
                "world_state": data["world_state"],
                "task_state": data["task_state"],
                "event_state": data["event_state"]}

