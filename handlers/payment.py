import os
import asyncio
from aiogram.types.callback_query import CallbackQuery
from aiogram.types import Message
from aiogram import F, Bot, Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InputMediaPhoto
from database.orm_query import orm_get_user_carts
from handlers.menu_processing import del_update_cart
from utils.paginator import Paginator

payment_router = Router()
PAYMENTS_TOKEN = os.getenv("PAYMENTS_TOKEN_API")
PRICE = types.LabeledPrice(label='Item1', amount=4200000)

@payment_router.callback_query(F.data.startswith("www"))
async def buy_process(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    await callback.answer()
    card = await orm_get_user_carts(session, callback.message.chat.id)

    product_names = []
    product_description = []
    product_prices = []
    quantities = []

    for cart_item in card:
        product_names.append(cart_item.product.name)
        product_description.append(cart_item.product.description)
        product_prices.append(cart_item.product.price)
        quantities.append(cart_item.quantity)


    paginator = Paginator(card, page=1)

    cart = paginator.get_page()[0]
    cart_price = round(cart.quantity * cart.product.price, 2)
    total_price = round(
        sum(cart.quantity * cart.product.price for cart in card), 2
    )
    print(total_price)
    image = InputMediaPhoto(
        media=cart.product.image,
        caption=f"<strong>{cart.product.name}</strong>\n{cart.product.price}$ x {cart.quantity} = {cart_price}$\
                \nТовар {paginator.page} из {paginator.pages} в корзине.\nОбщая стоимость товаров в корзине {total_price}",
    )
    # return print(f"{image.media, image.caption}")
    if PAYMENTS_TOKEN.split(':')[1] == 'TEST':
        await bot.send_invoice(chat_id=callback.message.chat.id,
                            title=product_names[0],
                            description= product_description[0],
                            provider_token=PAYMENTS_TOKEN,
                            currency='UAH',
                            photo_url= 'https://cdn.bulbapp.io/frontend/images/c1e46c0b-c5e0-49d0-b4a1-eadea1a527da/1',
                            photo_width=416,
                            photo_height=234,
                            photo_size=416,
                            need_email=False,
                            prices= [types.LabeledPrice(label=f"*"*15, amount=total_price * 100)],
                            start_parameter='one-month-subscription',
                            payload='test-invoice-payload'
                            )


@payment_router.pre_checkout_query(lambda query: True)
async def pre_checkout_process(pre_checkout: types.PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout.id, ok=True)

@payment_router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot, session: AsyncSession):
    await asyncio.sleep(1)
    await bot.send_message(message.chat.id, '👍')
    await del_update_cart(session, message.chat.id)
