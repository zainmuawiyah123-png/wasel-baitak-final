import streamlit as str_app
import streamlit.components.v1 as components
import urllib.parse
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

# --- إعداد قاعدة البيانات وحمايتها نهائياً من أي مسح ---
DB_NAME = "wasel_talabat_pro.db"

str_app.markdown('<link rel="manifest" href="manifest.json"><meta name="theme-color" content="#ff4b4b"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="Karak Gate">', unsafe_allow_html=True)

def get_db_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # إنشاء الجداول الأساسية
    c.execute("""CREATE TABLE IF NOT EXISTS customers (phone TEXT PRIMARY KEY, name TEXT, address TEXT, lat REAL DEFAULT 31.2842, lon REAL DEFAULT 35.7048)""")
    c.execute("""CREATE TABLE IF NOT EXISTS stores (name TEXT PRIMARY KEY, category TEXT, phone TEXT, pin_code TEXT, location TEXT, lat REAL, lon REAL, delivery_time TEXT, delivery_fee REAL, image_url TEXT, discount_badge TEXT DEFAULT '', rating REAL DEFAULT 5.0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, store_name TEXT, category TEXT, item_name TEXT, description TEXT, price REAL, unit_type TEXT, image_url TEXT, age_restricted INTEGER DEFAULT 0, discount_percent INTEGER DEFAULT 0, stock_qty REAL DEFAULT 100)""")
    c.execute("""CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_phone TEXT, store_name TEXT, item_name TEXT, price REAL, qty REAL, total REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, customer_phone TEXT, customer_address TEXT, customer_lat REAL, customer_lon REAL, store_name TEXT, store_lat REAL, store_lon REAL, items_desc TEXT, sub_total REAL, delivery_fee REAL, service_fee REAL, grand_total REAL, payment_method TEXT, order_status TEXT DEFAULT 'جديد (بانتظار الإدارة)', assigned_driver TEXT DEFAULT 'لم يُعين بعد', created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS drivers (name TEXT PRIMARY KEY, phone TEXT, pin_code TEXT, vehicle_type TEXT, status TEXT DEFAULT 'متوفر')""")
    
    # التحقق من الأعمدة وإضافتها إن لم تكن موجودة دون المسح بالبيانات القديمة
    try: c.execute("ALTER TABLE products ADD COLUMN stock_qty REAL DEFAULT 100")
    except: pass
    try: c.execute("ALTER TABLE products ADD COLUMN description TEXT")
    except: pass
    try: c.execute("ALTER TABLE products ADD COLUMN image_url TEXT")
    except: pass
    try: c.execute("ALTER TABLE stores ADD COLUMN image_url TEXT")
    except: pass
    try: c.execute("ALTER TABLE stores ADD COLUMN rating REAL DEFAULT 5.0")
    except: pass
    try: c.execute("ALTER TABLE products ADD COLUMN discount_percent INTEGER DEFAULT 0")
    except: pass

    # إدخال السائق الافتراضي فقط إذا كان جدول السائقين فارغاً
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
    str_app.session_state.update({"customer_name": "", "customer_address": "", "customer_phone": "", "lat": 31.2842, "lon": 35.7048, "selected_category": "الكل"})

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
        "🚚 4. تتبع مسار طلبي"
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
        str_app.markdown("### 🔥 العروض والمتاجر المتاحة")
        c.execute("SELECT DISTINCT category FROM stores")
        categories_list = ["الكل"] + [row[0] for row in c.fetchall() if row[0]]
        
        sel_cat = str_app.selectbox("تصفية حسب القسم:", categories_list)
        
        c.execute("SELECT name, category, delivery_time, delivery_fee, image_url, rating FROM stores" if sel_cat == "الكل" else "SELECT name, category, delivery_time, delivery_fee, image_url, rating FROM stores WHERE category = ?", () if sel_cat == "الكل" else (sel_cat,))
        stores_list = c.fetchall()
        
        if not stores_list: 
            str_app.info("لا توجد متاجر مضافة حالياً. يرجى إضافتها من لوحة الإدارة.")
        
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
        str_app.markdown("### 🚚 تتبع الطلبات الحالية والتقييم")
        ph = str_app.text_input("أدخل رقم هاتفك لعرض طلباتك وتتبعها وتقييمها:", value=str_app.session_state.customer_phone)
        if ph:
            c.execute("SELECT id, store_name, items_desc, grand_total, order_status, assigned_driver FROM orders WHERE customer_phone = ? ORDER BY id DESC", (ph,))
            orders = c.fetchall()
            if not orders:
                str_app.info("لا توجد طلبات مسجلة بهذا الرقم.")
            for oid, ost, oit, otot, ostat, odrv in orders:
                str_app.markdown(f"<div class='talabat-card'><h4>📦 طلب رقم #{oid} من متجر: {ost}</h4><p><b>الأصناف:</b> {oit}</p><p><b>المبلغ الإجمالي:</b> {otot} د.أ</p><p style='color:#ff5a00; font-weight:bold;'>حالة الطلب: {ostat}</p><p><b>السائق المعين:</b> {odrv}</p></div>", unsafe_allow_html=True)

