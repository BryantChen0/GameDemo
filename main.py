import json
import re
from google import genai
from google.genai import types

# --------------------------------------------------
# 初始化 API
# --------------------------------------------------
API_KEY = "AIzaSyDAopqnOSxalLPjmRGnenka--8bHY9LlrE"
client = genai.Client(api_key=API_KEY)

# --------------------------------------------------
# JSON Schema：强制输出结构
# --------------------------------------------------
event_schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "outcome": types.Schema(type=types.Type.STRING),
        "description": types.Schema(type=types.Type.STRING),
        "change": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        "conclusion": types.Schema(type=types.Type.STRING)
    },
    required=["outcome", "description", "conclusion"]
)

# --------------------------------------------------
# 玩家状态
# --------------------------------------------------
player_state = {
    "玩家名字": "玩家1",
    "血量": 100,
    "法力": 50,
    "体力": 100,

    "体质": 1,
    "敏捷": 1,
    "力量": 1,
    "智力": 1,
    "魅力": 1,

    "能力": [
        {"技能名字": "火焰法球", "技能消耗": 5, "技能介绍": "造成中等火焰伤害"},
        {"技能名字": "隐匿术", "技能消耗": 5, "技能介绍": "提高潜行成功率"}
    ],
    "装备": [],
    "物品": [{"物品名字": "木棍", "耐久": 100, "物品介绍": "一根普通的木棍"}]
}

# --------------------------------------------------
# 世界状态
# --------------------------------------------------
world_state = {
    "世界名字": "测试空间",
    "世界ID": 0,
    "危险度": 0,
    "世界介绍": "这是一个用于测试使用的空间，这里的任何技能都能生效，玩家可以使用任何指令",

    "科技水平": 10,
    "魔力总量": 10,
    "能力体系": "没有任何的能力体系",
    "当前任务": "无",
    "当前状态": "无"
}

# --------------------------------------------------
# 生成 Prompt
# --------------------------------------------------
def generate_prompt(player_state, world_state, player_action):
    return f"""
    你是「无限流文字游戏」的系统仲裁者（System Arbiter）。
    
    你的任务：
    1. 根据【玩家状态】、【世界状态】、【玩家行动】进行一次合理判定。
    2. 输出严格 JSON，不添加多余解释。
    3. 不向玩家提供提示，不改变玩家意图。
    4. 你负责叙事与判定，不负责指导玩家。
    5. 所有叙事内容只放在 description 字段中。
    6. 最后总结目前内容为1到2句话并放到conclusion字段中。
    7. 对于任何属性的变化，请使用血量，法力，体力，体质，敏捷，力量，智力和魅力的数值变动.
    8. 对于任何物品的获取或者失去，请使用获得某件物品或者失去某件物品
    
    判定结果类型固定为：
    crit（大成功）、success（成功）、partial（部分成功）、failure（失败）、fumble（大失败）
    
    玩家状态：{json.dumps(player_state, ensure_ascii=False)}
    世界状态：{json.dumps(world_state, ensure_ascii=False)}
    玩家行动：{json.dumps(player_action, ensure_ascii=False)}
    
    请输出严格符合 schema 的 JSON。
    """


# --------------------------------------------------
# 调用模型
# --------------------------------------------------
def generate_event(client, prompt):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.8,
            max_output_tokens=3000,
            response_mime_type="application/json",
            response_schema=event_schema
        )
    )
    return response.text

# --------------------------------------------------
# 更新状态
# --------------------------------------------------
def update_states(event, player_state, world_state):
    def apply_change(text):
        """
        根据字符串内容来判断对 player_state 的影响。
        自动识别 HP/MP/体力/属性 等等，只要格式像 XXX±数字。
        也能识别 “获得 物品名”。
        """
        # 数值类变动
        match = re.match(r"(.+?)([+-]\d+)", text)
        if match:
            key = match.group(1).strip()
            data = int(match.group(2))

            if key in player_state:
                player_state[key] += data
                return

        # 获得物品
        if text.startswith("获得"):
            item_name = text.replace("获得", "").strip()
            player_state["物品"].append({"物品名字": item_name})
            return

        #失去物品
        if text.startswith("失去"):
            item_name = text.replace("失去", "").strip()
            player_state["物品"].remove(item_name)
            return


    # 遍历 rewards
    for c in event.get("change", []):
        apply_change(c)

    # 更新世界状态
    world_state["当前状态"] = event.get("conclusion", "")

    return player_state, world_state


# --------------------------------------------------
# 游戏 Loop
# --------------------------------------------------
def main():
    print("欢迎来到无限流文字游戏 DEMO！")
    print(f"你进入了世界：{world_state['世界名字']}")

    for turn in range(10):
        action_name = input("\n请输入动作名称（如 攻击 / 潜行 / 使用技能）: ")
        target = input("目标（可空）: ")
        used_ability = input("使用技能（可空）: ")

        player_action = {
            "action": action_name,
            "target": target or None,
            "used_ability": used_ability or None
        }

        prompt = generate_prompt(player_state, world_state, player_action)

        print("\n--- AI 事件判定 ---")

        event_text = generate_event(client, prompt)
        print(event_text)

        # 解析 JSON
        try:
            event = json.loads(event_text)
            update_states(event, player_state, world_state)

            print("\n判定结果：", event["outcome"])
            print("叙述：", event["description"])
            print("变化：", event.get("change"))

        except Exception as e:
            print("❌ JSON 解析失败：", e)
            print("原文：", event_text)


if __name__ == "__main__":
    main()
