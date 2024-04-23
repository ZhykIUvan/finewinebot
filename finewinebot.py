import logging
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler
from telegram.ext import CommandHandler, ConversationHandler, ContextTypes
from telegram import ReplyKeyboardMarkup, \
    InlineKeyboardButton, InlineKeyboardMarkup, Update
import requests
from bs4 import BeautifulSoup

bot_token = '7076404083:AAFgozLDhCbZnZcy2vCLMqMAtzDBJI07RE0'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

reply_keyboard = [['/izbrannoe'], ['/help']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False, resize_keyboard=True)

res_poisk_po_ingredientu_d = {}


def pars():
    url = 'https://ru.inshaker.com/collections/150-alkogolnye-kokteyli?page=60'
    response = requests.get(url)

    def getting_string(s):
        res = []
        for ing in s:
            res.append(ing.text.strip())

        return res

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        drinks = soup.find_all('div', class_='cocktail-item')
        res = {}

        for drink in drinks:
            name = drink.find('div', class_='cocktail-item-name').text.strip().lower().capitalize()
            ingredients = drink.find_all('div', class_='cocktail-item-good-name')

            res[name] = getting_string(ingredients)
        return res
    else:
        return 'Ошибка при получении страницы'


def pars_links():
    url = 'https://ru.inshaker.com/collections/150-alkogolnye-kokteyli?page=60'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        drinks = soup.find_all('div', class_='cocktail-item')
        res = {}

        for drink in drinks:
            name = drink.find('div', class_='cocktail-item-name').text.strip().lower().capitalize()
            link = 'https://ru.inshaker.com' + drink.find('a', class_='cocktail-item-preview').get('href')
            image_link = 'https://ru.inshaker.com' + drink.find('img', class_='cocktail-item-image').get('src')

            res[name] = (link, image_link)
        return res
    else:
        return 'Ошибка при получении страницы'


def pars_links_dop(link):
    url = link
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        steps = soup.find_all('ul', class_="steps")
        res = []

        for step in steps:
            pre_res = step.find_all('li')
            for i in pre_res:
                res.append(i.text + '.')
        return res
    else:
        return 'Ошибка при получении страницы'


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я бармен-бот! Я могу помочь с приготовлением напитка, который вам по душе). "
        rf"Используйте команду 'поиск по названию напитка', "
        rf"'поиск по ингридиенту' или 'поиск рецепта напитка' чтобы начать диалог"
        rf"", reply_markup=markup)


async def help_command(update, context):
    await update.message.reply_text("Чтобы посмотреть, что я умею, достаточно нажать на кнопочку меню и прочитать "
                                    "описания команд.\n\nБот сделан при помощи сайта https://ru.inshaker.com")


async def poisk_po_ingredientu(update, context):
    await update.message.reply_text("Введите ингредиент который должен быть в вашем напитке.")
    return 1


async def poisk_po_ingredientu_2_vop(update, context):
    global res_poisk_po_ingredientu_d
    res_poisk_po_ingredientu_d['fisrt_ing'] = update.message.text
    await update.message.reply_text("Ага, а теперь второй ингредиент.")
    return 2


async def res_poisk_po_ingredientu(update, context):
    global res_poisk_po_ingredientu_d
    res_poisk_po_ingredientu_d['second_ing'] = update.message.text
    spis = pars()
    res_nap = []

    for nap, ings in spis.items():
        if res_poisk_po_ingredientu_d["fisrt_ing"].lower().capitalize() in ings:
            if res_poisk_po_ingredientu_d["second_ing"].lower().capitalize() in ings:
                res_nap.append(nap)

    if len(res_nap) != 0:
        await update.message.reply_text(f'Вам могут подойти:')
        for nap in res_nap:
            await update.message.reply_text(f'{nap}\n\n'
                                            f'Полный список ингредиентов:\n\n'
                                            f'{", ".join(spis[nap])}')
        await update.message.reply_text(f'Выдача напитков окончена')
    else:
        await update.message.reply_text(f'Простите, я не нашел напиток с таким набором ингредиентов')
    res_poisk_po_ingredientu_d.clear()
    print(res_poisk_po_ingredientu_d)
    return ConversationHandler.END


async def poisk_napitka(update, context):
    await update.message.reply_text("Введите полное название напитка.")
    return 1


