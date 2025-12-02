import json
from google import genai
from google.genai import types

# ---------------------------
# 初始化 API 和 Client
# ---------------------------
API_KEY = "AIzaSyDAopqnOSxalLPjmRGnenka--8bHY9LlrE"
client = genai.Client(api_key=API_KEY)

# 定义强制的 JSON 输出结构 (Schema)
event_schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "outcome": types.Schema(type=types.Type.STRING,
                                description="判定结果：crit (大成功), success (成功), partial (部分成功), failure (失败), fumble (大失败)"),
        "description": types.Schema(type=types.Type.STRING, description="事件的完整叙事描述"),
        "rewards": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING),
                                description="行动成功获得的奖励列表（如经验，道具，状态）"),
        "consequences": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING),
                                     description="行动失败或部分成功导致的后果列表（如伤害，状态变化）")
    },
    required=["outcome", "description"]
)

# ---------------------------
# 玩家初始状态
# ---------------------------
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

# ---------------------------
# 简单世界状态
# ---------------------------
world_state = {
    "name": "废墟魔都",
    "world_type": "魔法",
    "danger_level": 3,
    "magic_density": 10
}

# ---------------------------
# 构造 AI Prompt
# ---------------------------
def generate_prompt(player_state, world_state, player_action):
    # Prompt 不再需要要求返回 JSON，只需清晰地给出指令即可
    prompt = f"""
你是一个无限流文字游戏的系统仲裁者（System Arbiter）。
你的职责是：根据玩家状态、世界规则和玩家的行动，模拟一个骰子判定，并生成一个公正的事件结果。
请严格遵守以下核心规则：
1. **世界兼容系统**：此世界魔力浓度为 {world_state['magic_density']}。魔法技能（如火焰法球，适配度 1.0）应得到全效发挥。
2. **AI角色定位**：你只负责判定和叙事，**绝不**主动给出破局提示或改变玩家的行动目的。
3. **判定**：根据玩家的技能、世界状态和随机性，生成一个判定结果 (outcome)。

玩家状态：{json.dumps(player_state, ensure_ascii=False)}
世界状态：{json.dumps(world_state, ensure_ascii=False)}
玩家行动：{json.dumps(player_action, ensure_ascii=False)}

请基于这些信息，生成一个事件结果。
"""
    return prompt


# ---------------------------
# 调用 Gemini 生成事件 (修正后的函数)
# ---------------------------
def generate_event(client, prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # 使用快速高效的模型
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=3000,  # 适当增加 Max Tokens 以应对长叙事
                response_mime_type="application/json",  # 强制JSON输出
                response_schema=event_schema  # 强制JSON结构
            )
        )
        return response.text
    except Exception as e:
        return json.dumps(
            {"outcome": "system_failure", "description": f"API调用失败: {e}", "rewards": [], "consequences": []})


# ---------------------------
# 游戏循环
# ---------------------------
def main():
    print("欢迎来到无限流文字游戏 Demo！")
    print(f"你进入了世界：{world_state['name']}")

    # 玩家输入动作
    action_name = input("请输入动作名称（如 攻击 / 潜行 / 使用技能）: ")
    target = input("请输入目标（可留空）: ")
    used_ability = input("使用技能名称（可留空）: ")

    player_action = {
        "action": action_name,
        "target": target or None,
        "used_ability": used_ability if used_ability else None
    }

    # 构造 prompt
    prompt = generate_prompt(player_state, world_state, player_action)

    # 调用 Gemini
    event_result_text = generate_event(client, prompt)  # 传入 client 对象

    print("\n--- AI 输出事件 ---")
    print(event_result_text)

    # 尝试解析 JSON
    try:
        event_result = json.loads(event_result_text)

        outcome_map = {"crit": "🌟 大成功！", "success": "✅ 成功！", "partial": "⚠️ 部分成功！", "failure": "❌ 失败！",
                       "fumble": "💀 大失败！"}
        print(f"\n判定结果：{outcome_map.get(event_result['outcome'], event_result['outcome'])}")

        print("事件叙述：", event_result.get("description"))
        print("获得奖励：", event_result.get("rewards"))
        print("后果：", event_result.get("consequences"))
    except json.JSONDecodeError:
        print("\n❌ 严重错误：无法解析 AI 输出。原始文本：", event_result_text)
    except Exception as e:
        print(f"\n❌ 发生其他错误: {e}")


if __name__ == "__main__":
    main()
