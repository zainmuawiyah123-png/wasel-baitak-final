import sqlite3
import streamlit as str_app
import streamlit.components.v1 as components
import pandas as pd
import urllib.parse
import os
from datetime import datetime
import time
import datetime
import time
str_app.markdown('<script>const md={"name":"Karak Gate","short_name":"Karak Gate","start_url":"./","display":"standalone","background_color":"#ffffff","theme_color":"#ff4b4b","icons":[{"src":"https://img.icons8.com/color/192/192/kawaii-pizza.png","sizes":"192x192","type":"image/png"},{"src":"https://img.icons8.com/color/512/512/kawaii-pizza.png","sizes":"512x512","type":"image/png"}]};const blob=new Blob([JSON.stringify(md)],{type:"application/json"});const l=document.createElement("link");l.rel="manifest";l.href=URL.createObjectURL(blob);document.head.appendChild(l);let dp;window.addEventListener("beforeinstallprompt",(e)=>{e.preventDefault();dp=e;document.getElementById("install-container").style.display="block";});document.getElementById("install-btn").addEventListener("click",async()=>{if(dp){dp.prompt();dp=null;document.getElementById("install-container").style.display="none";}});</script><meta name="theme-color" content="#ff4b4b"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="Karak Gate">', unsafe_allow_html=True)
DB_NAME = "wasel_talabat_pro.db"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def get_db_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def save_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return ""

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS customers (phone TEXT PRIMARY KEY, name TEXT, address TEXT, lat REAL DEFAULT 31.2842, lon REAL DEFAULT 35.7048)""")
    c.execute("""CREATE TABLE IF NOT EXISTS stores (name TEXT PRIMARY KEY, category TEXT, phone TEXT, pin_code TEXT, location TEXT, lat REAL, lon REAL, delivery_time TEXT, delivery_fee REAL, image_url TEXT, discount_badge TEXT DEFAULT '')""")
    c.execute("""CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, store_name TEXT, category TEXT, item_name TEXT, description TEXT, price REAL, unit_type TEXT, image_url TEXT, age_restricted INTEGER DEFAULT 0, discount_percent INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_phone TEXT, store_name TEXT, item_name TEXT, price REAL, qty REAL, total REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, customer_phone TEXT, customer_address TEXT, customer_lat REAL, customer_lon REAL, store_name TEXT, store_lat REAL, store_lon REAL, items_desc TEXT, sub_total REAL, delivery_fee REAL, service_fee REAL, grand_total REAL, payment_method TEXT, order_status TEXT DEFAULT 'جديد (بانتظار الإدارة)', assigned_driver TEXT DEFAULT 'لم يُعين بعد', created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS drivers (name TEXT PRIMARY KEY, phone TEXT, pin_code TEXT, vehicle_type TEXT, status TEXT DEFAULT 'متوفر')""")
    
    conn.commit()
    conn.close()

init_db()

str_app.set_page_config(page_title="بوابة الكرك للطلبات", layout="wide", page_icon="🧡")

if 'welcomed' not in str_app.session_state:
    str_app.session_state.welcomed = False

if not str_app.session_state.welcomed:
    str_app.markdown("""
        <style>.stApp { background-color: #FF5A00 !important; }</style>
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh; text-align: center; color: #000000;">
            <h1 style="font-size: 4rem; font-weight: 900; color: #000000;">🍔 بوابة الكرك 🏰</h1>
            <h3 style="color: #111111; margin-top: 15px;">طلبك واصل لعندك...</h3>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(2.5)
    str_app.session_state.welcomed = True
    str_app.rerun()

talabat_style = """
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .main { background-color: #f4f5f7; direction: rtl; text-align: right; }
    .stButton>button { background-color: #ff5a00; color: white; border-radius: 8px; font-weight: bold; border: none; width: 100%; }
    .stButton>button:hover { background-color: #e05000; color: white; }
    .talabat-card { background-color: white; padding: 18px; border-radius: 12px; border: 1px solid #eaeaea; margin-bottom: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); direction: rtl; text-align: right; }
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
        "👤 1. بياناتي الشخصية وموقعي (البداية)", 
        "🏠 2. تصفح المتاجر والأصناف", 
        "🛒 3. السلة ودفع الفاتورة", 
        "🚚 4. تتبع مسار طلبي"
    ])
    
    with cust_tab1:
        str_app.markdown("<h2 style='color: #ff5a00;'>👤 بياناتك الشخصية وموقعك الجغرافي</h2>", unsafe_allow_html=True)
        r_name = str_app.text_input("الاسم الكامل:", value=str_app.session_state.customer_name)
        r_phone = str_app.text_input("رقم الهاتف:", value=str_app.session_state.customer_phone)
        r_address = str_app.text_area("العنوان بالتفصيل:", value=str_app.session_state.customer_address)
        
        str_app.markdown("#### 📍 تحديد الموقع الجغرافي (GPS) تلقائياً")
        geo_html = """
        <div style="padding: 10px; background: #e3f2fd; border-radius: 8px; text-align: center;">
            <button onclick="getLocation()" style="background-color: #1976d2; color: white; padding: 10px 20px; border-radius: 6px; cursor: pointer;">📍 حدد موقعي الحالي</button>
            <p id="geo_status" style="margin-top: 8px; font-weight: bold; color: #388e3c;"></p>
        </div>
        <script>
        function getLocation() {
            var status = document.getElementById("geo_status");
            if (navigator.geolocation) {
                status.innerHTML = "جاري التحديد...";
                navigator.geolocation.getCurrentPosition(function(position) {
                    status.innerHTML = "✅ تم! (خط العرض: " + position.coords.latitude.toFixed(5) + ", خط الطول: " + position.coords.longitude.toFixed(5) + ")";
                });
            } else { status.innerHTML = "المتصفح لا يدعم الموقع."; }
        }
        </script>
        """
        components.html(geo_html, height=90)
        
        cl1, cl2 = str_app.columns(2)
        r_lat = cl1.number_input("خط العرض (Lat):", value=str_app.session_state.lat, format="%.6f")
        r_lon = cl2.number_input("خط الطول (Lon):", value=str_app.session_state.lon, format="%.6f")
            
        if str_app.button("حفظ بياناتي 🚀"):
            if r_name.strip() and r_phone.strip():
                c.execute("INSERT OR REPLACE INTO customers (phone, name, address, lat, lon) VALUES (?, ?, ?, ?, ?)", (r_phone, r_name, r_address, r_lat, r_lon))
                conn.commit()
                str_app.session_state.update({"customer_name": r_name, "customer_phone": r_phone, "customer_address": r_address, "lat": r_lat, "lon": r_lon})
                str_app.success("✅ تم حفظ بياناتك بنجاح! انتقل الآن لتبويب (تصفح المتاجر والأصناف).")
            else:
                str_app.error("يرجى إدخال الاسم ورقم الهاتف على الأقل.")

    with cust_tab2:
        str_app.markdown("### 🔥 العروض والمتاجر المتاحة")
        c.execute("SELECT DISTINCT category FROM stores")
        categories_list = ["الكل"] + [row[0] for row in c.fetchall()]
        
        cols_cat = str_app.columns(len(categories_list) if categories_list else 1)
        for idx, cat_name in enumerate(categories_list):
            with cols_cat[idx % len(cols_cat)]:
                if str_app.button(cat_name, key=f"cat_{idx}"):
                    str_app.session_state.selected_category = cat_name

        sel_cat = str_app.session_state.selected_category
        c.execute("SELECT name, category, delivery_time, delivery_fee, image_url FROM stores" if sel_cat == "الكل" else "SELECT name, category, delivery_time, delivery_fee, image_url FROM stores WHERE category = ?", () if sel_cat == "الكل" else (sel_cat,))
        stores_list = c.fetchall()
        
        if not stores_list: str_app.info("لا توجد متاجر هنا.")
        st_cols = str_app.columns(2)
        for idx, (s_name, s_cat, s_time, s_fee, s_img) in enumerate(stores_list):
            with st_cols[idx % 2]:
                str_app.markdown("<div class='talabat-card'>", unsafe_allow_html=True)
                if s_img and os.path.exists(s_img):
                    str_app.image(s_img, width=120)
                else:
                    str_app.markdown("<h1 style='text-align: center; margin:0;'>🏪</h1>", unsafe_allow_html=True)
                
                str_app.markdown(f"<h3 style='color:#111; margin:10px 0 5px 0; font-weight:bold;'>{s_name}</h3>", unsafe_allow_html=True)
                str_app.markdown(f"<p style='color:gray; font-size:13px; margin:2px 0;'>🏷️ القسم: {s_cat} | ⏱ مدة التوصيل: {s_time} | 🚚 التوصيل: {s_fee} د.أ</p>", unsafe_allow_html=True)
                
                if str_app.button(f"تصفح متجر {s_name} 🛒", key=f"go_store_{idx}"):
                    str_app.session_state.active_store = s_name
                    str_app.success(f"تم اختيار متجر '{s_name}'! انتقل الآن لتبويب (السلة ودفع الفاتورة).")
                str_app.markdown("</div>", unsafe_allow_html=True)

    with cust_tab3:
        str_app.markdown("### 🛒 المنتجات والأصناف المتاحة للطلب")
        c.execute("SELECT name FROM stores")
        all_st_names = [s[0] for s in c.fetchall()]
        act_st = str_app.session_state.get("active_store", all_st_names[0] if all_st_names else "")
        chosen_store = str_app.selectbox("اختر المتجر أو المطعم للتسوق منه:", all_st_names, index=all_st_names.index(act_st) if act_st in all_st_names else 0)
        
        if chosen_store:
            c.execute("SELECT id, item_name, price, unit_type, description, image_url FROM products WHERE store_name = ?", (chosen_store,))
            prods = c.fetchall()
            if not prods:
                str_app.info("لا توجد أصناف مضافة لهذا المتجر بعد.")
            for pid, pname, pprice, punit, pdesc, pimg in prods:
                str_app.markdown("<div class='talabat-card'>", unsafe_allow_html=True)
                if pimg and os.path.exists(pimg):
                    str_app.image(pimg, width=100)
                
                str_app.markdown(f"<h3 style='color:#111; margin:10px 0 5px 0; font-weight:bold;'>{pname}</h3>", unsafe_allow_html=True)
                str_app.markdown(f"<p style='color:#ff5a00; font-weight:bold; font-size:16px; margin:2px 0;'>السعر: {pprice} د.أ ({punit})</p>", unsafe_allow_html=True)
                if pdesc:
                    str_app.markdown(f"<p style='color:#555; font-size:13px; margin:5px 0;'>{pdesc}</p>", unsafe_allow_html=True)
                
                qty = str_app.number_input(f"حدد الكمية لـ {pname}", min_value=0.0, step=1.0, key=f"q_{pid}")
                if str_app.button(f"أضف '{pname}' إلى السلة 🛒", key=f"add_{pid}"):
                    if qty > 0:
                        c.execute("INSERT INTO cart (customer_phone, store_name, item_name, price, qty, total) VALUES (?, ?, ?, ?, ?, ?)", (str_app.session_state.customer_phone, chosen_store, pname, pprice, qty, qty*pprice))
                        conn.commit()
                        str_app.success(f"✅ تمت إضافة {qty} من '{pname}' إلى سلتك بنجاح!")
                    else:
                        str_app.warning("يرجى تحديد الكمية أولاً.")
                str_app.markdown("</div>", unsafe_allow_html=True)
            
            str_app.markdown("---")
            str_app.markdown("### 🛍️ محتويات سلة طلباتك الحالية:")
            c.execute("SELECT id, item_name, qty, total FROM cart WHERE customer_phone = ?", (str_app.session_state.customer_phone,))
            cart_items = c.fetchall()
            sub_tot = 0
            for cid, citem, cqty, ctot in cart_items:
                sub_tot += ctot
                str_app.write(f"• {citem} (الكمية: {cqty}) = {ctot} د.أ")
                if str_app.button("حذف الصنف ❌", key=f"del_{cid}"):
                    c.execute("DELETE FROM cart WHERE id = ?", (cid,))
                    conn.commit()
                    str_app.rerun()
            
            if cart_items:
                str_app.markdown(f"#### 💰 إجمالي المشتريات: `{sub_tot} د.أ` (يضاف رسوم التوصيل 1.5 د.أ عند الإرسال).")
                
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
                        
                        wa_msg = f"طلب جديد #{new_o_id}%0aالزبون: {str_app.session_state.customer_name}%0aالهاتف: {str_app.session_state.customer_phone}%0aالعنوان: {str_app.session_state.customer_address}%0aالمتجر: {chosen_store}%0aالمطلوب: {items_str}%0aالإجمالي: {grand_tot} د.أ%0aالدفع: {pay_method}"
                        wa_url = f"https://api.whatsapp.com/send?phone=962797088219&text={wa_msg}"
                        str_app.markdown(f"<a href='{wa_url}' target='_blank' style='background-color:#25d366; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold; display:inline-block;'>📤 اضغط هنا لإرسال الطلب عبر الواتساب للإدارة/المتجر</a>", unsafe_allow_html=True)
                    else:
                        str_app.error("يرجى إكمال بياناتك الشخصية أولاً من تبويب (بياناتي الشخصية وموقعي).")

    with cust_tab4:
        str_app.markdown("### 🚚 تتبع الطلبات الحالية")
        ph = str_app.text_input("أدخل رقم هاتفك لعرض طلباتك وتتبعها:", value=str_app.session_state.customer_phone)
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
    sel_store = str_app.selectbox("اختر متجرك:", st_names)
    st_pin = str_app.text_input("أدخل الرمز السري للمتجر:", type="password")
    
    if st_pin:
        c.execute("SELECT pin_code FROM stores WHERE name = ?", (sel_store,))
        row_pin = c.fetchone()
        if row_pin and st_pin == row_pin[0]:
            str_app.success(f"تم الدخول لمتجر {sel_store} بنجاح.")
            
            st_tab1, st_tab2, st_tab3 = str_app.tabs([
                "📦 طلبات المتجر الواردة", 
                "➕ إضافة أصناف جديدة والأسعار", 
                "✏️ تعديل أو حذف الأصناف الحالية"
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
                str_app.markdown("### ➕ إضافة صنف جديد مع السعر والوصف لمتجرك:")
                with str_app.form("add_product_form"):
                    p_name = str_app.text_input("اسم الصنف (مثال: مندي لحم، بيبسي):")
                    p_cat = str_app.text_input("تصنيف الصنف (مثال: وجبات، مشروبات):")
                    p_price = str_app.number_input("السعر (د.أ):", value=1.00, step=0.25)
                    p_unit = str_app.text_input("نوع الوحدة (مثال: وجبة، كيس، لتر، باكيت):", value="وجبة")
                    p_desc = str_app.text_area("وصف الصنف:")
                    p_age = str_app.checkbox("صنف مقيد العمر (19+ مثل الدخان)?")
                    p_disc = str_app.number_input("نسبة الخصم % (إن وجد):", min_value=0, max_value=100, value=0)
                    
                    uploaded_prod_img = str_app.file_uploader("اختر صورة الصنف:", type=["png", "jpg", "jpeg"])
                    
                    if str_app.form_submit_button("إضافة الصنف للمتجر 🚀"):
                        if p_name.strip():
                            img_path = save_uploaded_file(uploaded_prod_img)
                            c.execute("INSERT INTO products (store_name, category, item_name, description, price, unit_type, image_url, age_restricted, discount_percent) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                      (sel_store, p_cat, p_name.strip(), p_desc, p_price, p_unit, img_path, 1 if p_age else 0, p_disc))
                            conn.commit()
                            str_app.success(f"✅ تم إضافة الصنف '{p_name}' بسعر {p_price} د.أ بنجاح لقائمة متجرك!")
                        else:
                            str_app.error("يرجى إدخال اسم الصنف على الأقل.")

            with st_tab3:
                str_app.markdown("### ✏️ تعديل أو حذف الأصناف الحالية في متجرك:")
                c.execute("SELECT id, item_name, price, unit_type FROM products WHERE store_name = ?", (sel_store,))
                store_prods = c.fetchall()
                if not store_prods:
                    str_app.info("لا توجد أصناف مسجلة لمتجرك حالياً.")
                else:
                    prod_map = {f"{p[1]} ({p[2]} د.أ)": p[0] for p in store_prods}
                    selected_p_str = str_app.selectbox("اختر الصنف للتعديل أو الحذف:", list(prod_map.keys()))
                    if selected_p_str:
                        p_id_to_edit = prod_map[selected_p_str]
                        c.execute("SELECT item_name, category, price, unit_type, description, discount_percent FROM products WHERE id = ?", (p_id_to_edit,))
                        p_info = c.fetchone()
                        
                        with str_app.form("edit_product_form"):
                            ep_name = str_app.text_input("اسم الصنف:", value=p_info[0])
                            ep_cat = str_app.text_input("التصنيف:", value=p_info[1])
                            ep_price = str_app.number_input("السعر (د.أ):", value=float(p_info[2]), step=0.25)
                            ep_unit = str_app.text_input("نوع الوحدة:", value=p_info[3])
                            ep_desc = str_app.text_area("الوصف:", value=p_info[4])
                            ep_disc = str_app.number_input("نسبة الخصم %:", value=int(p_info[5]), min_value=0, max_value=100)
                            
                            col_ep1, col_ep2 = str_app.columns(2)
                            with col_ep1:
                                save_ep = str_app.form_submit_button("💾 حفظ التعديلات")
                            with col_ep2:
                                del_ep = str_app.form_submit_button("🗑️ حذف الصنف نهائياً")
                                
                            if save_ep:
                                c.execute("UPDATE products SET item_name=?, category=?, price=?, unit_type=?, description=?, discount_percent=? WHERE id=?", 
                                          (ep_name, ep_cat, ep_price, ep_unit, ep_desc, ep_disc, p_id_to_edit))
                                conn.commit()
                                str_app.success("✅ تم تحديث الصنف بنجاح!")
                                str_app.rerun()
                                
                            if del_ep:
                                c.execute("DELETE FROM products WHERE id=?", (p_id_to_edit,))
                                conn.commit()
                                str_app.success("🗑️ تم حذف الصنف بنجاح!")
                                str_app.rerun()
        else:
            str_app.error("الرمز السري غير صحيح!")

# ==========================================
# 3. واجهة السائقين
# ==========================================
elif main_interface == "السائقين":
    str_app.markdown("<h3 style='color: #333;'>🛵 بوابة السائقين (الكباتن)</h3>", unsafe_allow_html=True)
    c.execute("SELECT name FROM drivers")
    drv_names = [d[0] for d in c.fetchall()]
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
            str_app.error("الرمز السري غير صحيح!")

# ==========================================
# 4. لوحة الإدارة (محدثة لتتضمن أيضاً تبويب لإدارة الأصناف والأسعار لأي متجر)
# ==========================================
elif main_interface == "الإدارة":
    str_app.markdown("<h3 style='color: #333;'>⚙️ لوحة الإدارة المركزية</h3>", unsafe_allow_html=True)
    admin_pass = str_app.text_input("أدخل كلمة مرور الإدارة:", type="password")
    
    if admin_pass == "1234":
        str_app.success("صلاحيات الإدارة مفعلة.")
        
        tab_ords, tab_manage_stores, tab_add_st, tab_admin_prods, tab_manage_drv, tab_add_dr, tab_excel, tab_qr = str_app.tabs([
            "📦 إدارة الطلبات وجرس التنبيه", 
            "🏪 تعديل/حذف المتاجر", 
            "➕ إضافة متجر (GPS)", 
            "🍔 إدارة أصناف المتاجر", 
            "🛵 تعديل/حذف السائقين", 
            "➕ إضافة سائق", 
            "📥 الاستيراد (Excel/CSV)", 
            "📱 QR Code"
        ])
        
        with tab_ords:
            str_app.markdown("### 🔔 الطلبات الواردة وجرس التنبيه الاحتياطي للتاجر والسائق")
            c.execute("SELECT id, customer_name, customer_phone, customer_address, store_name, items_desc, grand_total, order_status, assigned_driver FROM orders ORDER BY id DESC")
            all_ords = c.fetchall()
            
            new_cnt = sum(1 for o in all_ords if "جديد" in o[7])
            if new_cnt > 0:
                str_app.warning(f"🚨 يوجد ({new_cnt}) طلب جديد بانتظار الإدارة!")
                play_sound_alert()
                
            if not all_ords:
                str_app.info("لا توجد طلبات مسجلة حالياً.")
            else:
                c.execute("SELECT name, phone FROM stores")
                st_phones = {s[0]: s[1] for s in c.fetchall()}
                c.execute("SELECT name, phone FROM drivers")
                dr_phones = {d[0]: d[1] for d in c.fetchall()}
                
                for oid, cnam, cph, cadd, st_name, itm, tot, stat, drv in all_ords:
                    with str_app.expander(f"طلب #{oid} - الزبون: {cnam} ({st_name}) - الحالة: {stat}"):
                        str_app.write(f"📞 هاتف الزبون: {cph} | 📍 العنوان: {cadd}")
                        str_app.write(f"🛒 الأصناف: {itm}")
                        str_app.write(f"💰 المبلغ: {tot} د.أ | السائق: {drv}")
                        
                        col_b1, col_b2 = str_app.columns(2)
                        with col_b1:
                            if str_app.button(f"🔔 تشغيل جرس التنبيه للصوت للطلب #{oid}", key=f"bell_{oid}"):
                                play_sound_alert()
                        with col_b2:
                            st_ph = st_phones.get(st_name, "")
                            if st_ph:
                                st_wa_msg = f"تنبيه طلب جديد #{oid}%0aالزبون: {cnam}%0aالمطلوب: {itm}%0aالمبلغ: {tot} د.أ"
                                st_wa_url = f"https://api.whatsapp.com/send?phone={st_ph}&text={st_wa_msg}"
                                str_app.markdown(f"<a href='{st_wa_url}' target='_blank' style='background-color:#25d366; color:white; padding:6px 12px; border-radius:6px; text-decoration:none; font-size:13px; display:inline-block;'>📤 إرسال واتساب للتاجر</a>", unsafe_allow_html=True)
                            
                            if drv != "لم يُعين بعد":
                                dr_ph = dr_phones.get(drv, "")
                                if dr_ph:
                                    dr_wa_msg = f"تنبيه طلب توصيل #{oid}%0aالمتجر: {st_name}%0aالعنوان: {cadd}"
                                    dr_wa_url = f"https://api.whatsapp.com/send?phone={dr_ph}&text={dr_wa_msg}"
                                    str_app.markdown(f"<a href='{dr_wa_url}' target='_blank' style='background-color:#25d366; color:white; padding:6px 12px; border-radius:6px; text-decoration:none; font-size:13px; display:inline-block;'>📤 إرسال واتساب للسائق</a>", unsafe_allow_html=True)
                        
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
            str_app.markdown("### 🏪 تعديل أو حذف المتاجر الحالية")
            c.execute("SELECT name, category, phone, delivery_fee FROM stores")
            stores_db = c.fetchall()
            if not stores_db:
                str_app.info("لا توجد متاجر مسجلة.")
            else:
                st_names_list = [s[0] for s in stores_db]
                sel_edit_st = str_app.selectbox("اختر المتجر للتعديل أو الحذف:", st_names_list)
                if sel_edit_st:
                    c.execute("SELECT name, category, phone, pin_code, delivery_fee FROM stores WHERE name = ?", (sel_edit_st,))
                    st_data = c.fetchone()
                    with str_app.form("edit_st_form"):
                        e_name = str_app.text_input("اسم المتجر:", value=st_data[0])
                        e_cat = str_app.text_input("القسم:", value=st_data[1])
                        e_phone = str_app.text_input("رقم الهاتف:", value=st_data[2])
                        e_pin = str_app.text_input("الرمز السري:", value=st_data[3], type="password")
                        e_fee = str_app.number_input("رسوم التوصيل:", value=float(st_data[4]), step=0.25)
                        
                        col_es1, col_es2 = str_app.columns(2)
                        with col_es1:
                            upd_st = str_app.form_submit_button("حفظ التعديلات")
                        with col_es2:
                            del_st = str_app.form_submit_button("حذف المتجر نهائياً")
                            
                        if upd_st:
                            c.execute("UPDATE stores SET name=?, category=?, phone=?, pin_code=?, delivery_fee=? WHERE name=?", (e_name, e_cat, e_phone, e_pin, e_fee, sel_edit_st))
                            conn.commit()
                            str_app.success("تم تحديث المتجر بنجاح!")
                            str_app.rerun()
                        if del_st:
                            c.execute("DELETE FROM stores WHERE name=?", (sel_edit_st,))
                            c.execute("DELETE FROM products WHERE store_name=?", (sel_edit_st,))
                            conn.commit()
                            str_app.success("تم حذف المتجر بنجاح!")
                            str_app.rerun()

        with tab_add_st:
            str_app.markdown("### ➕ إضافة متجر جديد مع GPS وصورة")
            with str_app.form("new_st"):
                ns_name = str_app.text_input("اسم المتجر:")
                ns_cat = str_app.selectbox("القسم:", ["مطاعم", "بقالة", "حلويات", "صيدليات"])
                ns_phone = str_app.text_input("رقم الهاتف:")
                ns_pin = str_app.text_input("الرمز السري للمتجر:", type="password")
                uploaded_store_img = str_app.file_uploader("شعار المتجر:", type=["png", "jpg", "jpeg"])
                
                geo_st_html = """
                <div style="padding: 10px; background: #fff3e0; border-radius: 8px; text-align: center;">
                    <button onclick="getStoreLoc()" style="background-color: #f57c00; color: white; padding: 8px; border-radius: 6px; border:none;">📍 حدد موقع المتجر الحالي GPS</button>
                    <p id="st_geo_stat" style="margin-top: 5px; font-weight: bold; color: #e65100;"></p>
                </div>
                <script>
                function getStoreLoc() {
                    var status = document.getElementById("st_geo_stat");
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(function(pos) {
                            status.innerHTML = "✅ Lat: " + pos.coords.latitude.toFixed(5) + " | Lon: " + pos.coords.longitude.toFixed(5);
                        });
                    }
                }
                </script>
                """
                components.html(geo_st_html, height=75)
                
                cl1, cl2 = str_app.columns(2)
                ns_lat = cl1.number_input("خط العرض (Lat):", value=31.2842, format="%.6f")
                ns_lon = cl2.number_input("خط الطول (Lon):", value=35.7048, format="%.6f")
                ns_fee = str_app.number_input("رسوم التوصيل:", value=1.50)
                
                if str_app.form_submit_button("إضافة متجر جديد"):
                    if ns_name and ns_pin:
                        store_img_path = save_uploaded_file(uploaded_store_img)
                        c.execute("INSERT INTO stores (name, category, phone, pin_code, location, lat, lon, delivery_fee, image_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (ns_name, ns_cat, ns_phone, ns_pin, "الكرك", ns_lat, ns_lon, ns_fee, store_img_path))
                        conn.commit()
                        str_app.success("تم إضافة المتجر بنجاح!")
                    else:
                        str_app.error("يرجى إدخال اسم المتجر والرمز السري.")

        with tab_admin_prods:
            str_app.markdown("### 🍔 إدارة أصناف وأسعار المتاجر من لوحة الإدارة")
            c.execute("SELECT name FROM stores")
            all_st_list = [s[0] for s in c.fetchall()]
            if not all_st_list:
                str_app.info("لا توجد متاجر مضافة بعد.")
            else:
                chosen_admin_store = str_app.selectbox("اختر المتجر لإضافة أو تعديل أصنافه:", all_st_list, key="admin_st_sel")
                with str_app.form("admin_add_prod"):
                    ap_name = str_app.text_input("اسم الصنف:")
                    ap_cat = str_app.text_input("التصنيف:")
                    ap_price = str_app.number_input("السعر (د.أ):", value=1.00, step=0.25)
                    ap_unit = str_app.text_input("نوع الوحدة:", value="وجبة")
                    ap_desc = str_app.text_area("وصف الصنف:")
                    ap_img = str_app.file_uploader("صورة الصنف:", type=["png", "jpg", "jpeg"], key="admin_p_img")
                    
                    if str_app.form_submit_button("إضافة الصنف للمتجر 🚀"):
                        if ap_name.strip():
                            img_p = save_uploaded_file(ap_img)
                            c.execute("INSERT INTO products (store_name, category, item_name, description, price, unit_type, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                      (chosen_admin_store, ap_cat, ap_name.strip(), ap_desc, ap_price, ap_unit, img_p))
                            conn.commit()
                            str_app.success(f"✅ تمت إضافة الصنف '{ap_name}' لمتجر {chosen_admin_store} بنجاح!")

        with tab_manage_drv:
            str_app.markdown("### 🛵 تعديل أو حذف السائقين")
            c.execute("SELECT name, phone, vehicle_type, pin_code FROM drivers")
            dr_db = c.fetchall()
            if not dr_db:
                str_app.info("لا توجد سائقين.")
            else:
                dr_names_list = [d[0] for d in dr_db]
                sel_edit_dr = str_app.selectbox("اختر السائق للتعديل أو الحذف:", dr_names_list)
                if sel_edit_dr:
                    c.execute("SELECT name, phone, vehicle_type, pin_code FROM drivers WHERE name = ?", (sel_edit_dr,))
                    dr_data = c.fetchone()
                    with str_app.form("edit_dr_form"):
                        ed_name = str_app.text_input("اسم السائق:", value=dr_data[0])
                        ed_phone = str_app.text_input("رقم الهاتف:", value=dr_data[1])
                        ed_veh = str_app.text_input("نوع المركبة:", value=dr_data[2])
                        ed_pin = str_app.text_input("الرمز السري:", value=dr_data[3], type="password")
                        
                        col_ed1, col_ed2 = str_app.columns(2)
                        with col_ed1:
                            upd_dr = str_app.form_submit_button("حفظ التعديلات")
                        with col_ed2:
                            del_dr = str_app.form_submit_button("حذف السائق نهائياً")
                            
                        if upd_dr:
                            c.execute("UPDATE drivers SET name=?, phone=?, vehicle_type=?, pin_code=? WHERE name=?", (ed_name, ed_phone, ed_veh, ed_pin, sel_edit_dr))
                            conn.commit()
                            str_app.success("تم تحديث السائق بنجاح!")
                            str_app.rerun()
                        if del_dr:
                            c.execute("DELETE FROM drivers WHERE name=?", (sel_edit_dr,))
                            conn.commit()
                            str_app.success("تم حذف السائق بنجاح!")
                            str_app.rerun()

        with tab_add_dr:
            str_app.markdown("### ➕ إضافة سائق جديد")
            with str_app.form("new_dr"):
                nd_name = str_app.text_input("اسم السائق:")
                nd_phone = str_app.text_input("رقم الهاتف:")
                nd_pin = str_app.text_input("الرمز السري للسائق:", type="password")
                nd_veh = str_app.text_input("نوع المركبة:")
                if str_app.form_submit_button("إضافة سائق جديد"):
                    if nd_name and nd_pin:
                        c.execute("INSERT INTO drivers (name, phone, pin_code, vehicle_type) VALUES (?, ?, ?, ?)", (nd_name, nd_phone, nd_pin, nd_veh))
                        conn.commit()
                        str_app.success("تم إضافة السائق بنجاح!")

        with tab_excel:
            str_app.markdown("### 📥 الاستيراد الآلي للأصناف عبر ملف Excel / CSV")
            uploaded_csv = str_app.file_uploader("اختر ملف CSV:", type=["csv"])
            if uploaded_csv is not None:
                df = pd.read_csv(uploaded_csv)
                str_app.dataframe(df)
                str_app.success("تم قراءة الملف بنجاح!")

        with tab_qr:
            str_app.markdown("### 📱 توليد QR Code للمنصة")
            app_url = "https://wasel-talabat-karak.streamlit.app"
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={urllib.parse.quote(app_url)}"
            str_app.image(qr_url, caption="مسح الكود لفتح بوابة الكرك للطلبات")

conn.close()