async def res_poisk_napitka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spis = pars()
    nap = update.message.text.lower().capitalize()
    keyboard = [
        [InlineKeyboardButton("Добавить в избранное", callback_data=f"{nap}")]
    ]

    reply_markup_2 = InlineKeyboardMarkup(keyboard)
    n = '\n'
    if nap in spis.keys():
        await update.message.reply_text(f"Вот список ингредиентов для {nap}:\n\n"
                                        f"{f'{n}'.join(spis[nap])}", reply_markup=reply_markup_2)
    else:
        await update.message.reply_text(f'Простите, я не нашел такой напиток.')
    return ConversationHandler.END


async def dob_v_izb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data[-1] == 'd':
        if query.data[:-1] in context.user_data.keys():
            context.user_data.pop(query.data[:-1])
            await query.edit_message_text(text=f"Напиток {query.data[:-1]} убран из избранных.")
        else:
            await query.edit_message_text(text=f"Напиток {query.data[:-1]} уже убран из избранных.")

    elif query.data == 'no':
        await query.edit_message_text(text=f"Ничего не изменилось.")

    elif query.data.lower().capitalize() == 'Del':
        keyboard = [
            [InlineKeyboardButton("Не удалять", callback_data=f"no")]
        ]

        for nap in context.user_data.keys():
            keyboard.append([InlineKeyboardButton(f"{nap}", callback_data=f"{nap}d")])

        reply_markup_1 = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text=f"Вы точно хотите удалить напиток из избранного?",
                                      reply_markup=reply_markup_1)
        query.data = ''
    else:
        if query.data.lower().capitalize() in context.user_data.keys():
            await query.edit_message_text(text=f"Вы уже добавили напиток {query.data.lower().capitalize()}"
                                               f" в избранное.")
        else:
            context.user_data[query.data.lower().capitalize()] = query.data.lower().capitalize()
            await query.edit_message_text(text=f"Напиток {query.data.lower().capitalize()} добавлен в избранное.")
        query.data = ''


async def poisk_recepta(update, context):
    await update.message.reply_text("Введите полное название напитка.")
    return 1


async def res_poisk_recepta(update, context):
    spis = pars_links()
    nap = update.message.text.lower().capitalize()
    user_id = update.message.from_user.id
    n = '\n'
    if nap in spis.keys():
        res = pars_links_dop(spis[nap][0])
        for i in range(len(res)):
            res[i] = f'{i + 1}. {res[i]}'
        msg = f'Подробный рецепт к напитку {nap}:\n\n' \
              f'{f"{n}".join(res)}'
        requests.get(f'https://api.telegram.org/bot{bot_token}/sendPhoto?chat_id='
                     f'{user_id}&caption={msg}&photo={spis[nap][1]}')
    else:
        await update.message.reply_text(f'Простите, я не нашел такой напиток.')
    return ConversationHandler.END


async def izbrannoe(update, context):
    res = ''
    keyboard = [
        [InlineKeyboardButton("Удалить из избранного", callback_data=f"DEL")]
    ]

    reply_markup_1 = InlineKeyboardMarkup(keyboard)
    if context.user_data != {}:
        for nap in context.user_data.keys():
            res += f'\n{nap}'
        await update.message.reply_text(f"Избранные напитки:\n{res}", reply_markup=reply_markup_1)
    else:
        await update.message.reply_text(f"Вы еще не добавили никакой напиток.")


async def stop(update, context):
    await update.message.reply_text("Все процессы остановлены")
    context.user_data.clear()
    return ConversationHandler.END


def main():
    application = Application.builder().token(bot_token).build()

    conv_handler_ing = ConversationHandler(
        entry_points=[CommandHandler('poisk_po_ingredientu', poisk_po_ingredientu)],

        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, poisk_po_ingredientu_2_vop)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, res_poisk_po_ingredientu)]
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    conv_handler_nap = ConversationHandler(
        entry_points=[CommandHandler('poisk_napitka', poisk_napitka)],

        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, res_poisk_napitka)],
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    conv_handler_recipe = ConversationHandler(
        entry_points=[CommandHandler('poisk_recepta', poisk_recepta)],

        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, res_poisk_recepta)],
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    text_handler = MessageHandler(filters.TEXT, start)

    application.add_handler(conv_handler_ing)
    application.add_handler(conv_handler_nap)
    application.add_handler(conv_handler_recipe)
    application.add_handler(CallbackQueryHandler(dob_v_izb))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("izbrannoe", izbrannoe))
    application.add_handler(text_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
