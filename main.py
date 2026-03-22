import json
from GameStateManager import GameStateManager
from SaveLoad import SaveLoad
from Prompt import Prompt

# --------------------------------------------------
# 游戏主要逻辑
# --------------------------------------------------
def main():
    print("欢迎来到无限流文字游戏 DEMO！")
    selected_task = None

    archive_manager = SaveLoad("game.json")
    game_state = archive_manager.load()

    player_state = game_state["player_state"]
    world_state = game_state["world_state"]
    task_state = game_state["task_state"]
    event_state = game_state["event_state"]

    for turns in range(3):
        manager = GameStateManager(player_state, world_state, task_state, event_state)

        if selected_task:
            player_action = {
                "action": "选择任务",
                "task_data": selected_task
            }
            selected_task = None
        else:
            action_name = input("\n请输入动作名称（如 攻击 / 潜行 / 使用技能）: ")
            target = input("目标（可空）: ")
            used_ability = input("使用技能（可空）: ")

            player_action = {
                "action": action_name,
                "target": target or None,
                "used_ability": used_ability or None
            }
        prompt_manager = Prompt(player_state, world_state, task_state, event_state, player_action)

        print("\n--- AI 事件判定 ---")

        event_text = prompt_manager.generate_event()
        print(event_text)

        # 解析 JSON
        try:
            event = json.loads(event_text)

            if isinstance(event, str):
                event = json.loads(event)

            manager.apply_change(event)
            print("\n当前回合的结果：", event)

            # 任务选择逻辑
            if event.get("task_options"):
                print("可选任务：")
                for i, t in enumerate(event["task_options"]):
                    print(f"{i + 1}. {t['task']} - {t['description']} - {t['reward']}")

                choice = int(input("请选择任务编号: "))
                selected_task = event["task_options"][choice - 1]

            #技能消耗逻辑
            ability_use = event.get("ability_use")
            if ability_use:
                for ability_used in ability_use:
                    result = manager.apply_ability(ability_used.get("ability_name"))

                    if "error" in result:
                        print("技能使用失败:", result["error"])
                        continue

        except Exception as e:
            print("❌ JSON 解析失败：", e)
            print("原文：", event_text)

    archive_manager.save(game_state, player_state, world_state, task_state, event_state)

if __name__ == "__main__":
    main()
