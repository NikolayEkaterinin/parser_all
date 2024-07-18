from telethon import TelegramClient, functions
import pandas as pd

# Введите сюда свои api_id и api_hash
api_id = '23873540'
api_hash = '67a55477f07ab105fc6f69d1541cc91e'
phone_number = '+79201221648'

# Создаем клиент Telegram
client = TelegramClient('session_name', api_id, api_hash)


async def main():
    # Аутентификация
    await client.start(phone=phone_number)
    print("Client Created and Authenticated")

    # Введите ключевые слова для поиска групп
    keywords = ["Business", "Investment", "Google", "Facebook", "Partners", "Affiliate Marketing",
                "Digital Marketing", "Marketing", "Investors", "Startups", "Business Partnership"]

    groups_info = []

    for keyword in keywords:
        result = await client(functions.contacts.SearchRequest(
            q=keyword,
            limit=50
        ))

        for chat in result.chats:
            if hasattr(chat, 'participants_count') and chat.megagroup and chat.participants_count >= 500:
                messages = await client.get_messages(chat, limit=100)
                if messages:
                    recent_activity = messages[0].date

                    # Фильтрация по критериям
                    if "crypto" not in chat.title.lower() and "binary" not in chat.title.lower():
                        last_month_msgs = [msg for msg in messages if msg.date and (
                            pd.Timestamp.now(tz='UTC') - pd.Timestamp(msg.date)).days <= 30]
                        english_msgs = [msg for msg in last_month_msgs if msg.message and sum(
                            1 for char in msg.message if char.isascii()) / len(msg.message) > 0.8]

                        if len(last_month_msgs) > 0 and len(english_msgs) / len(last_month_msgs) > 0.8:
                            try:
                                invite_link = await client(functions.messages.ExportChatInviteRequest(
                                    peer=chat.id
                                ))
                                invite_link = invite_link.link if invite_link else None
                            except:
                                invite_link = None

                            group_info = {
                                'title': chat.title,
                                'id': chat.id,
                                'participants': chat.participants_count,
                                'recent_activity': recent_activity,
                                'invite_link': invite_link
                            }
                            groups_info.append(group_info)

    # Сохранение данных в CSV
    df = pd.DataFrame(groups_info)
    df.to_csv('telegram_groups.csv', index=False)

with client:
    client.loop.run_until_complete(main())