# ==========================================
# 2. واجهة المتاجر
# ==========================================
elif main_interface == "المتاجر":
    str_app.markdown("<h3 style='color: #333;'>🏪 بوابة المتاجر والمطاعم</h3>", unsafe_allow_html=True)
    c.execute("SELECT name FROM stores")
    st_names = [s[0] for s in c.fetchall()]
    if not st_names:
        str_app.warning("لا توجد متاجر مسجلة في النظام حالياً. يرجى إضافتها من لوحة الإدارة.")
    else:
        sel_store = str_app.selectbox("اختر متجرك:", st_names)
        st_pin = str_app.text_input("أدخل الرمز السري للمتجر:", type="password")
        
        if st_pin:
            c.execute("SELECT pin_code FROM stores WHERE name = ?", (sel_store,))
            row_pin = c.fetchone()
            if row_pin and st_pin == row_pin[0]:
                str_app.success(f"تم الدخول لمتجر {sel_store} بنجاح.")
                st_tab1, st_tab2, st_tab3 = str_app.tabs([
                    "📦 طلبات المتجر الواردة", 
                    "➕ إضافة أصناف جديدة مع العروض والأسعار", 
                    "✏️ تعديل أو حذف الأصناف والحالية"
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
                    str_app.markdown("### ➕ إضافة صنف جديد (مع السعر، نسبة الخصم، والكمية ورابط الصورة):")
                    with str_app.form("add_product_form_store"):
                        p_name = str_app.text_input("اسم الصنف:")
                        p_cat = str_app.text_input("تصنيف الصنف:")
                        col_p1, col_p2 = str_app.columns(2)
                        p_price = col_p1.number_input("السعر (د.أ):", value=1.00, step=0.25)
                        p_stock = col_p2.number_input("الكمية المتوفرة (المخزون):", value=50.0, step=1.0)
                        
                        p_unit = str_app.text_input("نوع الوحدة (وجبة، كيس، لتر، قطعة):", value="وجبة")
                        p_desc = str_app.text_area("وصف الصنف التفصيلي:")
                        p_img_url = str_app.text_input("رابط صورة الصنف (Image URL):", placeholder="https://example.com/image.jpg")
                        p_disc = str_app.number_input("نسبة الخصم % (0 إذا لم يوجد عرض):", min_value=0, max_value=100, value=0)
                        
                        if str_app.form_submit_button("إضافة الصنف للمتجر 🚀"):
                            if p_name.strip():
                                c.execute("INSERT INTO products (store_name, category, item_name, description, price, unit_type, image_url, discount_percent, stock_qty) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                          (sel_store, p_cat, p_name.strip(), p_desc, p_price, p_unit, p_img_url.strip(), p_disc, p_stock))
                                conn.commit()
                                str_app.success(f"✅ تم إضافة الصنف '{p_name}' مع نسبة خصم {p_disc}% بنجاح!")
                            else:
                                str_app.error("يرجى إدخال اسم الصنف على الأقل.")

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
        str_app.warning("لا توجد سائقين مسجلين في النظام. يرجى إضافتهم من لوحة الإدارة.")
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
# 4. لوحة الإدارة المركزية
# ==========================================
elif main_interface == "الإدارة":
    str_app.markdown("<h3 style='color: #333;'>⚙️ لوحة الإدارة المركزية</h3>", unsafe_allow_html=True)
    admin_pass = str_app.text_input("أدخل كلمة مرور الإدارة:", type="password")
    
    if admin_pass == "1234":
        str_app.success("صلاحيات الإدارة مفعلة.")
        
        tab_ords, tab_manage_stores, tab_add_st, tab_admin_prods, tab_manage_drv, tab_add_dr, tab_qr = str_app.tabs([
            "📦 إدارة الطلبات", 
            "🏪 تعديل/حذف المتاجر والتقييم", 
            "➕ إضافة متجر", 
            "🍔 إدارة وإضافة أصناف وعروض المتاجر", 
            "🛵 تعديل/حذف السائقين", 
            "➕ إضافة سائق",
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
            str_app.markdown("### 🏪 تعديل أو حذف المتاجر وتحديث التقييم (Rate)")
            c.execute("SELECT name, category, phone, pin_code, delivery_time, delivery_fee, image_url, rating FROM stores")
            stores_db = c.fetchall()
            if not stores_db:
                str_app.info("لا توجد متاجر مسجلة حالياً.")
            else:
                st_map_admin = {s[0]: s for s in stores_db}
                sel_st_adm = str_app.selectbox("اختر المتجر للإدارة:", list(st_map_admin.keys()))
                if sel_st_adm:
                    st_dat = st_map_admin[sel_st_adm]
                    with str_app.form("edit_store_form"):
                        up_cat = str_app.text_input("القسم:", value=st_dat[1])
                        up_phone = str_app.text_input("هاتف المتجر:", value=st_dat[2])
                        up_pin = str_app.text_input("الرمز السري:", value=st_dat[3])
                        up_time = str_app.text_input("مدة التوصيل:", value=st_dat[4])
                        up_fee = str_app.number_input("رسوم التوصيل:", value=float(st_dat[5]))
                        up_img = str_app.text_input("رابط صورة المتجر (Image URL):", value=st_dat[6] if st_dat[6] else "")
                        up_rating = str_app.number_input("التقييم (Rate من 1.0 إلى 5.0):", value=float(st_dat[7]) if st_dat[7] else 5.0, min_value=1.0, max_value=5.0, step=0.1)
                        
                        col_s1, col_s2 = str_app.columns(2)
                        with col_s1:
                            save_st = str_app.form_submit_button("💾 حفظ تعديلات المتجر")
                        with col_s2:
                            del_st = str_app.form_submit_button("🗑 حذف المتجر نهائياً")
                            
                        if save_st:
                            c.execute("UPDATE stores SET category=?, phone=?, pin_code=?, delivery_time=?, delivery_fee=?, image_url=?, rating=? WHERE name=?", (up_cat, up_phone, up_pin, up_time, up_fee, up_img.strip(), up_rating, sel_st_adm))
                            conn.commit()
                            str_app.success("✅ تم تحديث بيانات المتجر والتقييم بنجاح!")
                            str_app.rerun()
                        if del_st:
                            c.execute("DELETE FROM stores WHERE name=?", (sel_st_adm,))
                            c.execute("DELETE FROM products WHERE store_name=?", (sel_st_adm,))
                            conn.commit()
                            str_app.success("🗑 تم حذف المتجر ومنتجاته بنجاح!")
                            str_app.rerun()

        with tab_add_st:
            str_app.markdown("### ➕ إضافة متجر أو مطعم جديد")
            with str_app.form("new_store_form"):
                ns_name = str_app.text_input("اسم المتجر:")
                ns_cat = str_app.text_input("القسم (مثال: مطاعم، سوبرماركت، مخابز):")
                ns_phone = str_app.text_input("رقم هاتف المتجر:")
                ns_pin = str_app.text_input("الرمز السري لدخول المتجر:")
                ns_time = str_app.text_input("وقت التوصيل التقديري:", value="20-30 دقيقة")
                ns_fee = str_app.number_input("رسوم التوصيل الافتراضية (د.أ):", value=1.50)
                ns_img_url = str_app.text_input("رابط شعار أو صورة المتجر (Image URL):", placeholder="https://example.com/logo.jpg")
                ns_rating = str_app.number_input("التقييم الابتدائي (Rate):", value=5.0, min_value=1.0, max_value=5.0, step=0.1)
                
                if str_app.form_submit_button("إضافة المتجر 🚀"):
                    if ns_name.strip() and ns_pin.strip():
                        c.execute("INSERT OR REPLACE INTO stores (name, category, phone, pin_code, delivery_time, delivery_fee, image_url, rating, lat, lon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                  (ns_name.strip(), ns_cat, ns_phone, ns_pin, ns_time, ns_fee, ns_img_url.strip(), ns_rating, 31.2842, 35.7048))
                        conn.commit()
                        str_app.success(f"✅ تم إضافة المتجر '{ns_name}' بنجاح!")
                    else:
                        str_app.error("يرجى إدخال اسم المتجر والرمز السري على الأقل.")

        with tab_admin_prods:
            str_app.markdown("### 🍔 إدارة وإضافة أصناف وعروض المتاجر من لوحة الإدارة")
            c.execute("SELECT name FROM stores")
            all_stores_names = [s[0] for s in c.fetchall()]
            if not all_stores_names:
                str_app.info("لا توجد متاجر مضافة بعد. يرجى إضافة متجر أولاً.")
            else:
                chosen_admin_store = str_app.selectbox("اختر المتجر لإدارة أصنافه أو إضافة صنف جديد:", all_stores_names, key="adm_st_sel")
                
                with str_app.form("admin_add_new_product"):
                    str_app.markdown(f"**➕ إضافة صنف جديد لمتجر ({chosen_admin_store}):**")
                    adm_p_name = str_app.text_input("اسم الصنف الجديد:")
                    adm_p_cat = str_app.text_input("التصنيف:")
                    col_ap1, col_ap2 = str_app.columns(2)
                    adm_p_price = col_ap1.number_input("السعر (د.أ):", value=1.00, step=0.25)
                    adm_p_stock = col_ap2.number_input("الكمية المتوفرة (المخزون):", value=50.0, step=1.0)
                    adm_p_unit = str_app.text_input("الوحدة (وجبة، كيس، لتر):", value="وجبة")
                    adm_p_desc = str_app.text_area("وصف الصنف:")
                    adm_p_img = str_app.text_input("رابط صورة الصنف (Image URL):", placeholder="https://example.com/product.jpg", key="adm_img_url_in")
                    adm_p_disc = str_app.number_input("نسبة الخصم % (عروض الأصناف):", min_value=0, max_value=100, value=0, key="adm_disc_in")
                    
                    if str_app.form_submit_button("إضافة الصنف كمسؤول 🚀"):
                        if adm_p_name.strip():
                            c.execute("INSERT INTO products (store_name, category, item_name, description, price, unit_type, image_url, discount_percent, stock_qty) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                      (chosen_admin_store, adm_p_cat, adm_p_name.strip(), adm_p_desc, adm_p_price, adm_p_unit, adm_p_img.strip(), adm_p_disc, adm_p_stock))
                            conn.commit()
                            str_app.success(f"✅ تم إضافة الصنف '{adm_p_name}' مع نسبة خصم {adm_p_disc}% بنجاح!")
                        else:
                            str_app.error("يرجى إدخال اسم الصنف.")

                str_app.markdown("---")
                str_app.markdown("### ✏️ قائمة الأصناف الحالية (تعديل أو حذف مباشر):")
                c.execute("SELECT id, item_name, price, unit_type, stock_qty, description, image_url, discount_percent FROM products WHERE store_name = ?", (chosen_admin_store,))
                store_products_all = c.fetchall()
                if not store_products_all:
                    str_app.info("لا توجد أصناف لهذا المتجر حالياً.")
                else:
                    for sp_id, sp_name, sp_price, sp_unit, sp_stock, sp_desc, sp_img, sp_disc in store_products_all:
                        with str_app.expander(f"صنف: {sp_name} | السعر: {sp_price} د.أ | خصم: {sp_disc}%"):
                            with str_app.form(f"form_admin_prod_{sp_id}"):
                                ap_name = str_app.text_input("اسم الصنف:", value=sp_name, key=f"ap_n_{sp_id}")
                                col_ep1, col_ep2 = str_app.columns(2)
                                ap_price = col_ep1.number_input("السعر:", value=float(sp_price), step=0.25, key=f"ap_p_{sp_id}")
                                ap_stock = col_ep2.number_input("الكمية:", value=float(sp_stock) if sp_stock is not None else 50.0, step=1.0, key=f"ap_st_{sp_id}")
                                ap_unit = str_app.text_input("الوحدة:", value=sp_unit, key=f"ap_u_{sp_id}")
                                ap_desc = str_app.text_area("الوصف:", value=sp_desc if sp_desc else "", key=f"ap_d_{sp_id}")
                                ap_img_edit = str_app.text_input("رابط الصورة (Image URL):", value=sp_img if sp_img else "", key=f"ap_img_{sp_id}")
                                ap_disc_edit = str_app.number_input("نسبة الخصم %:", value=int(sp_disc) if sp_disc else 0, min_value=0, max_value=100, key=f"ap_disc_{sp_id}")
                                
                                col_btn1, col_btn2 = str_app.columns(2)
                                with col_btn1:
                                    if str_app.form_submit_button("حفظ التعديل"):
                                        c.execute("UPDATE products SET item_name=?, price=?, unit_type=?, stock_qty=?, description=?, image_url=?, discount_percent=? WHERE id=?", (ap_name, ap_price, ap_unit, ap_stock, ap_desc, ap_img_edit.strip(), ap_disc_edit, sp_id))
                                        conn.commit()
                                        str_app.success("✅ تم التعديل بنجاح!")
                                        str_app.rerun()
                                with col_btn2:
                                    if str_app.form_submit_button("حذف الصنف"):
                                        c.execute("DELETE FROM products WHERE id=?", (sp_id,))
                                        conn.commit()
                                        str_app.success("🗑 تم الحذف بنجاح!")
                                        str_app.rerun()

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
                            save_dr = str_app.form_submit_button("💾 حفظ تعديلات السائق")
                        with col_d2:
                            del_dr = str_app.form_submit_button("🗑️ حذف السائق نهائياً")
                            
                        if save_dr:
                            c.execute("UPDATE drivers SET phone=?, pin_code=?, vehicle_type=? WHERE name=?", (ud_phone, ud_pin, ud_veh, sel_drv_adm))
                            conn.commit()
                            str_app.success("✅ تم تحديث بيانات السائق بنجاح!")
                            str_app.rerun()
                        if del_dr:
                            c.execute("DELETE FROM drivers WHERE name=?", (sel_drv_adm,))
                            conn.commit()
                            str_app.success("🗑 تم حذف السائق بنجاح!")
                            str_app.rerun()

        with tab_add_dr:
            str_app.markdown("### ➕ إضافة سائق جديد")
            with str_app.form("new_driver_form"):
                nd_name = str_app.text_input("اسم السائق الكامل:")
                nd_phone = str_app.text_input("رقم الهاتف:")
                nd_pin = str_app.text_input("الرمز السري:")
                nd_veh = str_app.text_input("نوع المركبة (دراجة نارية، سيارة):", value="دراجة نارية")
                
                if str_app.form_submit_button("إضافة السائق 🚀"):
                    if nd_name.strip() and nd_pin.strip():
                        c.execute("INSERT OR REPLACE INTO drivers (name, phone, pin_code, vehicle_type, status) VALUES (?, ?, ?, ?, ?)", (nd_name.strip(), nd_phone, nd_pin, nd_veh, "متوفر"))
                        conn.commit()
                        str_app.success(f"✅ تم إضافة السائق '{nd_name}' بنجاح!")
                    else:
                        str_app.error("يرجى إدخال اسم السائق والرمز السري.")

        with tab_qr:
            str_app.markdown("### 📱 رمز الاستجابة السريعة (QR Code) للتطبيق")
            str_app.info("يمكنك طباعة هذا الرمز أو عرضه للزبائن لسهولة الدخول للرابط الخاص بالتطبيق.")
            qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=https://share.streamlit.io/"
            str_app.image(qr_url, width=250)
    elif admin_pass != "":
        str_app.error("كلمة مرور الإدارة غير صحيحة!")

conn.close()