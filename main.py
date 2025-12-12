import json
from google import genai
from google.genai import types
from GameStateManager import GameStateManager

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
        "property_change": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
        "object_change": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
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
        {"名字": "火焰法球", "介绍": "造成中等火焰伤害"},
        {"名字": "隐匿术", "介绍": "提高潜行成功率"}
    ],
    "装备": [],
    "物品": [{"名字": "牛肉", "介绍": "一块可以用来吃的牛肉"},]
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
    8. 对于任何物品的获取或者失去，请使用以下格式：“获得物品：某个物品“或 “失去物品：某个物品”
    9. 对于任何能力的获取或者失去，请使用以下格式：“获得能力：某个能力”或“失去能力：某个能力”
    
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
# 游戏 Loop
# --------------------------------------------------
def main():
    print("欢迎来到无限流文字游戏 DEMO！")
    print(f"你进入了世界：{world_state['世界名字']}")
    manager = GameStateManager(player_state, world_state)

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
            manager.apply_change(event)

            print("\n判定结果：", event["outcome"])
            print("叙述：", event["description"])
            print("属性变化：", event.get("property_change"))
            print("物品或能力变化", event.get("object_change"))
            print("----------------------------------------")
            print(player_state)
            print("----------------------------------------")

        except Exception as e:
            print("❌ JSON 解析失败：", e)
            print("原文：", event_text)


if __name__ == "__main__":
    main()
