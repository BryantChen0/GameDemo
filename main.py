import json
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
        "rewards": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        "consequences": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        "conclusion": types.Schema(type=types.Type.STRING)
    },
    required=["outcome", "description", "conclusion"]
)

# --------------------------------------------------
# 示例玩家状态
# --------------------------------------------------
player_state = {
    "name": "玩家1",
    "hp": 100,
    "mp": 50,
    "abilities": [
        {"name": "火焰法球", "type": "魔法", "cost": 5, "effect": "造成中等火焰伤害", "world_compatibility": 1.0},
        {"name": "隐匿术", "type": "技能", "cost": 3, "effect": "提高潜行成功率", "world_compatibility": 0.8}
    ],
    "items": []
}

# --------------------------------------------------
# 世界状态
# --------------------------------------------------
world_state = {
    "name": "废墟魔都",
    "world_type": "魔法",
    "danger_level": 3,
    "current_event": "无"
}

# --------------------------------------------------
# 生成 Prompt（不带规则）
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
    7. 血量和法力值的变化，使用HP和MP来表示
    
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
    # 如果事件给出了任何改变角色的状态
    rewards = event.get("rewards", [])
    for r in rewards:
        if "HP+" in r:
            value = int(r.split("HP+")[1])
            player_state["hp"] += value
            player_state["hp"] = min(player_state["hp"], 100)

        if "MP+" in r:
            value = int(r.split("MP+")[1])
            player_state["mp"] += value
            player_state["mp"] = min(player_state["mp"], 50)

        if "获得" in r:
            item_name = r.replace("获得", "").strip()
            player_state["items"].append(item_name)

    consequences = event.get("consequences", [])
    for c in consequences:
        if "HP-" in c:
            value = int(c.split("HP-")[1])
            player_state["hp"] -= value

        if "MP-" in c:
            value = int(c.split("MP-")[1])
            player_state["mp"] -= value

    # 对于每一个事件，都将总结后的事件发展传递到世界状态的当前事件中
    world_state["current_event"] = event.get("conclusion", [])


    return player_state, world_state

# --------------------------------------------------
# 游戏 Loop
# --------------------------------------------------
def main():
    print("欢迎来到无限流文字游戏 DEMO！")
    print(f"你进入了世界：{world_state['name']}")

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
            print("奖励：", event.get("rewards"))
            print("后果：", event.get("consequences"))

        except Exception as e:
            print("❌ JSON 解析失败：", e)
            print("原文：", event_text)


if __name__ == "__main__":
    main()
