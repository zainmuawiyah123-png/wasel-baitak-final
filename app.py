import base64
import os
import sqlite3
import time
import urllib.parse
import streamlit as st

st.set_page_config(
    page_title="بوابة الكرك للطلبات - Karak Gate", page_icon="🏰", layout="wide"
)

# ---------------------------------------------------------
# تصميم CSS المخصص والشاشة الترحيبية وتنبيهات الجرس الصوتية
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp { background-color: #F8F9FA; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right; }
    
    .splash-screen {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: linear-gradient(135deg, #FF6600 0%, #FF8533 100%);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 99999;
        color: white;
        text-align: center;
    }
    .splash-title {
        font-size: 52px;
        font-weight: 900;
        margin-bottom: 10px;
        letter-spacing: 2px;
        text-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .splash-subtitle {
        font-size: 24px;
        font-weight: 500;
        opacity: 0.95;
    }
    
    .hero-box {
        background: linear-gradient(135deg, #FF6600 0%, #FF8533 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(255, 102, 0, 0.3);
    }
    .hero-box h1 { font-size: 26px; font-weight: 800; margin: 0; }
    
    .cat-container {
        display: flex;
        gap: 12px;
        overflow-x: auto;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .cat-badge {
        background: linear-gradient(135deg, #FF6600 0%, #FF8533 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 25px;
        font-weight: 700;
        font-size: 15px;
        white-space: nowrap;
        box-shadow: 0 3px 8px rgba(255, 102, 0, 0.3);
        text-align: center;
    }
    .store-thumb {
        width: 90px;
        height: 90px;
        object-fit: cover;
        border-radius: 12px;
        border: 2px solid #E5E7EB;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .item-thumb {
        width: 60px;
        height: 60px;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
    }
    
    @keyframes ring {
      0% { transform: rotate(0); }
      10% { transform: rotate(15deg); }
      20% { transform: rotate(-15deg); }
      30% { transform: rotate(10deg); }
      40% { transform: rotate(-10deg); }
      50% { transform: rotate(5deg); }
      60% { transform: rotate(-5deg); }
      100% { transform: rotate(0); }
    }
    .bell-alert {
      display: inline-block;
      animation: ring 1.2s infinite ease-in-out;
      font-size: 24px;
      color: #FF6600;
    }
    </style>
""",
    unsafe_allow_html=True,
)

def play_sound_alert():
  sound_html = """
    <audio autoplay>
      <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
    </audio>
    """
  st.markdown(sound_html, unsafe_allow_html=True)

if "splash_shown" not in st.session_state:
  splash_placeholder = st.empty()
  splash_placeholder.markdown(
      """
        <div class="splash-screen">
            <div class="splash-title">🏰 بوابة الكرك للطلبات</div>
            <div class="splash-subtitle">Karak Gate</div>
            <p style="margin-top: 25px; font-size: 16px; opacity: 0.8;">جاري تحميل المنصة...</p>
        </div>
    """,
      unsafe_allow_html=True,
  )
  time.sleep(1.5)
  splash_placeholder.empty()
  st.session_state["splash_shown"] = True

if not os.path.exists("uploads"):
  os.makedirs("uploads")

def init_db():
  conn = sqlite3.connect("karak_talabat_secure.db", check_same_thread=False)
  c = conn.cursor()

  c.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            rating REAL DEFAULT 4.8,
            delivery_time TEXT,
            delivery_fee TEXT,
            image_url TEXT,
            offer TEXT,
            passcode TEXT DEFAULT '5678',
            lat REAL DEFAULT 31.1852,
            lon REAL DEFAULT 35.7048,
            phone TEXT DEFAULT '0797028819'
        )
    """)
  
  c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT,
            item_name TEXT,
            price REAL,
            discount TEXT,
            image_url TEXT
        )
    """)
  
  c.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT DEFAULT '0797028819',
            vehicle TEXT,
            passcode TEXT DEFAULT '1122',
            lat REAL DEFAULT 31.1800,
            lon REAL DEFAULT 35.7000
        )
    """)
  
  c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT,
            customer_name TEXT,
            phone TEXT,
            address TEXT,
            items_desc TEXT,
            payment_method TEXT,
            total_price REAL,
            status TEXT DEFAULT 'قيد المعالجة',
            cust_lat REAL DEFAULT 31.1850,
            cust_lon REAL DEFAULT 35.7050
        )
    """)
  
  c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
  c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_pass', '1234')")
  c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('store_pass', '5678')")
  c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('driver_pass', '1122')")

  conn.commit()
  return conn, c

conn, c = init_db()

def get_setting(key):
  c.execute("SELECT value FROM settings WHERE key = ?", (key,))
  row = c.fetchone()
  return row[0] if row else ""

if "main_nav" not in st.session_state:
  st.session_state["main_nav"] = "الرئيسية"

st.markdown("""
    <div class="hero-box">
        <h1>🏰 بوابة الكرك للطلبات - Karak Gate</h1>
        <p style="margin-top: 5px; font-size: 14px;">منصة التوصيل الأولى في محافظة الكرك</p>
    </div>
""", unsafe_allow_html=True)

col_1, col_2, col_3, col_4, col_5 = st.columns(5)
with col_1:
  if st.button("🏠 الرئيسية", use_container_width=True):
    st.session_state["main_nav"] = "الرئيسية"
    st.rerun()
with col_2:
  if st.button("🛍️ واجهة الزبائن", use_container_width=True):
    st.session_state["main_nav"] = "الزبائن"
    st.rerun()
with col_3:
  if st.button("🏪 واجهة المتاجر", use_container_width=True):
    st.session_state["main_nav"] = "المتاجر"
    st.rerun()
with col_4:
  if st.button("🛵 واجهة السائقين", use_container_width=True):
    st.session_state["main_nav"] = "السائقين"
    st.rerun()
with col_5:
  if st.button("⚙️ الإدارة المركزية", use_container_width=True):
    st.session_state["main_nav"] = "الإدارة"
    st.rerun()

st.markdown("---")

# =========================================================
# الرئيسية
# =========================================================
if st.session_state["main_nav"] == "الرئيسية":
  st.markdown("### 🌟 أهلاً بك في منصة الكرك للطلبات")
  search_query = st.text_input("🔍 بحث سريع عن مطعم، صنف، أو منتج...", "")

  st.markdown("---")
  st.markdown("### 📂 أقسام المتاجر والخدمات")
  st.markdown("""
        <div class="cat-container">
            <div class="cat-badge">🍔 مطاعم</div>
            <div class="cat-badge">🍰 حلويات</div>
            <div class="cat-badge">🥜 محامص ومكسرات</div>
            <div class="cat-badge">🛒 ماركت</div>
            <div class="cat-badge">🥬 خضروات وفواكه</div>
            <div class="cat-badge">💊 صيدليات ومستلزمات طبية</div>
        </div>
    """, unsafe_allow_html=True)

  st.markdown("---")
  st.markdown("### 🔥 عروض ومتاجر الكرك الحقيقية")
  c.execute("SELECT name, category, rating, delivery_time, offer, image_url FROM stores LIMIT 6")
  sample_stores = c.fetchall()
  
  if not sample_stores:
    st.info("لا توجد متاجر مضافة حالياً. قم بإضافة المتاجر والمحلات الحقيقية من 'واجهة المتاجر' أو 'الإدارة المركزية'.")
  else:
    cols = st.columns(3)
    for idx, st_sample in enumerate(sample_stores):
      s_name, s_cat, s_rating, s_time, s_offer, s_img = st_sample
      with cols[idx % 3]:
        img_tag = f'<img src="{s_img}" style="width:100%; height:120px; object-fit:cover; border-radius:8px; margin-bottom:10px;">' if s_img else '<div style="height:120px; background:#e5e7eb; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#6b7280; margin-bottom:10px;">لا توجد صورة</div>'
        st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; border:1px solid #E5E7EB; margin-bottom:15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                {img_tag}
                <h4 style="margin:0 0 5px 0; color:#1F2937;">{s_name}</h4>
                <p style="margin:0; font-size:13px; color:#6B7280;">التصنيف: {s_cat} | ⭐ {s_rating}</p>
                <p style="margin:5px 0 0 0; font-size:13px; color:#FF6600; font-weight:bold;">🏷️ العرض: {s_offer}</p>
                <p style="margin:5px 0 0 0; font-size:12px; color:#4B5563;">⏱ وقت التوصيل: {s_time}</p>
            </div>
        """, unsafe_allow_html=True)

# =========================================================
# 1. واجهة الزبائن
# =========================================================
elif st.session_state["main_nav"] == "الزبائن":
  st.subheader("🛍️ بوابة الزبائن الرئيسية")
  cust_t1, cust_t2, cust_t3, cust_t4 = st.tabs([
      "👤 بياناتك والموقع الجغرافي",
      "🏠 تصفح المتاجر والأصناف",
      "🛒 السلة والدفع",
      "📍 تتبع الطلب والرحلة",
  ])

  with cust_t1:
    with st.form("cust_form_auto"):
      c_name = st.text_input("الاسم الكامل:")
      c_phone = st.text_input("رقم الهاتف:")
      c_address = st.text_area("العنوان بالتفصيل (مثل: الكرك، المرج):")
      c_lat = st.number_input("خط العرض (Latitude):", value=31.1852, format="%.6f")
      c_lon = st.number_input("خط الطول (Longitude):", value=35.7048, format="%.6f")
      if st.form_submit_button("حفظ بياناتي وموقعي"):
        st.session_state["client_info"] = {
            "name": c_name,
            "phone": c_phone,
            "address": c_address,
            "lat": c_lat,
            "lon": c_lon,
        }
        st.success("تم حفظ بياناتك وموقعك الجغرافي بنجاح!")

  with cust_t2:
    st.markdown("### 🏠 المتاجر وموقعها على الخريطة")
    c.execute("SELECT * FROM stores")
    stores = c.fetchall()
    if not stores:
      st.info("لا توجد متاجر مسجلة حالياً. يرجى إدخال المتاجر الحقيقية من واجهة المتاجر.")
    for store in stores:
      s_id, s_name, s_cat, s_rating, s_time, s_fee, s_img, s_offer, s_pass, s_lat, s_lon, s_phone_db = store
      col_img, col_det = st.columns([1, 5])
      with col_img:
        if s_img:
          st.markdown(f'<img src="{s_img}" class="store-thumb">', unsafe_allow_html=True)
        else:
          st.markdown('<div style="width:90px; height:90px; background:#e5e7eb; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:12px; color:#6b7280;">بدون صورة</div>', unsafe_allow_html=True)
      with col_det:
        st.markdown(f"#### {s_name} &nbsp;&nbsp;<span style='background:#FEF3C7;color:#D97706;padding:2px 8px;border-radius:6px;font-size:14px;'>⭐ {s_rating}</span>", unsafe_allow_html=True)
        st.write(f"التصنيف: {s_cat} | ⏱️ {s_time} | 🚚 {s_fee} | 📍 [خريطة المتجر](https://maps.google.com/?q={s_lat},{s_lon})")
        st.markdown(f"<span style='color:#FF6600;'>🏷️ {s_offer}</span>", unsafe_allow_html=True)

      with st.expander(f"📦 عرض أصناف وعروض {s_name}"):
        c.execute("SELECT id, item_name, price, discount, image_url FROM items WHERE store_name = ?", (s_name,))
        items = c.fetchall()
        if not items:
          st.info("لا توجد أصناف مضافة لهذا المتجر بعد.")
        for itm in items:
          i_id, i_name, i_price, i_disc, i_img = itm
          col_i_img, col_it1, col_it2 = st.columns([1, 3, 1])
          with col_i_img:
            if i_img:
              st.markdown(f'<img src="{i_img}" class="item-thumb">', unsafe_allow_html=True)
            else:
              st.markdown('<div style="width:60px; height:60px; background:#e5e7eb; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:10px; color:#6b7280;">بدون صورة</div>', unsafe_allow_html=True)
          with col_it1:
            st.write(f"• **{i_name}**\n- السعر: **{i_price} JD**\n- العرض: {i_disc}")
          with col_it2:
            if st.button("➕ إضافة", key=f"add_c_{s_id}_{i_id}_{s_name}"):
              st.session_state["cart_item"] = f"{s_name} - {i_name} ({i_price} JD)"
              st.session_state["cart_store"] = s_name
              st.session_state["cart_item_price"] = i_price
              st.success("تمت الإضافة للسلة!")
          st.markdown("---")
      st.markdown("---")

  with cust_t3:
    st.markdown("### 🛒 السلة وفاتورة الطلب التفصيلية")
    chosen_item = st.session_state.get("cart_item", "لم يتم اختيار أي صنف بعد")
    chosen_store = st.session_state.get("cart_store", "")
    item_price = st.session_state.get("cart_item_price", 0.0)

    st.write(f"الطلب الحالي: **{chosen_item}**")

    delivery_fee_val = 0.75
    if chosen_store:
      c.execute("SELECT delivery_fee FROM stores WHERE name = ?", (chosen_store,))
      fee_row = c.fetchone()
      if fee_row and fee_row[0]:
        import re
        numbers = re.findall(r"\d+\.\d+|\d+", fee_row[0])
        if numbers:
          delivery_fee_val = float(numbers[0])

    service_fee = 0.25
    total_bill = item_price + delivery_fee_val + service_fee if item_price > 0 else 0.0

    if item_price > 0:
      st.markdown(f"""
            <div style="background:#F3F4F6; padding:15px; border-radius:8px; margin-bottom:15px;">
                <b>تفاصيل الفاتورة:</b><br>
                • قيمة الوجبة/المنتج: {item_price} JD<br>
                • أجور التوصيل: {delivery_fee_val} JD<br>
                • رسوم الخدمة: {service_fee} JD<br>
                <hr style="margin:5px 0;">
                <b>المجموع الإجمالي المطلوب: <span style="color:#FF6600;">{total_bill:.2f} JD</span></b>
            </div>
            """, unsafe_allow_html=True)

    with st.form("payment_form"):
      pay_choice = st.radio("طريقة الدفع:", [
          "نقداً عند الاستلام",
          "تحويل كليك (CliQ) - رقم: 0797028819 (البنك الإسلامي) أو samarza (بنك الاتحاد)"
      ])
      submitted_order = st.form_submit_button("تأكيد الطلب وإرساله")
      if submitted_order:
        if item_price == 0:
          st.error("يرجى اختيار صنف من المتاجر أولاً قبل تأكيد الطلب!")
        else:
          client = st.session_state.get("client_info", {
              "name": "زبون", "phone": "0790000000", "address": "الكرك", "lat": 31.185, "lon": 35.705
          })
          c.execute("""INSERT INTO orders (store_name, customer_name, phone, address, items_desc, payment_method, total_price, status, cust_lat, cust_lon) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (chosen_store, client["name"], client["phone"], client["address"], chosen_item, pay_choice, total_bill, "قيد المعالجة", client["lat"], client["lon"]))
          conn.commit()
          st.success("تم إرسال طلبك بنجاح!")

    if item_price > 0:
      client_data = st.session_state.get("client_info", {"name": "زبون", "phone": "0790000000", "address": "الكرك"})
      wa_msg = (f"🏰 *طلب جديد عبر بوابة الكرك للطلبات*:\n"
                f"👤 الزبون: {client_data['name']} ({client_data['phone']})\n"
                f"📍 العنوان: {client_data['address']}\n"
                f"🏬 المتجر: {chosen_store}\n"
                f"📦 الطلب: {chosen_item}\n"
                f"💰 المجموع الكلي: {total_bill:.2f} JD\n"
                f"💳 طريقة الدفع: تم الاختيار")
      encoded_wa = urllib.parse.quote(wa_msg)
      st.markdown(f'<a href="https://wa.me/962797028819?text={encoded_wa}" target="_blank" style="display:inline-block; background-color:#25D366; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold; margin-top:10px;">💬 إرسال تفاصيل الطلب عبر الواتساب (0797028819)</a>', unsafe_allow_html=True)

  with cust_t4:
    st.markdown("### 📍 تتبع الطلب والرحلة الحية")
    c.execute("SELECT id, store_name, status, cust_lat, cust_lon FROM orders")
    orders_list = c.fetchall()
    if not orders_list:
      st.info("لا توجد طلبات حالياً للتتبع.")
    for mo in orders_list:
      st.write(f"طلب #{mo[0]} | المتجر: {mo[1]} | الحالة: 🚚 {mo[2]} | 📍 [موقع التسليم على الخريطة](https://maps.google.com/?q={mo[3]},{mo[4]})")

# =========================================================
# 2. واجهة المتاجر
# =========================================================
elif st.session_state["main_nav"] == "المتاجر":
  st.subheader("🏪 واجهة المتاجر الآمنة وإدارة المنتجات الحقيقية")
  store_pass_input = st.text_input("أدخل كلمة سر لوحة المتاجر:", type="password", key="store_login_pass")
  if store_pass_input == get_setting("store_pass"):
    st.success("تم تسجيل الدخول بنجاح!")
    play_sound_alert()
    st.markdown('<h3><span class="bell-alert">🔔</span> تنبيه الطلبات الجديدة نشط</h3>', unsafe_allow_html=True)

    st_t1, st_t2, st_t3 = st.tabs([
        "📋 الطلبات الواردة للتجهيز",
        "➕ إضافة محل أو متجر حقيقي",
        "🍔 إضافة أصناف وعروض حقيقية للمتاجر",
    ])

    with st_t1:
      c.execute("SELECT id, store_name, items_desc, status FROM orders")
      orders_db = c.fetchall()
      if not orders_db:
        st.info("لا توجد طلبات جديدة حالياً.")
      for os_item in orders_db:
        st.markdown(f"""
                <div style="background:#FFF; padding:12px; border-radius:8px; border:1px solid #ddd; margin-bottom:10px;">
                    <b>طلب رقم #{os_item[0]}</b><br>
                    🏷️ <b>يوجد طلب من بوابة الكرك لتجهيز الطلب:</b> {os_item[2]}<br>
                    📊 الحالة: {os_item[3]}
                </div>
                """, unsafe_allow_html=True)

    with st_t2:
      with st.form("store_owner_add_store"):
        st.markdown("#### إضافة محل أو متجر جديد للنظام")
        so_name = st.text_input("اسم المحل أو المتجر الحقيقي:")
        so_cat = st.selectbox("التصنيف:", ["مطاعم", "حلويات", "محامص ومكسرات", "ماركت", "خضروات وفواكه", "صيدليات ومستلزمات طبية"], key="so_cat_key")
        so_rating = st.number_input("التقييم:", value=4.9, step=0.1, key="so_rate_key")
        so_time = st.text_input("وقت التوصيل:", value="20-30 دقيقة", key="so_time_key")
        so_fee = st.text_input("رسوم التوصيل:", value="0.75 دينار", key="so_fee_key")
        so_offer = st.text_input("العرض الخاص الحقيقي:", value="عرض مميز للزبائن", key="so_offer_key")
        so_pass = st.text_input("كلمة سر المتجر:", value="5678", key="so_pass_key")
        so_phone = st.text_input("رقم هاتف المتجر (واتساب):", value="0797028819", key="so_phone_key")
        so_lat = st.number_input("خط العرض (Latitude):", value=31.185200, format="%.6f", key="so_lat_key")
        so_lon = st.number_input("خط الطول (Longitude):", value=35.704800, format="%.6f", key="so_lon_key")
        so_img_url = st.text_input("رابط صورة المحل أو المتجر الحقيقية:", value="", key="so_img_key")

        if st.form_submit_button("حفظ وإضافة المتجر"):
          c.execute("""INSERT INTO stores (name, category, rating, delivery_time, delivery_fee, image_url, offer, passcode, lat, lon, phone) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (so_name, so_cat, so_rating, so_time, so_fee, so_img_url, so_offer, so_pass, so_lat, so_lon, so_phone))
          conn.commit()
          st.success(f"تمت إضافة المتجر ({so_name}) بنجاح!")
          st.rerun()

    with st_t3:
      with st.form("store_owner_add_item"):
        st.markdown("#### إضافة أصناف وعروض حقيقية للمتاجر")
        c.execute("SELECT name FROM stores")
        stores_list = [r[0] for r in c.fetchall()]
        if stores_list:
          selected_store = st.selectbox("اختر المتجر:", stores_list, key="item_store_sel")
          item_name = st.text_input("اسم الصنف أو الوجبة الحقيقية:", key="item_name_in")
          item_price = st.number_input("السعر (بالدينار الأردني):", value=2.00, step=0.25, key="item_price_in")
          item_discount = st.text_input("العرض أو نسبة الخصم الحقيقية:", value="بدون", key="item_disc_in")
          item_img_url = st.text_input("رابط صورة الصنف الحقيقية (مثل صورة اللوز):", value="", key="item_img_in")

          if st.form_submit_button("إضافة الصنف الحقيقي إلى القائمة"):
            c.execute("""INSERT INTO items (store_name, item_name, price, discount, image_url) 
                         VALUES (?, ?, ?, ?, ?)""",
                      (selected_store, item_name, item_price, item_discount, item_img_url))
            conn.commit()
            st.success("تمت إضافة الصنف الحقيقي مع صورته بنجاح!")
            st.rerun()
        else:
          st.warning("يرجى إضافة متجر أولاً.")

  elif store_pass_input != "":
    st.error("كلمة السر غير صحيحة!")

# =========================================================
# 3. واجهة السائقين
# =========================================================
elif st.session_state["main_nav"] == "السائقين":
  st.subheader("🛵 واجهة السائقين الآمنة وتتبع خط الرحلة")
  drv_pass_input = st.text_input("أدخل كلمة سر لوحة السائقين:", type="password", key="drv_login_pass")
  if drv_pass_input == get_setting("driver_pass"):
    st.success("مرحباً بك كابتن!")
    play_sound_alert()
    st.markdown('<h3><span class="bell-alert">🔔</span> جرس تنبيه رحلات التوصيل يعمل</h3>', unsafe_allow_html=True)
    c.execute("""SELECT o.id, o.store_name, o.customer_name, o.phone, o.address, o.status, o.total_price, o.items_desc, s.lat, s.lon, o.cust_lat, o.cust_lon 
                 FROM orders o LEFT JOIN stores s ON o.store_name = s.name""")
    deliveries = c.fetchall()
    if not deliveries:
      st.info("لا توجد طلبات توصيل متاحة حالياً.")
    for do in deliveries:
      d_id, d_store, d_cust, d_phone, d_addr, d_status, d_total, d_items, s_lat, s_lon, c_lat, c_lon = do
      if s_lat is None:
        s_lat, s_lon = 31.1852, 35.7048

      st.markdown(f"""
            <div style="background:#FFF; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px;">
                <b>طلب توصيل رقم #{d_id}</b><br>
                🏬 المتجر: {d_store} | 👤 الزبون: {d_cust} (هاتف: {d_phone})<br>
                📍 عنوان الزبون: {d_addr}<br>
                📦 تفاصيل الطلب: {d_items}<br>
                💰 <b>القيمة الإجمالية المطلوبة للتحصيل (نقداً): <span style="color:#FF6600;">{d_total:.2f} JD</span></b><br>
                📊 الحالة الحالية: <b>{d_status}</b><br>
                🔗 <b>روابط التوجيه الجغرافي GPS:</b><br>
                &nbsp;&nbsp;• <a href="https://maps.google.com/?q={s_lat},{s_lon}" target="_blank">موقع المتجر للاستلام</a><br>
                &nbsp;&nbsp;• <a href="https://maps.google.com/?q={c_lat},{c_lon}" target="_blank">موقع الزبون للتسليم</a>
            </div>
            """, unsafe_allow_html=True)

      if st.button(f"تحديث الطلب #{d_id} إلى 'تم التوصيل بنجاح'", key=f"d_up_btn_{d_id}"):
        c.execute("UPDATE orders SET status = 'تم التوصيل بنجاح' WHERE id = ?", (d_id,))
        conn.commit()
        st.success("تم تحديث حالة التوصيل!")
        st.rerun()
  elif drv_pass_input != "":
    st.error("كلمة السر غير صحيحة!")

# =========================================================
# 4. الإدارة المركزية
# =========================================================
elif st.session_state["main_nav"] == "الإدارة":
  st.subheader("⚙️ لوحة الإدارة المركزية")
  admin_pass_input = st.text_input("أدخل كلمة سر لوحة الإدارة:", type="password", key="adm_login_pass")
  if admin_pass_input == get_setting("admin_pass"):
    st.success("مرحباً بك في لوحة الإدارة المركزية.")
    play_sound_alert()

    adm_t1, adm_t2, adm_t3, adm_t4, adm_t5, adm_t6, adm_t7 = st.tabs([
        "📋 الطلبات والإشعارات",
        "🏪 المتاجر والمواقع",
        "🗑️ حذف وإدارة المتاجر والأصناف",
        "➕ إضافة أصناف",
        "🛵 السائقين",
        "🔑 كلمات السر",
        "📊 التقارير",
    ])

    with adm_t1:
      c.execute("SELECT id, store_name, customer_name, total_price, status, items_desc FROM orders")
      orders_adm = c.fetchall()
      if not orders_adm:
        st.info("لا توجد طلبات مسجلة حالياً.")
      for ao in orders_adm:
        st.write(f"طلب #{ao[0]} | المتجر: {ao[1]} | الزبون: {ao[2]} | المجموع: {ao[3]} JD | الحالة: {ao[4]}")
        msg_store = f"🏰 *إشعار إدارة بوابة الكرك للمتجر {ao[1]}*:\nيوجد طلب جديد رقم #{ao[0]}\nالمنتج: {ao[5]}\nيرجى التجهيز الفوري!"
        encoded_ms = urllib.parse.quote(msg_store)
        st.markdown(f'<a href="https://wa.me/962797028819?text={encoded_ms}" target="_blank" style="background:#25D366; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:13px; margin-left:5px;">💬 إرسال واتساب للمتجر</a>', unsafe_allow_html=True)

        msg_driver = f"🏰 *إشعار إدارة بوابة الكرك للسائق*:\nيوجد طلب توصيل جديد رقم #{ao[0]} من متجر {ao[1]}\nالمجموع المطلوب تحصيله: {ao[3]} JD\nيرجى المتابعة."
        encoded_md = urllib.parse.quote(msg_driver)
        st.markdown(f'<a href="https://wa.me/962797028819?text={encoded_md}" target="_blank" style="background:#25D366; color:white; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:13px;">💬 إرسال واتساب للسائق</a>', unsafe_allow_html=True)

        if st.button(f"تأكيد الطلب #{ao[0]}", key=f"adm_cnf_btn_{ao[0]}"):
          c.execute("UPDATE orders SET status = 'تم التأكيد وجاري التجهيز' WHERE id = ?", (ao[0],))
          conn.commit()
          st.rerun()
        st.markdown("---")

    with adm_t2:
      with st.form("add_store_admin_form"):
        s_name = st.text_input("اسم المتجر الحقيقي:", key="adm_s_name")
        s_cat = st.selectbox("التصنيف:", ["مطاعم", "حلويات", "محامص ومكسرات", "ماركت", "خضروات وفواكه", "صيدليات ومستلزمات طبية"], key="adm_s_cat")
        s_rating = st.number_input("التقييم:", value=4.9, key="adm_s_rat")
        s_time = st.text_input("وقت التوصيل:", value="20-30 دقيقة", key="adm_s_time")
        s_fee = st.text_input("رسوم التوصيل:", value="0.75 دينار", key="adm_s_fee")
        s_offer = st.text_input("العرض الخاص الحقيقي:", value="عرض مميز", key="adm_s_off")
        s_passcode = st.text_input("كلمة سر المتجر:", value="5678", key="adm_s_pass")
        s_phone = st.text_input("رقم هاتف المتجر:", value="0797028819", key="adm_s_ph")
        s_lat = st.number_input("خط عرض المتجر:", value=31.185200, format="%.6f", key="adm_s_lat")
        s_lon = st.number_input("خط طول المتجر:", value=35.704800, format="%.6f", key="adm_s_lon")
        s_img_url = st.text_input("رابط صورة المتجر الحقيقية:", value="", key="adm_s_img")

        if st.form_submit_button("إضافة المتجر الحقيقي"):
          c.execute("""INSERT INTO stores (name, category, rating, delivery_time, delivery_fee, image_url, offer, passcode, lat, lon, phone) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (s_name, s_cat, s_rating, s_time, s_fee, s_img_url, s_offer, s_passcode, s_lat, s_lon, s_phone))
          conn.commit()
          st.success("تمت إضافة المتجر بنجاح!")
          st.rerun()

    with adm_t3:
      st.markdown("### 🗑️ إدارة وحذف المتاجر المسجلة")
      c.execute("SELECT id, name, category FROM stores")
      all_db_stores = c.fetchall()
      if not all_db_stores:
        st.info("لا توجد متاجر مضافة حالياً.")
      for st_item in all_db_stores:
        st_id, st_n, st_cat = st_item
        col_st1, col_st2 = st.columns([4, 1])
        with col_st1:
          st.write(f"🏬 **{st_n}** (التصنيف: {st_cat})")
        with col_st2:
          if st.button("حذف المتجر", key=f"del_store_{st_id}"):
            c.execute("DELETE FROM stores WHERE id = ?", (st_id,))
            c.execute("DELETE FROM items WHERE store_name = ?", (st_n,))
            conn.commit()
            st.success(f"تم حذف المتجر {st_n} بنجاح!")
            st.rerun()

      st.markdown("---")
      st.markdown("### 🗑️ إدارة وحذف الأصناف والوجبات")
      c.execute("SELECT id, store_name, item_name, price FROM items")
      all_db_items = c.fetchall()
      if not all_db_items:
        st.info("لا توجد أصناف مضافة حالياً.")
      for it_item in all_db_items:
        it_id, it_sname, it_iname, it_pr = it_item
        col_it1, col_it2 = st.columns([4, 1])
        with col_it1:
          st.write(f"🍔 متجر: {it_sname} | الصنف: **{it_iname}** ({it_pr} JD)")
        with col_it2:
          if st.button("حذف الصنف", key=f"del_item_{it_id}"):
            c.execute("DELETE FROM items WHERE id = ?", (it_id,))
            conn.commit()
            st.success("تم حذف الصنف بنجاح!")
            st.rerun()

    with adm_t4:
      with st.form("admin_add_item_form"):
        c.execute("SELECT name FROM stores")
        all_stores = [r[0] for r in c.fetchall()]
        if all_stores:
          sel_store_for_item = st.selectbox("اختر المتجر:", all_stores, key="adm_item_store")
          item_title = st.text_input("اسم الصنف الحقيقي:", key="adm_item_title")
          item_price = st.number_input("السعر:", value=2.50, key="adm_item_price")
          item_disc = st.text_input("العرض أو الخصم:", value="بدون", key="adm_item_disc")
          item_img_url = st.text_input("رابط صورة الصنف الحقيقية:", value="", key="adm_item_img")

          if st.form_submit_button("إضافة الصنف الحقيقي"):
            c.execute("""INSERT INTO items (store_name, item_name, price, discount, image_url) 
                         VALUES (?, ?, ?, ?, ?)""",
                      (sel_store_for_item, item_title, item_price, item_disc, item_img_url))
            conn.commit()
            st.success("تمت إضافة الصنف مع صورته بنجاح!")

    with adm_t5:
      with st.form("add_drv_form"):
        d_name = st.text_input("اسم السائق الحقيقي:", key="adm_d_name")
        d_phone = st.text_input("رقم هاتف السائق:", value="0797028819", key="adm_d_ph")
        d_veh = st.text_input("نوع المركبة:", key="adm_d_veh")
        if st.form_submit_button("إضافة السائق"):
          c.execute("INSERT INTO drivers (name, phone, vehicle) VALUES (?, ?, ?)", (d_name, d_phone, d_veh))
          conn.commit()
          st.success("تمت إضافة السائق بنجاح!")

    with adm_t6:
      with st.form("change_pass_form"):
        new_adm = st.text_input("كلمة سر الإدارة:", value=get_setting("admin_pass"), key="ch_adm")
        new_str = st.text_input("كلمة سر المتاجر:", value=get_setting("store_pass"), key="ch_str")
        new_drv = st.text_input("كلمة سر السائقين:", value=get_setting("driver_pass"), key="ch_drv")
        if st.form_submit_button("تحديث كلمات السر"):
          c.execute("UPDATE settings SET value = ? WHERE key = 'admin_pass'", (new_adm,))
          c.execute("UPDATE settings SET value = ? WHERE key = 'store_pass'", (new_str,))
          c.execute("UPDATE settings SET value = ? WHERE key = 'driver_pass'", (new_drv,))
          conn.commit()
          st.success("تم التحديث!")

    with adm_t7:
      c.execute("SELECT SUM(total_price), COUNT(*) FROM orders")
      res = c.fetchone()
      st.metric("إجمالي المبيعات", f"{res[0] if res[0] else 0.0} دينار")
      st.metric("إجمالي الطلبات", res[1] if res[1] else 0)

  elif admin_pass_input != "":
    st.error("كلمة السر غير صحيحة!")