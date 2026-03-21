import json
import requests

#AI调用工具类
class Prompt:
    def __init__(self, player_state, world_state, task_state, event_state, player_action):
        self.player_state = player_state
        self.world_state = world_state
        self.task_state = task_state
        self.event_state = event_state
        self.player_action = player_action

    # --------------------------------------------------
    # 获取AI生成的事件
    # --------------------------------------------------
    def generate_event(self):
        prompt = f"""
            你将扮演为玩家创作无限流小说的系统仲裁者

            你的任务：
            1. 根据玩家状态、世界状态、任务状态、事件状态、玩家行动进行一次合理判定。
            2. 如果玩家当前的某项属性为负数，那么这个属性相关的判定极大概率产生负面结果。
            3. 你负责叙事与判定，不提供提示，也不改变玩家意图。
            4. 所有叙事内容只放在 description 字段中，判定结果类型写入 outcome 字段。
            5. 对于属性、状态、物品/能力、任务的变化，必须输出**结构化 JSON 对象**，不要字符串化。
            6. 最后总结目前内容为1到2句话并放到 conclusion 字段中。
            7. 绝对不要输出任何解释、提示或 Markdown 代码块。
            8. 当玩家表现出想要接取任务的意向时：
               - 只生成多个可选任务列表（task_options 字段）
               - 不允许修改 task_change
               - 不允许修改 world_change
               - 不进行剧情推进
            9. 只有当玩家明确选择某个任务时：
               - 才允许生成 task_change
               - 才允许触发 world_change（进入任务世界）
    
            玩家状态：{json.dumps(self.player_state, ensure_ascii=False)}
            世界状态：{json.dumps(self.world_state, ensure_ascii=False)}
            任务状态：{json.dumps(self.task_state, ensure_ascii=False)}
            事件状态：{json.dumps(self.event_state, ensure_ascii=False)}
            玩家行动：{json.dumps(self.player_action, ensure_ascii=False)}
    
            请严格输出 JSON，结构如下（必须遵守，不能缺少字段）：
            {{
              "outcome": "success",                 // 判定结果类型：crit、success、partial、failure、fumble
              "description": "描述文字",             // 事件叙事
              "task_options": [                     //将任务列表存放到这里
                  {{"task": "任务1", "description": "介绍"}},
                  {{"task": "任务2", "description": "介绍"}}
                ]
              "task_change":{{"action":"接取","task":"任务名","description":"任务介绍"}},// 任务变化，每项必须有 action、task、description
              "property_change": [                   // 属性变化，每项 name + delta
                {{"name":"属性名称","delta":数值变化}}
              ],
              "object_change": [                      // 物品/装备/能力变化，每项 action、type、name、description
                {{"action":"获取","type":"","name":"物品名称","description":"物品介绍"}}
              ],
              "world_change": {{"action":"进入","world":"世界名称","description":"世界介绍"}},
              "conclusion": "总结"
            }}
    
            注意：
            - 属性变化只允许使用：生命、法力、体力、体质、敏捷、力量、智力、魅力、积分。
            - 物品变化请写为对象：{{"action":"获取/失去","type":"装备/物品/能力","name":"名称","description":"说明"}}。
            - 任务变化请写为对象：{{"action":"接取/完成","task":"任务名","description":"任务介绍"}}。
            - 世界变化请写为对象：{{"action":"进入/退出","world":"世界名","description":"世界介绍"}}。
            - JSON 必须合法可解析，不允许任何多余文本、提示或 Markdown。
    
            严格按以上格式输出 JSON，不允许偏离。
            """
        url = "http://localhost:11434/api/generate"

        payload = {
            "model": "qwen2.5",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        response = requests.post(url, json=payload)
        print(response.text)
        return response.json()["response"]