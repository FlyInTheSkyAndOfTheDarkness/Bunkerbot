import telebot
from telebot import types
import random
import threading
from collections import defaultdict

# Создаем бота
bot = telebot.TeleBot('7897964631:AAFvNdfxnCZQvnOnTzjH1A7SKos0FXkXJzo')

# Храним данные о текущей игре
games = {}

# Карты для игры "Бункер"
cards = {
    "Возраст": ["20 лет", "25 лет", "30 лет", "35 лет", "40 лет", "45 лет", "50 лет", "60 лет", "70 лет", "80 лет"],
    "Профессия": ["Инженер", "Врач", "Учитель", "Архитектор", "Программист", "Повар", "Художник", "Механик", "Полицейский", "Ученый"],
    "Здоровье": ["Полностью здоров", "Слабое зрение", "Аллергия", "Инвалидность", "Сахарный диабет", "Проблемы с сердцем", "Астма", "Без хронических болезней", "Больной гриппом", "Перенес операцию"],
    "Хобби": ["Путешествия", "Чтение", "Рисование", "Спорт", "Игра на гитаре", "Шахматы", "Кулинария", "Танцы", "Компьютерные игры", "Садоводство"],
    "Фобия": ["Боязнь высоты", "Клаустрофобия", "Страх темноты", "Аэрофобия", "Агорафобия", "Страх змей", "Боязнь воды", "Страх пауков", "Боязнь огня", "Страх толпы"],
    "Навыки": ["Готовить пищу", "Чинить технику", "Оказывать первую помощь", "Плавать", "Выживание в дикой природе", "Строительство", "Программирование", "Знание иностранных языков", "Навыки лидерства", "Умение скрываться"],
    "Имущество": ["Палатка", "Аптечка", "Канистра воды", "Охотничий нож", "Теплая одежда", "Солнечные батареи", "Радиопередатчик", "Пачка консервов", "Спальный мешок", "Карта местности"]
}

# Команда /start
@bot.message_handler(commands=['start'])
def start_game(message):
    chat_id = message.chat.id
    games[chat_id] = {
        "players": [],
        "roles": {},
        "started": False,
        "current_round": 0,
        "votes": defaultdict(int),
        "message_counts": defaultdict(int)  # Ограничение на сообщения
    }
    bot.send_message(chat_id, "Добро пожаловать в игру 'Бункер'! Добавьте участников с помощью команды /join. Когда все готовы, начните игру командой /begin.")

# Команда /join
@bot.message_handler(commands=['join'])
def join_game(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    game = games.get(chat_id)

    if not game:
        bot.send_message(chat_id, "Сначала начните игру командой /start.")
        return

    if user_id in game["players"]:
        bot.send_message(chat_id, f"{username}, вы уже присоединились к игре.")
    else:
        game["players"].append(user_id)
        bot.send_message(chat_id, f"{username} присоединился к игре!")

# Команда /begin
@bot.message_handler(commands=['begin'])
def begin_game(message):
    chat_id = message.chat.id
    game = games.get(chat_id)

    if not game:
        bot.send_message(chat_id, "Сначала начните игру командой /start.")
        return

    if len(game["players"]) < 2:
        bot.send_message(chat_id, "Для начала игры нужно как минимум 2 игрока.")
        return

    game["started"] = True
    bot.send_message(chat_id, "Игра началась! Все получают свои характеристики.")
    
    for player in game["players"]:
        player_cards = generate_unique_cards()
        game["roles"][player] = player_cards
        cards_text = "\n".join([f"{key}: {value}" for key, value in player_cards.items()])
        bot.send_message(player, f"Ваши характеристики:\n{cards_text}")
    
    start_round(chat_id)

# Генерация уникальных карт
def generate_unique_cards():
    player_cards = {}
    for category, options in cards.items():
        player_cards[category] = random.choice(options)
    return player_cards

# Начало раунда
def start_round(chat_id):
    game = games.get(chat_id)
    if not game or not game["started"]:
        return
    
    current_round = game["current_round"]
    categories = list(cards.keys())

    if current_round >= len(categories):
        bot.send_message(chat_id, "Игра окончена! Спасибо за участие!")
        games.pop(chat_id, None)
        return

    category = categories[current_round]
    bot.send_message(chat_id, f"Раунд {current_round + 1}. Открыта карта: {"Профессия"}")
    
    # Таймер обсуждения
    discussion_time = 60 if current_round == 0 else 180
    threading.Timer(discussion_time, end_discussion, args=[chat_id, category]).start()
    bot.send_message(chat_id, f"У вас есть {discussion_time // 60} минут(ы) на обсуждение!")

# Ограничение на сообщения
@bot.message_handler(func=lambda message: True)
def limit_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    game = games.get(chat_id)

    if not game or not game["started"]:
        return

    # Ограничение на длину сообщения
    if len(message.text) > 200:
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, f"{message.from_user.first_name}, сообщение слишком длинное! Максимум 200 символов.")
        return

    # Ограничение на количество сообщений
    game["message_counts"][user_id] += 1
    if game["message_counts"][user_id] > 5:
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, f"{message.from_user.first_name}, вы превысили лимит сообщений (5 за раунд).")
        return

# Завершение обсуждения
def end_discussion(chat_id, category):
    bot.send_message(chat_id, f"Время обсуждения вышло! Переходим к голосованию за исключение.")
    start_voting(chat_id, category)

# Начало голосования
def start_voting(chat_id, category):
    game = games.get(chat_id)
    if not game:
        return

    players = game["players"]
    markup = types.InlineKeyboardMarkup()

    for player_first_name in players:
        player_name = f"Игрок {player_first_name}"
        markup.add(types.InlineKeyboardButton(text=player_name, callback_data=f"vote_{player_first_name}"))
    
    bot.send_message(chat_id, "Голосуйте за игрока, которого хотите исключить:", reply_markup=markup)

# Обработка голосов
@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def handle_vote(call):
    chat_id = call.message.chat.id
    voter_id = call.from_user.id
    game = games.get(chat_id)

    if not game or voter_id not in game["players"]:
        return

    voted_id = int(call.data.split("_")[1])
    game["votes"][voted_id] += 1
    bot.send_message(chat_id, f"{call.from_user.first_name} проголосовал!")

# Завершение голосования
def end_voting(chat_id):
    game = games.get(chat_id)
    if not game:
        return

    if game["votes"]:
        loser = max(game["votes"], key=game["votes"].get)
        bot.send_message(chat_id, f"Игрок {loser} исключен!")
        game["players"].remove(loser)

    game["votes"].clear()
    game["message_counts"].clear()
    game["current_round"] += 1
    start_round(chat_id)

# Команда /reset
@bot.message_handler(commands=['reset'])
def reset_game(message):
    chat_id = message.chat.id
    if chat_id in games:
        del games[chat_id]
    bot.send_message(chat_id, "Игра сброшена. Начните новую игру командой /start.")

# Запуск бота
bot.polling(none_stop=True)

