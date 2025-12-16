import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

# ================= CONFIG =================
BOT_TOKEN = "5129418991:AAGUWNQXed4qbzKFKiYGZCRofOAziMPx8b4"
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
MEDIA_URL = "http://127.0.0.1:8000"  # media fayllar uchun
ORDER_GROUP_ID = -1002052739892
# =========================================

logging.basicConfig(level=logging.INFO)

# ================= FSM =================
class OrderState(StatesGroup):
    quantity = State()
    name = State()
    phone = State()
    location = State()
# ======================================

# ================= HELPERS =================
async def get_products():
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE_URL}/products/") as resp:
            return await resp.json()


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Mahsulotlar")],
            [KeyboardButton(text="🛒 Savatcha")]
        ],
        resize_keyboard=True
    )
# ===========================================

# ================= START =================
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(cart=[])
    await message.answer(
        "Assalomu alaykum 👋\nMahsulotlarni tanlang:",
        reply_markup=main_menu()
    )
# ========================================

# ================= PRODUCTS =================
async def show_products(message: Message):
    products = await get_products()

    async with aiohttp.ClientSession() as session:
        for product in products:
            # Agar product['image'] allaqachon to'liq URL bo'lsa, MEDIA_URL qo'shmaymiz
            image_url = product["image"]

            async with session.get(image_url) as resp:
                image_bytes = await resp.read()

            photo = BufferedInputFile(image_bytes, filename="product.jpg")

            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="➕ Savatga qo‘shish",
                        callback_data=f"add_{product['id']}"
                    )]
                ]
            )

            await message.answer_photo(
                photo=photo,
                caption=f"📦 {product['name']}\n💰 {product['price']} so‘m",
                reply_markup=kb
            )
# ==========================================

# ================= ADD TO CART =================
async def add_to_cart(call: CallbackQuery, state: FSMContext):
    product_id = int(call.data.split("_")[1])

    products = await get_products()
    product = next(p for p in products if p["id"] == product_id)

    # selected_product ni saqlaymiz
    await state.update_data(selected_product=product)

    await call.message.answer("Nechta dona olasiz?")
    await state.set_state(OrderState.quantity)
    await call.answer()
# ==============================================


# ================= QUANTITY =================
async def set_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Faqat son kiriting!")

    quantity = int(message.text)
    data = await state.get_data()

    cart = data.get("cart", [])
    product = data.get("selected_product")

    if not product:
        return await message.answer("Xatolik yuz berdi, qayta boshlang /start")

    # Cartga qo'shamiz
    cart.append({
        "product": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "price": product["price"] * quantity
    })

    # Cartni saqlaymiz, selected_product ni o'chiramiz
    await state.update_data(cart=cart)
    await state.update_data(selected_product=None)

    await message.answer(
        "✅ Savatga qo‘shildi",
        reply_markup=main_menu()
    )

    # holatni boshlang'ichga qaytaramiz
    await state.clear()
    await state.update_data(cart=cart)  # cartni yana qayta saqlaymiz
# ============================================


# ================= CART =================
async def show_cart(message: Message, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", [])

    if not cart:
        return await message.answer("🛒 Savatcha bo‘sh")

    text = "🛒 Savatchangiz:\n\n"
    total = 0
    for item in cart:
        text += f"• {item['product_name']} x{item['quantity']} = {item['price']} so‘m\n"
        total += item["price"]
    text += f"\n💰 Jami: {total} so‘m"

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Buyurtma berish")],
            [KeyboardButton(text="⬅️ Ortga")]
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=kb)
# =======================================

# ================= ORDER FLOW =================
async def order_start(message: Message, state: FSMContext):
    await message.answer("Ismingizni kiriting:")
    await state.set_state(OrderState.name)

async def get_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Telefon raqamingizni kiriting:")
    await state.set_state(OrderState.phone)

async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Lokatsiya yuborish", request_location=True)]],
        resize_keyboard=True
    )
    await message.answer("Yetkazib berish manzilini yuboring:", reply_markup=kb)
    await state.set_state(OrderState.location)
# =============================================

# ================= FINISH =================
async def finish_order(message: Message, state: FSMContext):
    data = await state.get_data()
    cart = data["cart"]
    total_price = sum(item["price"] for item in cart)

    payload = {
        "full_name": data["full_name"],
        "phone": data["phone"],
        "latitude": message.location.latitude,
        "longitude": message.location.longitude,
        "total_price": total_price,
        "items": [
            {"product": item["product"], "quantity": item["quantity"], "price": item["price"]}
            for item in cart
        ]
    }

    async with aiohttp.ClientSession() as session:
        await session.post(f"{API_BASE_URL}/orders/", json=payload)

    # Telegram groupga yuborish
    text = f"🆕 YANGI BUYURTMA\n\n👤 {data['full_name']}\n📞 {data['phone']}\n\n"
    for item in cart:
        text += f"• {item['product_name']} x{item['quantity']} = {item['price']} so‘m\n"
    text += f"\n💰 Jami: {total_price} so‘m"

    await message.bot.send_message(ORDER_GROUP_ID, text)
    await message.bot.send_location(ORDER_GROUP_ID,
                                    message.location.latitude,
                                    message.location.longitude)

    await message.answer("✅ Buyurtma qabul qilindi!\nTez orada yetkazib beramiz 🚚",
                         reply_markup=main_menu())
    await state.clear()
# ============================================

# ================= BACK =================
async def back(message: Message):
    await message.answer("Asosiy menyu", reply_markup=main_menu())
# ======================================

# ================= MAIN =================
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(start_handler, F.text == "/start")
    dp.message.register(show_products, F.text == "🛍 Mahsulotlar")
    dp.callback_query.register(add_to_cart, F.data.startswith("add_"))
    dp.message.register(set_quantity, OrderState.quantity)
    dp.message.register(show_cart, F.text == "🛒 Savatcha")
    dp.message.register(order_start, F.text == "✅ Buyurtma berish")
    dp.message.register(get_name, OrderState.name)
    dp.message.register(get_phone, OrderState.phone)
    dp.message.register(finish_order, F.location, OrderState.location)
    dp.message.register(back, F.text == "⬅️ Ortga")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
