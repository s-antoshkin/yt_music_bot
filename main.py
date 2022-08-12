import os
import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv

import exceptions
import files_actions

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

# logging.basicConfig(
#     format="%(asctime)s - %(levelname)s - %(message)s", level=logging.DEBUG
# )

logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class FMSCount(StatesGroup):
    count = State()


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("cancel", "Отмена ввода колличества песен"),
    ])


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    await message.answer(
        md.text(
            md.text(md.hbold("Бот для прослушивания музыки с YTMusic.")) + "\n",
            md.text(md.text("Ссылка на песню (видео) - "), md.hunderline("одна песня;")),
            md.text(
                md.text("Ссылка на плейлист - плейлист на указанное количество песен, "), md.hunderline("без догрузки!")
            ) + "\n",
            md.text("Плейлисты - только реальные (свои, чужие), без 'радио', без 'реомендованных' плейлистов!"),
            sep="\n"
        ), parse_mode="HTML"
    )


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message, state):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply('ОК')


@dp.message_handler(lambda message: not message.html_text.isdigit())
async def check_link(message, state='*'):
    files_actions.delete_songs(message.from_user.id)
    await FMSCount.count.set()
    await FMSCount.next()
    try:
        songs_count = files_actions.songs_count(message.html_text)
    except exceptions.NotCorrectMessage as e:
        await message.answer(str(e))
        return   
    await state.update_data(link=str(message.html_text))   
    await state.update_data(song_all=int(songs_count)) 
    if songs_count > 1:
        await FMSCount.next()
        await message.answer(
            f'Количество песен в плейлисте (ориентировочно) - {songs_count}\n'
            'Сколько грузим?(числом или /cancel (или "отмена"))',
            )
    else:
        await send_music(message.from_user.id, message.html_text, state)


@dp.message_handler(lambda message: message.text.isdigit(), state=FMSCount.count)
async def check_count(message, state):
    await state.update_data(count=int(message.text))
    await message.reply('Ща всё будет!')
    async with state.proxy() as data:
        await send_music(message.from_user.id, data['link'], state, data['count'])


async def send_music(chat_id, link, state, count=0):
    files = files_actions.create_song_list(chat_id, link, count) 
    try:
        if files != None:
            for sound_pack in files:
                await bot.send_media_group(chat_id, media=sound_pack)
        else:
            await bot.send_message(chat_id, 'Кривой плейлист! Читай описание! (/help)')
    except exceptions.SendMessageError as e:
        await bot.send_message(chat_id, str(e))   
    files_actions.delete_songs(chat_id) 
    await state.finish()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
