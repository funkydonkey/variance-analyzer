"""Тестирование variance analysis агента."""
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import os
from dotenv import load_dotenv
from ai.variance_agent import VarianceAnalyst, interactive_mode

load_dotenv(override=True)

async def main():
    print("="*60)
    print("🤖 Variance Analysis Agent - Demo")
    print("="*60)

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Ошибка: установи OPENAI_API_KEY в .env файле")
        print("Создай .env файл:")
        print("  echo 'OPENAI_API_KEY=your-key-here' > .env")
        return
    
    analyst = VarianceAnalyst("test_data.csv")

    questions = [
        "Какие счета имеют наибольшее отклонение?",
        "Покажи топ-3 отклонения по модулю",
        "Какая сводная статистика по данным?",
        "В каких периодах Revenue выше бюджета?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"❓ Вопрос {i}: {question}")
        print(f"\n{'='*60}")

        try:
            response = await analyst.chat(question)
            print(f"🤖 Ответ: {response}")
        except Exception as e:
            print(f"Ошибка: {str(e)}")

        print(f"\n{'='*60}")
        print("✨ Тестирование завершено!")

    print(f"\n Хочешь задать свой вопрос?")
    if input().lower() == 'y':
        # from ai.variance_agent import interactive_mode
        await interactive_mode("test_data.csv")
        
if __name__ == "__main__":
    asyncio.run(main())
