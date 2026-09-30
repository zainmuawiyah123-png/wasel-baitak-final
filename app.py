import streamlit as str_app
import sqlite3
import os
import time
from datetime import datetime

# إعدادات صفحة Streamlit
str_app.set_page_config(page_title="بوابة الكرك للطلبات", layout="wide", page_icon="🧡")

# --- إدارة شاشة الترحيب لمنع التعليق ---
if 'show_splash' not in str_app.session_state:
    str_app.session_state.show_splash = True

if str_app.session_state.show_splash:
    str_app.markdown("""
        <div style="text-align: center; padding: 60px; background-color: #fffaf0; border-radius: 15px; border: 2px solid #ff4b4b;">
            <h1 style="color: #ff4b4b; font-size: 40px;">🏰 بوابة الكرك 🍔</h1>
            <h3 style="color: #444;">...طلبك واصل لعندك...</h3>
        </div>
    """, unsafe_allow_html=True)
    
    time.sleep(2)
    str_app.session_state.show_splash = False
    str_app.rerun()

# --- إعداد قاعدة البيانات الشاملة مع روابط المتاجر ---
DB_NAME = "wasel_talabat_pro.db"

def get_db_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS customers (phone TEXT PRIMARY KEY, name TEXT, address TEXT, lat REAL DEFAULT 31.2842, lon REAL DEFAULT 35.7048)""")
    c.execute("""CREATE TABLE IF NOT EXISTS stores (name TEXT PRIMARY KEY, category TEXT, phone TEXT, pin_code TEXT, location TEXT, delivery_time TEXT, delivery_fee REAL, image_url TEXT, rating REAL DEFAULT 5.0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, store_name TEXT, category TEXT, item_name TEXT, description TEXT, price REAL, unit_type TEXT, image_url TEXT, age_restricted INTEGER DEFAULT 0, discount_percent INTEGER DEFAULT 0, stock_qty REAL DEFAULT 100)""")
    c.execute("""CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_phone TEXT, store_name TEXT, item_name TEXT, price REAL, qty REAL, total REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, customer_phone TEXT, customer_address TEXT, customer_lat REAL, customer_lon REAL, store_name TEXT, store_lat REAL, store_lon REAL, items_desc TEXT, sub_total REAL, delivery_fee REAL, service_fee REAL, grand_total REAL, payment_method TEXT, order_status TEXT DEFAULT 'جديد (بانتظار الإدارة)', assigned_driver TEXT DEFAULT 'لم يُعين بعد', created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS drivers (name TEXT PRIMARY KEY, phone TEXT, pin_code TEXT, vehicle_type TEXT, status TEXT DEFAULT 'متوفر')""")
    c.execute("""CREATE TABLE IF NOT EXISTS store_ratings (id INTEGER PRIMARY KEY AUTOINCREMENT, store_name TEXT, customer_phone TEXT, rating INTEGER, comment TEXT)""")
    
    # التحقق من الأعمدة وإضافتها تلقائياً إن لم تكن موجودة
    try: c.execute("ALTER TABLE products ADD COLUMN stock_qty REAL DEFAULT 100")
    except: pass
    try: c.execute("ALTER TABLE products ADD COLUMN description TEXT")
    except: pass
    try: c.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
    except: pass
    try: c.execute("ALTER TABLE products ADD COLUMN discount_percent INTEGER DEFAULT 0")
    except: pass
    try: c.execute("ALTER TABLE stores ADD COLUMN rating REAL DEFAULT 5.0")
    except: pass
    try: c.execute("ALTER TABLE stores ADD COLUMN image_url TEXT")
    except: pass

    # المتاجر الأساسية الافتراضية
    c.execute("SELECT COUNT(*) FROM stores")
    if c.fetchone()[0] == 0:
        default_stores = [
            ("مطعم الرمسي", "مطاعم ومشاوي", "0790000000", "1234", "الكرك - الثنية", "25-35 دقيقة", 1.50, "", 4.9),
            ("ليالي الكرك", "مطاعم ومشويات", "0791111111", "1234", "الكرك - المرج", "15-25 دقيقة", 1.00, "", 4.8),
            ("عنبتاوي", "حلويات", "0792222222", "1234", "الكرك - المدينة", "15-25 دقيقة", 1.00, "", 5.0),
            ("حلويات حبيبة", "حلويات", "0793333333", "1234", "الكرك - المدينة", "15-25 دقيقة", 1.00, "", 4.9),
            ("جوانا", "معجنات ومأكولات", "0794444444", "1234", "الكرك - الجامعة", "20-30 دقيقة", 1.20, "", 4.7)
        ]
        c.executemany("INSERT OR IGNORE INTO stores (name, category, phone, pin_code, location, delivery_time, delivery_fee, image_url, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", default_stores)

    c.execute("SELECT COUNT(*) FROM drivers")
    if c.fetchone()[0] == 0:
        c.execute("INSERT OR IGNORE INTO drivers (name, phone, pin_code, vehicle_type, status) VALUES (?, ?, ?, ?, ?)", ("محمد الكركي", "0795555555", "1234", "دراجة نارية", "متوفر"))

    conn.commit()
    conn.close()

init_db()

# تنسيقات CSS العامة
talabat_style = """
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .main { background-color: #f4f5f7; direction: rtl; text-align: right; }
    .stButton>button { background-color: #ff5a00; color: white; border-radius: 8px; font-weight: bold; border: none; width: 100%; }
    .stButton>button:hover { background-color: #e05000; color: white; }
    .talabat-card { background-color: white; padding: 18px; border-radius: 12px; border: 1px solid #eaeaea; margin-bottom: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); direction: rtl; text-align: right; }
    .discount-badge { background-color: #ff4b4b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    </style>
"""
str_app.markdown(talabat_style, unsafe_allow_html=True)

def play_sound_alert():
    audio_html = """
        <audio autoplay controls style="display:block; margin: 10px 0; height: 30px;">
            <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
        </audio>
    """
    str_app.markdown(audio_html, unsafe_allow_html=True)

if "customer_name" not in str_app.session_state:
    str_app.session_state.update({"customer_name": "", "customer_address": "", "customer_phone": "", "lat": 31.2842, "lon": 35.7048})

str_app.markdown("<h2 style='text-align: center; color: #ff5a00;'>🏰 بوابة الكرك للطلبات - النظام المتكامل</h2>", unsafe_allow_html=True)

portal_col1, portal_col2, portal_col3, portal_col4 = str_app.columns(4)
with portal_col1:
    btn_cust = str_app.button("🛍️ واجهة الزبائن")
with portal_col2:
    btn_store = str_app.button("🏪 واجهة المتاجر")
with portal_col3:
    btn_drv = str_app.button("🛵 واجهة السائقين")
with portal_col4:
    btn_admin = str_app.button("⚙️ الإدارة المركزية")

if "active_main_portal" not in str_app.session_state:
    str_app.session_state.active_main_portal = "الزبائن"

if btn_cust: str_app.session_state.active_main_portal = "الزبائن"
if btn_store: str_app.session_state.active_main_portal = "المتاجر"
if btn_drv: str_app.session_state.active_main_portal = "السائقين"
if btn_admin: str_app.session_state.active_main_portal = "الإدارة"

main_interface = str_app.session_state.active_main_portal
str_app.markdown("---")

conn = get_db_connection()
c = conn.cursor()

# ==========================================
# 1. واجهة الزبائن
# ==========================================
if main_interface == "الزبائن":
    str_app.markdown("<h3 style='color: #333;'>🛍️ بوابة الزبائن الرئيسية</h3>", unsafe_allow_html=True)
    
    cust_tab1, cust_tab2, cust_tab3, cust_tab4 = str_app.tabs([
        "👤 1. بياناتي الشخصية وموقعي", 
        "🏠 2. تصفح المتاجر والأصناف", 
        "🛒 3. السلة ودفع الفاتورة", 
        "🚚 4. تتبع الطلبات والتقييم ⭐"
    ])
    
    with cust_tab1:
        str_app.markdown("<h2 style='color: #ff5a00;'>👤 بياناتك الشخصية وموقعك الجغرافي</h2>", unsafe_allow_html=True)
        r_name = str_app.text_input("الاسم الكامل:", value=str_app.session_state.customer_name)
        r_phone = str_app.text_input("رقم الهاتف:", value=str_app.session_state.customer_phone)
        r_address = str_app.text_area("العنوان بالتفصيل:", value=str_app.session_state.customer_address)
        
        cl1, cl2 = str_app.columns(2)
        r_lat = cl1.number_input("خط العرض (Lat):", value=str_app.session_state.lat, format="%.6f")
        r_lon = cl2.number_input("خط الطول (Lon):", value=str_app.session_state.lon, format="%.6f")
            
        if str_app.button("حفظ بياناتي 🚀"):
            if r_name.strip() and r_phone.strip():
                c.execute("INSERT OR REPLACE INTO customers (phone, name, address, lat, lon) VALUES (?, ?, ?, ?, ?)", (r_phone, r_name, r_address, r_lat, r_lon))
                conn.commit()
                str_app.session_state.update({"customer_name": r_name, "customer_phone": r_phone, "customer_address": r_address, "lat": r_lat, "lon": r_lon})
                str_app.success("✅ تم حفظ بياناتك بنجاح!")
            else:
                str_app.error("يرجى إدخال الاسم ورقم الهاتف على الأقل.")

    with cust_tab2:
        str_app.markdown("### 🔥 المتاجر والمطاعم المتاحة")
        c.execute("SELECT DISTINCT category FROM stores")
        categories_list = ["الكل"] + [row[0] for row in c.fetchall() if row[0]]
        sel_cat = str_app.selectbox("تصفية حسب القسم:", categories_list)
        
        c.execute("SELECT name, category, delivery_time, delivery_fee, image_url, rating FROM stores" if sel_cat == "الكل" else "SELECT name, category, delivery_time, delivery_fee, image_url, rating FROM stores WHERE category = ?", () if sel_cat == "الكل" else (sel_cat,))
        stores_list = c.fetchall()
        
        if not stores_list: 
            str_app.info("لا توجد متاجر مضافة حالياً.")
        
        st_cols = str_app.columns(2)
        for idx, (s_name, s_cat, s_time, s_fee, s_img, s_rate) in enumerate(stores_list):
            with st_cols[idx % 2]:
                str_app.markdown("<div class='talabat-card'>", unsafe_allow_html=True)
                if s_img and s_img.startswith("http"):
                    str_app.image(s_img, width=150)
                else:
                    str_app.markdown("<h1 style='text-align: center; margin:0;'>🏪</h1>", unsafe_allow_html=True)
                
                str_app.markdown(f"<h3 style='color:#111; margin:10px 0 5px 0; font-weight:bold;'>{s_name} <span style='font-size:15px; color:#ffaa00;'>⭐ {s_rate if s_rate else 5.0}</span></h3>", unsafe_allow_html=True)
                str_app.markdown(f"<p style='color:gray; font-size:13px; margin:2px 0;'>🏷 القسم: {s_cat} | ⏱ التوصيل: {s_time} | 🚚 الرسوم: {s_fee} د.أ</p>", unsafe_allow_html=True)
                
                if str_app.button(f"تصفح متجر {s_name} 🛒", key=f"go_store_{idx}"):
                    str_app.session_state.active_store = s_name
                    str_app.success(f"تم اختيار متجر '{s_name}'! انتقل لتبويب السلة لإتمام الطلب.")
                str_app.markdown("</div>", unsafe_allow_html=True)

    with cust_tab3:
        str_app.markdown("### 🛒 المنتجات والأصناف المتاحة للطلب والعروض")
        c.execute("SELECT name FROM stores")
        all_st_names = [s[0] for s in c.fetchall()]
        act_st = str_app.session_state.get("active_store", all_st_names[0] if all_st_names else "")
        chosen_store = str_app.selectbox("اختر المتجر أو المطعم للتسوق منه:", all_st_names, index=all_st_names.index(act_st) if act_st in all_st_names else 0)
        
        if chosen_store:
            c.execute("SELECT id, item_name, price, unit_type, description, image_url, stock_qty, discount_percent FROM products WHERE store_name = ?", (chosen_store,))
            prods = c.fetchall()
            if not prods:
                str_app.info("لا توجد أصناف مضافة لهذا المتجر بعد.")
            
            for pid, pname, pprice, punit, pdesc, pimg, pstock, pdisc in prods:
                str_app.markdown("<div class='talabat-card'>", unsafe_allow_html=True)
                if pimg and pimg.startswith("http"):
                    str_app.image(pimg, width=120)
                
                effective_price = pprice
                if pdisc and pdisc > 0:
                    effective_price = pprice * (1 - pdisc / 100)
                    str_app.markdown(f"<span class='discount-badge'>خصم {pdisc}% 🔥</span>", unsafe_allow_html=True)
                
                str_app.markdown(f"<h3 style='color:#111; margin:10px 0 5px 0; font-weight:bold;'>{pname}</h3>", unsafe_allow_html=True)
                if pdisc and pdisc > 0:
                    str_app.markdown(f"<p style='color:#888; text-decoration:line-through; font-size:14px; margin:0;'>السعر الأصلي: {pprice} د.أ</p>", unsafe_allow_html=True)
                    str_app.markdown(f"<p style='color:#ff5a00; font-weight:bold; font-size:16px; margin:2px 0;'>سعر العرض: {effective_price:.2f} د.أ ({punit}) | المتوفر: {pstock}</p>", unsafe_allow_html=True)
                else:
                    str_app.markdown(f"<p style='color:#ff5a00; font-weight:bold; font-size:16px; margin:2px 0;'>السعر: {pprice} د.أ ({punit}) | المتوفر: {pstock}</p>", unsafe_allow_html=True)
                
                if pdesc:
                    str_app.markdown(f"<p style='color:#555; font-size:13px; margin:5px 0;'>{pdesc}</p>", unsafe_allow_html=True)
                
                qty = str_app.number_input(f"حدد الكمية لـ {pname}", min_value=0.0, max_value=float(pstock) if pstock and pstock>0 else 100.0, step=1.0, key=f"q_{pid}")
                if str_app.button(f"أضف '{pname}' إلى السلة 🛒", key=f"add_{pid}"):
                    if qty > 0:
                        c.execute("INSERT INTO cart (customer_phone, store_name, item_name, price, qty, total) VALUES (?, ?, ?, ?, ?, ?)", (str_app.session_state.customer_phone, chosen_store, pname, effective_price, qty, qty*effective_price))
                        conn.commit()
                        str_app.success(f"✅ تمت إضافة {qty} من '{pname}' إلى سلتك بنجاح!")
                    else:
                        str_app.warning("يرجى تحديد الكمية أولاً.")
                str_app.markdown("</div>", unsafe_allow_html=True)
            
            str_app.markdown("---")
            str_app.markdown("### 🛍 محتويات سلة طلباتك الحالية:")
            c.execute("SELECT id, item_name, qty, total FROM cart WHERE customer_phone = ?", (str_app.session_state.customer_phone,))
            cart_items = c.fetchall()
            sub_tot = 0
            for cid, citem, cqty, ctot in cart_items:
                sub_tot += ctot
                str_app.write(f"• {citem} (الكمية: {cqty}) = {ctot:.2f} د.أ")
                if str_app.button("حذف الصنف ❌", key=f"del_{cid}"):
                    c.execute("DELETE FROM cart WHERE id = ?", (cid,))
                    conn.commit()
                    str_app.rerun()
            
            if cart_items:
                str_app.markdown(f"#### 💰 إجمالي المشتريات: `{sub_tot:.2f} د.أ` (يضاف رسوم التوصيل عند الإرسال).")
                pay_method = str_app.selectbox("طريقة الدفع:", [
                    "الدفع نقداً عند الاستلام",
                    "CliQ - samarza (بنك الاتحاد)", 
                    "CliQ - ميرال (البنك الإسلامي الأردني: 962797088219)"
                ])
                
                if str_app.button("🛒 إرسال الطلب النهائي الآن 🚀"):
                    if str_app.session_state.customer_phone and str_app.session_state.customer_name != '':
                        items_str = ", ".join([f"{i[1]} (عدد {i[2]})" for i in cart_items])
                        grand_tot = sub_tot + 1.50
                        
                        c.execute("INSERT INTO orders (customer_name, customer_phone, customer_address, store_name, items_desc, grand_total, payment_method, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                  (str_app.session_state.customer_name, str_app.session_state.customer_phone, str_app.session_state.customer_address, chosen_store, items_str, grand_tot, pay_method, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        
                        c.execute("SELECT last_insert_rowid()")
                        new_o_id = c.fetchone()[0]
                        
                        c.execute("DELETE FROM cart WHERE customer_phone = ?", (str_app.session_state.customer_phone,))
                        conn.commit()
                        
                        str_app.success("🎉 تم إرسال طلبك بنجاح للإدارة والمطعم!")
                        wa_msg = f"طلب جديد #{new_o_id}%0aالزبون: {str_app.session_state.customer_name}%0aالهاتف: {str_app.session_state.customer_phone}%0aالعنوان: {str_app.session_state.customer_address}%0aالمتجر: {chosen_store}%0aالمطلوب: {items_str}%0aالإجمالي: {grand_tot:.2f} د.أ%0aالدفع: {pay_method}"
                        wa_url = f"https://api.whatsapp.com/send?phone=962797088219&text={wa_msg}"
                        str_app.markdown(f"<a href='{wa_url}' target='_blank' style='background-color:#25d366; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold; display:inline-block;'>📤 اضغط هنا لإرسال الطلب عبر الواتساب للإدارة/المتجر</a>", unsafe_allow_html=True)
                    else:
                        str_app.error("يرجى إكمال بياناتك الشخصية أولاً.")

    with cust_tab4:
        str_app.markdown("### 🚚 تتبع الطلبات وتقييم المتاجر ⭐")
        ph = str_app.text_input("أدخل رقم هاتفك لعرض طلباتك وتقييمها:", value=str_app.session_state.customer_phone)
        if ph:
            c.execute("SELECT id, store_name, items_desc, grand_total, order_status FROM orders WHERE customer_phone = ? ORDER BY id DESC", (ph,))
            orders = c.fetchall()
            if not orders:
                str_app.info("لا توجد طلبات مسجلة بهذا الرقم.")
            for oid, ost, oit, otot, ostat in orders:
                str_app.markdown(f"<div class='talabat-card'><h4>📦 طلب رقم #{oid} من متجر: {ost}</h4><p><b>الأصناف:</b> {oit}</p><p><b>المبلغ:</b> {otot} د.أ | الحالة: <span style='color:#ff5a00; font-weight:bold;'>{ostat}</span></p></div>", unsafe_allow_html=True)
                
                # تقييم المتجر من قبل الزبون
                with str_app.form(f"rate_form_{oid}"):
                    str_app.markdown(f"**⭐ قيم تجربتك لمتجر {ost}:**")
                    user_rate = str_app.slider("التقييم من 1 إلى 5 نجوم:", 1, 5, 5, key=f"r_sl_{oid}")
                    user_comment = str_app.text_input("تعليقك (اختياري):", key=f"r_cm_{oid}")
                    if str_app.form_submit_button("إرسال التقييم ⭐"):
                        c.execute("INSERT INTO store_ratings (store_name, customer_phone, rating, comment) VALUES (?, ?, ?, ?)", (ost, ph, user_rate, user_comment))
                        conn.commit()
                        
                        # حساب متوسط التقييم للمتجر وتحديثه تلقائياً
                        c.execute("SELECT AVG(rating) FROM store_ratings WHERE store_name = ?", (ost,))
                        avg_r = c.fetchone()[0] or 5.0
                        c.execute("UPDATE stores SET rating = ? WHERE name = ?", (round(avg_r, 1), ost))
                        conn.commit()
                        
                        str_app.success("🎉 شكراً لك! تم تسجيل تقييمك بنجاح وتحديث تقييم المتجر.")

# ==========================================
# 2. واجهة المتاجر
# ==========================================
elif main_interface == "المتاجر":
    str_app.markdown("<h3 style='color: #333;'>🏪 بوابة المتاجر والمطاعم</h3>", unsafe_allow_html=True)
    c.execute("SELECT name, pin_code FROM stores")
    stores_auth = c.fetchall()
    st_names = [s[0] for s in stores_auth]
    
    if not st_names:
        str_app.warning("لا توجد متاجر مسجلة. يرجى إضافتها من لوحة الإدارة.")
    else:
        sel_store = str_app.selectbox("اختر متجرك:", st_names)
        st_pin = str_app.text_input("أدخل الرمز السري للمتجر:", type="password")
        
        if st_pin:
            store_row = next((s for s in stores_auth if s[0] == sel_store), None)
            if store_row and st_pin == store_row[1]:
                str_app.success(f"تم الدخول لمتجر {sel_store} بنجاح.")
                st_tab1, st_tab2, st_tab3 = str_app.tabs([
                    "📦 طلبات المتجر الواردة", 
                    "➕ إضافة أصناف وعروض جديدة", 
                    "✏️ تعديل أو حذف الأصناف"
                ])
                
                with st_tab1:
                    c.execute("SELECT id, customer_name, customer_phone, items_desc, order_status FROM orders WHERE store_name = ? ORDER BY id DESC", (sel_store,))
                    st_ords = c.fetchall()
                    new_ord_count = sum(1 for o in st_ords if "جديد" in o[4] or "بانتظار" in o[4] or "التحضير" in o[4])
                    if new_ord_count > 0:
                        str_app.warning(f"🔔 لديك ({new_ord_count}) طلبات جديدة أو قيد التحضير!")
                        play_sound_alert()
                    
                    if not st_ords:
                        str_app.info("لا توجد طلبات مسجلة لمتجرك حتى الآن.")
                    for oid, cnam, cph, itm, stat in st_ords:
                        str_app.markdown(f"<div class='talabat-card'><h4>طلب رقم #{oid} - الزبون: {cnam}</h4><p>📞 الهاتف: {cph}</p><p><b>المطلوب:</b> {itm}</p><p><b>حالة الطلب:</b> <span style='color:red; font-weight:bold;'>{stat}</span></p></div>", unsafe_allow_html=True)
                
                with st_tab2:
                    str_app.markdown("### ➕ إضافة صنف جديد (مع السعر، الكمية، ورابط الصورة):")
                    with str_app.form("add_product_form_store"):
                        p_name = str_app.text_input("اسم الصنف:")
                        p_cat = str_app.text_input("تصنيف الصنف:")
                        col_p1, col_p2 = str_app.columns(2)
                        p_price = col_p1.number_input("السعر (د.أ):", value=1.00, step=0.25)
                        p_stock = col_p2.number_input("الكمية المتوفرة (المخزون):", value=50.0, step=1.0)
                        
                        p_unit = str_app.text_input("نوع الوحدة (وجبة، كيس، لتر):", value="وجبة")
                        p_desc = str_app.text_area("وصف الصنف التفصيلي:")
                        p_img_url = str_app.text_input("رابط صورة الصنف (Image URL):", placeholder="https://example.com/image.jpg")
                        p_disc = str_app.number_input("نسبة الخصم %:", min_value=0, max_value=100, value=0)
                        
                        if str_app.form_submit_button("إضافة الصنف للمتجر 🚀"):
                            if p_name.strip():
                                c.execute("INSERT INTO products (store_name, category, item_name, description, price, unit_type, image_url, discount_percent, stock_qty) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                          (sel_store, p_cat, p_name.strip(), p_desc, p_price, p_unit, p_img_url.strip(), p_disc, p_stock))
                                conn.commit()
                                str_app.success(f"✅ تم إضافة الصنف '{p_name}' بنجاح!")
                            else:
                                str_app.error("يرجى إدخال اسم الصنف.")

                with st_tab3:
                    str_app.markdown("### ✏️ تعديل أو حذف الأصناف الحالية في متجرك:")
                    c.execute("SELECT id, item_name, price, unit_type, stock_qty FROM products WHERE store_name = ?", (sel_store,))
                    store_prods = c.fetchall()
                    if not store_prods:
                        str_app.info("لا توجد أصناف مسجلة لمتجرك حالياً.")
                    else:
                        prod_map = {f"{p[1]} (السعر: {p[2]} د.أ - الكمية: {p[4]})": p[0] for p in store_prods}
                        selected_p_str = str_app.selectbox("اختر الصنف للتعديل أو الحذف:", list(prod_map.keys()))
                        if selected_p_str:
                            p_id_to_edit = prod_map[selected_p_str]
                            c.execute("SELECT item_name, category, price, unit_type, description, discount_percent, stock_qty, image_url FROM products WHERE id = ?", (p_id_to_edit,))
                            p_info = c.fetchone()
                            
                            with str_app.form("edit_product_form"):
                                ep_name = str_app.text_input("اسم الصنف:", value=p_info[0])
                                ep_cat = str_app.text_input("التصنيف:", value=p_info[1])
                                col_ep1, col_ep2 = str_app.columns(2)
                                ep_price = col_ep1.number_input("السعر (د.أ):", value=float(p_info[2]), step=0.25)
                                ep_stock = col_ep2.number_input("الكمية المتوفرة:", value=float(p_info[6]) if p_info[6] is not None else 50.0, step=1.0)
                                
                                ep_unit = str_app.text_input("نوع الوحدة:", value=p_info[3])
                                ep_desc = str_app.text_area("الوصف:", value=p_info[4] if p_info[4] else "")
                                ep_img_url = str_app.text_input("رابط صورة الصنف (Image URL):", value=p_info[7] if p_info[7] else "")
                                ep_disc = str_app.number_input("نسبة الخصم %:", value=int(p_info[5]) if p_info[5] else 0, min_value=0, max_value=100)
                                
                                col_btn1, col_btn2 = str_app.columns(2)
                                with col_btn1:
                                    save_ep = str_app.form_submit_button("💾 حفظ التعديلات")
                                with col_btn2:
                                    del_ep = str_app.form_submit_button("🗑 حذف الصنف نهائياً")
                                    
                                if save_ep:
                                    c.execute("UPDATE products SET item_name=?, category=?, price=?, unit_type=?, description=?, discount_percent=?, stock_qty=?, image_url=? WHERE id=?", 
                                              (ep_name, ep_cat, ep_price, ep_unit, ep_desc, ep_disc, ep_stock, ep_img_url.strip(), p_id_to_edit))
                                    conn.commit()
                                    str_app.success("✅ تم تحديث الصنف بنجاح!")
                                    str_app.rerun()
                                if del_ep:
                                    c.execute("DELETE FROM products WHERE id=?", (p_id_to_edit,))
                                    conn.commit()
                                    str_app.success("🗑️ تم حذف الصنف بنجاح!")
                                    str_app.rerun()
            else:
                str_app.error("الرمز السري للمتجر غير صحيح!")

# ==========================================
# 3. واجهة السائقين
# ==========================================
elif main_interface == "السائقين":
    str_app.markdown("<h3 style='color: #333;'>🛵 بوابة السائقين (الكباتن)</h3>", unsafe_allow_html=True)
    c.execute("SELECT name FROM drivers")
    drv_names = [d[0] for d in c.fetchall()]
    if not drv_names:
        str_app.warning("لا توجد سائقين مسجلين في النظام.")
    else:
        sel_drv = str_app.selectbox("اختر اسمك:", drv_names)
        dr_pin = str_app.text_input("أدخل الرمز السري للسائق:", type="password")
        
        if dr_pin:
            c.execute("SELECT pin_code FROM drivers WHERE name = ?", (sel_drv,))
            row_dp = c.fetchone()
            if row_dp and dr_pin == row_dp[0]:
                str_app.success(f"مرحباً كابتن {sel_drv}.")
                c.execute("SELECT id, store_name, customer_address, items_desc, grand_total, order_status FROM orders WHERE assigned_driver = ? ORDER BY id DESC", (sel_drv,))
                dr_ords = c.fetchall()
                
                active_dr_ords = sum(1 for o in dr_ords if "مع السائق" in o[5] or "التحضير" in o[5])
                if active_dr_ords > 0:
                    str_app.warning(f"🔔 لديك ({active_dr_ords}) طلبات نشطة للتوصيل!")
                    play_sound_alert()

                if not dr_ords:
                    str_app.info("لا توجد طلبات مسندة إليك حالياً.")
                for oid, dst, cadd, itm, gtot, stat in dr_ords:
                    str_app.markdown(f"<div class='talabat-card'><h4>طلب رقم #{oid} (من متجر: {dst})</h4><p><b>عنوان التوصيل:</b> {cadd}</p><p><b>المطلوب:</b> {itm}</p><p><b>المبلغ المطلوب تحصيله:</b> {gtot} د.أ</p><p><b>الحالة:</b> <span style='color:green; font-weight:bold;'>{stat}</span></p></div>", unsafe_allow_html=True)
            else:
                str_app.error("الرمز السري للسائق غير صحيح!")

# ==========================================
# 4. لوحة الإدارة المركزية الشاملة
# ==========================================
elif main_interface == "الإدارة":
    str_app.markdown("<h3 style='color: #333;'>⚙️ لوحة الإدارة المركزية</h3>", unsafe_allow_html=True)
    admin_pass = str_app.text_input("أدخل كلمة مرور الإدارة (1234):", type="password")
    
    if admin_pass == "1234":
        str_app.success("صلاحيات الإدارة مفعلة.")
        
        tab_ords, tab_manage_stores, tab_add_store, tab_manage_drv, tab_add_dr, tab_finance, tab_qr = str_app.tabs([
            "📦 إدارة الطلبات", 
            "🏪 إدارة وتعديل/حذف المتاجر وصورها", 
            "➕ إضافة متجر جديد", 
            "🛵 تعديل/حذف السائقين", 
            "➕ إضافة سائق",
            "📊 التقرير المالي والأرباح",
            "📱 QR Code"
        ])
        
        with tab_ords:
            str_app.markdown("### 🔔 الطلبات الواردة وجرس التنبيه")
            c.execute("SELECT id, customer_name, customer_phone, customer_address, store_name, items_desc, grand_total, order_status, assigned_driver FROM orders ORDER BY id DESC")
            all_ords = c.fetchall()
            
            new_cnt = sum(1 for o in all_ords if "جديد" in o[7])
            if new_cnt > 0:
                str_app.warning(f"🚨 يوجد ({new_cnt}) طلب جديد بانتظار الإدارة!")
                play_sound_alert()
                
            if not all_ords:
                str_app.info("لا توجد طلبات مسجلة حالياً.")
            else:
                for oid, cnam, cph, cadd, st_name, itm, tot, stat, drv in all_ords:
                    with str_app.expander(f"طلب #{oid} - الزبون: {cnam} ({st_name}) - الحالة: {stat}"):
                        str_app.write(f"📞 هاتف الزبون: {cph} | 📍 العنوان: {cadd}")
                        str_app.write(f"🛒 الأصناف: {itm}")
                        str_app.write(f"💰 المبلغ: {tot} د.أ | السائق: {drv}")
                        
                        c.execute("SELECT name FROM drivers")
                        all_d_names = ["لم يُعين بعد"] + [d[0] for d in c.fetchall()]
                        new_drv = str_app.selectbox("تعيين سائق:", all_d_names, index=all_d_names.index(drv) if drv in all_d_names else 0, key=f"d_sel_{oid}")
                        new_stat = str_app.selectbox("تحديث الحالة:", ['جديد (بانتظار الإدارة)', 'تم الاعتماد وجاري التحضير بالمتجر', 'مع السائق في الطريق إليك', 'تم التوصيل بنجاح', 'ملغي'], index=0, key=f"s_sel_{oid}")
                        
                        if str_app.button("حفظ تحديث الطلب", key=f"save_o_{oid}"):
                            c.execute("UPDATE orders SET order_status=?, assigned_driver=? WHERE id=?", (new_stat, new_drv, oid))
                            conn.commit()
                            str_app.success("تم التحديث بنجاح!")
                            str_app.rerun()

        with tab_manage_stores:
            str_app.markdown("### 🏪 إدارة وتعديل المتاجر وصورها الحقيقية")
            c.execute("SELECT name, category, phone, pin_code, delivery_time, delivery_fee, image_url, rating FROM stores")
            stores_db = c.fetchall()
            if not stores_db:
                str_app.info("لا توجد متاجر مسجلة حالياً.")
            else:
                st_map_adm = {s[0]: s for s in stores_db}
                sel_st_adm = str_app.selectbox("اختر المتجر للإدارة والتعديل:", list(st_map_adm.keys()))
                if sel_st_adm:
                    st_dat = st_map_adm[sel_st_adm]
                    with str_app.form("edit_store_form_admin"):
                        up_cat = str_app.text_input("القسم:", value=st_dat[1])
                        up_phone = str_app.text_input("الهاتف:", value=st_dat[2])
                        up_pin = str_app.text_input("الرمز السري للمتجر:", value=st_dat[3])
                        up_time = str_app.text_input("وقت التوصيل:", value=st_dat[4])
                        up_fee = str_app.number_input("رسوم التوصيل:", value=float(st_dat[5]))
                        up_img = str_app.text_input("رابط صورة المتجر (Image URL):", value=st_dat[6] if st_dat[6] else "")
                        
                        col_s1, col_s2 = str_app.columns(2)
                        with col_s1:
                            save_st = str_app.form_submit_button("💾 حفظ التعديلات")
                        with col_s2:
                            del_st = str_app.form_submit_button("🗑 حذف المتجر نهائياً")
                            
                        if save_st:
                            c.execute("UPDATE stores SET category=?, phone=?, pin_code=?, delivery_time=?, delivery_fee=?, image_url=? WHERE name=?", 
                                      (up_cat, up_phone, up_pin, up_time, up_fee, up_img.strip(), sel_st_adm))
                            conn.commit()
                            str_app.success("✅ تم تحديث بيانات المتجر والصورة بنجاح!")
                            str_app.rerun()
                        if del_st:
                            c.execute("DELETE FROM stores WHERE name=?", (sel_st_adm,))
                            c.execute("DELETE FROM products WHERE store_name=?", (sel_st_adm,))
                            conn.commit()
                            str_app.success("🗑 تم حذف المتجر ومنتجاته بنجاح!")
                            str_app.rerun()

        with tab_add_store:
            str_app.markdown("### ➕ إضافة متجر أو مطعم جديد")
            with str_app.form("new_store_form_admin"):
                ns_name = str_app.text_input("اسم المتجر الجديد:")
                ns_cat = str_app.text_input("القسم (مثال: مطاعم، حلويات):")
                ns_phone = str_app.text_input("رقم الهاتف:")
                ns_pin = str_app.text_input("الرمز السري لدخول المتجر:")
                ns_time = str_app.text_input("وقت التوصيل:", value="20-30 دقيقة")
                ns_fee = str_app.number_input("رسوم التوصيل:", value=1.50)
                ns_img = str_app.text_input("رابط صورة/شعار المتجر (Image URL):")
                
                if str_app.form_submit_button("إضافة المتجر 🚀"):
                    if ns_name.strip() and ns_pin.strip():
                        c.execute("INSERT OR REPLACE INTO stores (name, category, phone, pin_code, delivery_time, delivery_fee, image_url, rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                  (ns_name.strip(), ns_cat, ns_phone, ns_pin, ns_time, ns_fee, ns_img.strip(), 5.0))
                        conn.commit()
                        str_app.success(f"✅ تم إضافة المتجر '{ns_name}' بنجاح!")
                    else:
                        str_app.error("يرجى إدخال اسم المتجر والرمز السري.")

        with tab_manage_drv:
            str_app.markdown("### 🛵 إدارة أو حذف السائقين")
            c.execute("SELECT name, phone, pin_code, vehicle_type FROM drivers")
            drivers_db = c.fetchall()
            if not drivers_db:
                str_app.info("لا توجد سائقين مسجلين حالياً.")
            else:
                drv_map_adm = {d[0]: d for d in drivers_db}
                sel_drv_adm = str_app.selectbox("اختر السائق:", list(drv_map_adm.keys()))
                if sel_drv_adm:
                    d_dat = drv_map_adm[sel_drv_adm]
                    with str_app.form("edit_driver_form"):
                        ud_phone = str_app.text_input("هاتف السائق:", value=d_dat[1])
                        ud_pin = str_app.text_input("الرمز السري:", value=d_dat[2])
                        ud_veh = str_app.text_input("نوع المركبة:", value=d_dat[3])
                        
                        col_d1, col_d2 = str_app.columns(2)
                        with col_d1:
                            save_dr = str_app.form_submit_button("💾 حفظ التعديلات")
                        with col_d2:
                            del_dr = str_app.form_submit_button("🗑️ حذف السائق")
                            
                        if save_dr:
                            c.execute("UPDATE drivers SET phone=?, pin_code=?, vehicle_type=? WHERE name=?", (ud_phone, ud_pin, ud_veh, sel_drv_adm))
                            conn.commit()
                            str_app.success("✅ تم التحديث بنجاح!")
                            str_app.rerun()
                        if del_dr:
                            c.execute("DELETE FROM drivers WHERE name=?", (sel_drv_adm,))
                            conn.commit()
                            str_app.success("🗑 تم الحذف بنجاح!")
                            str_app.rerun()

        with tab_add_dr:
            str_app.markdown("### ➕ إضافة سائق جديد")
            with str_app.form("new_driver_form"):
                nd_name = str_app.text_input("اسم السائق الكامل:")
                nd_phone = str_app.text_input("رقم الهاتف:")
                nd_pin = str_app.text_input("الرمز السري:")
                nd_veh = str_app.text_input("نوع المركبة:", value="دراجة نارية")
                
                if str_app.form_submit_button("إضافة السائق 🚀"):
                    if nd_name.strip() and nd_pin.strip():
                        c.execute("INSERT OR REPLACE INTO drivers (name, phone, pin_code, vehicle_type, status) VALUES (?, ?, ?, ?, ?)", (nd_name.strip(), nd_phone, nd_pin, nd_veh, "متوفر"))
                        conn.commit()
                        str_app.success(f"✅ تم إضافة السائق '{nd_name}' بنجاح!")
                    else:
                        str_app.error("يرجى إدخال اسم السائق والرمز السري.")

        with tab_finance:
            str_app.markdown("### 📊 التقرير المالي الشامل والأرباح")
            c.execute("SELECT SUM(grand_total) FROM orders WHERE order_status = 'تم التوصيل بنجاح'")
            total_rev = c.fetchone()[0] or 0.0
            c.execute("SELECT COUNT(*) FROM orders")
            total_orders_count = c.fetchone()[0] or 0
            
            col_f1, col_f2 = str_app.columns(2)
            col_f1.metric("إجمالي المبيعات المكتملة", f"{total_rev:.2f} د.أ")
            col_f2.metric("إجمالي عدد الطلبات الكلي", total_orders_count)
            
            str_app.markdown("---")
            str_app.markdown("#### تفاصيل كافة الطلبات المسجلة في النظام:")
            c.execute("SELECT id, customer_name, store_name, grand_total, order_status, created_at FROM orders ORDER BY id DESC")
            fin_ords = c.fetchall()
            for fid, fnam, fst, ftot, fstat, fdate in fin_ords:
                str_app.write(f"• طلب #{fid} | الزبون: {fnam} | المتجر: {fst} | المبلغ: {ftot} د.أ | الحالة: {fstat} | التاريخ: {fdate}")

        with tab_qr:
            str_app.markdown("### 📱 رمز الاستجابة السريعة (QR Code) للتطبيق")
            str_app.info("يمكنك طباعة هذا الرمز أو عرضه للزبائن لسهولة الدخول للرابط الخاص بالتطبيق.")
            qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=https://share.streamlit.io/"
            str_app.image(qr_url, width=250)
    elif admin_pass != "":
        str_app.error("كلمة مرور الإدارة غير صحيحة!")

conn.close()