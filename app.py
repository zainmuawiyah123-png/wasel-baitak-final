import base64
import os
import sqlite3
import time
import urllib.parse
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="بوابة الكرك للطلبات - Karak Gate", page_icon="🏰", layout="wide"
)

# ---------------------------------------------------------
# دوال نظام الصوت التلقائي والشاشة الترحيبية والتصميم
# ---------------------------------------------------------
def play_auto_sound():
  sound_html = """
        <audio autoplay style="display:none;">
            <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
        </audio>
    """
  components.html(sound_html, height=0, width=0)


st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    
    .stApp { background-color: #F8F9FA; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; direction: rtl; text-align: right; }
    
    .hero-banner {
        background: linear-gradient(135deg, #FF6600 0%, #FF8533 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(255, 102, 0, 0.3);
    }
    
    .categories-bar {
        display: flex;
        gap: 10px;
        overflow-x: auto;
        padding: 10px 0;
        margin-bottom: 20px;
    }
    
    .cat-pill {
        background: linear-gradient(135deg, #FF6600 0%, #FF8533 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 30px;
        font-weight: 700;
        font-size: 14px;
        white-space: nowrap;
        box-shadow: 0 3px 8px rgba(255, 102, 0, 0.3);
        text-align: center;
        display: inline-block;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# تهيئة قاعدة البيانات في مسار دائم ومستقر
# ---------------------------------------------------------
DB_PATH = "karak_talabat_secure.db"


def init_db():
  conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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
            phone TEXT DEFAULT '0797088219'
        )
    """)

  c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_name TEXT,
            item_name TEXT,
            price REAL,
            discount TEXT,
            quantity TEXT,
            unit TEXT,
            image_url TEXT
        )
    """)

  c.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT DEFAULT '0797088219',
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
  c.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_pass', '1234')"
  )
  c.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('store_pass', '5678')"
  )
  c.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('driver_pass',"
      " '1122')"
  )

  conn.commit()
  return conn, c


conn, c = init_db()


def get_setting(key):
  c.execute("SELECT value FROM settings WHERE key = ?", (key,))
  row = c.fetchone()
  return row[0] if row else ""


UPLOAD_DIR = os.path.abspath("uploads")
if not os.path.exists(UPLOAD_DIR):
  os.makedirs(UPLOAD_DIR)


def save_uploaded_image(uploaded_file):
  if uploaded_file is not None:
    safe_name = "".join(
        ch for ch in uploaded_file.name if ch.isalnum() or ch in ("_", ".", "-")
    )
    filename = f"{int(time.time())}_{safe_name}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
      f.write(uploaded_file.getbuffer())
    return file_path
  return ""


def render_image_safely(
    img_path, width="100%", height="120px", border_radius="8px"
):
  if img_path and os.path.exists(img_path):
    try:
      with open(img_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
        return f'<img src="data:image/jpeg;base64,{encoded}" style="width:{width}; height:{height}; object-fit:cover; border-radius:{border_radius}; border:1px solid #E5E7EB; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">'
    except Exception:
      pass
  return f'<div style="width:{width}; height:{height}; background:#E5E7EB; border-radius:{border_radius}; display:flex; align-items:center; justify-content:center; color:#6B7280; font-size:12px; text-align:center; border:1px dashed #D1D5DB;">بدون صورة</div>'


# إدارة الحالات الأساسية والجلسة
if "show_welcome" not in st.session_state:
  st.session_state["show_welcome"] = True

if "main_nav" not in st.session_state:
  st.session_state["main_nav"] = "الرئيسية"

if "cart_items" not in st.session_state:
  st.session_state["cart_items"] = []

if "cart_store" not in st.session_state:
  st.session_state["cart_store"] = ""

# ---------------------------------------------------------
# الشاشة الترحيبية الأولية
# ---------------------------------------------------------
if st.session_state["show_welcome"]:
  st.markdown(
      """
        <style>
        .stApp { background: linear-gradient(135deg, #FF6600 0%, #FF8533 100%) !important; }
        </style>
        <div style="text-align: center; padding: 80px 20px; color: white;">
            <h1 style="font-size: 48px; font-weight: bold; text-shadow: 0 2px 10px rgba(0,0,0,0.2);">🏰 بوابة الكرك للطلبات</h1>
            <h3 style="margin-top: 20px; font-size: 22px; font-weight: 500;">منصة التوصيل والخدمات الذكية الأولى في محافظة الكرك</h3>
            <p style="margin-top: 15px; font-size: 16px; opacity: 0.9;">جاري تحضير النظام والبوابات الذكية...</p>
        </div>
    """,
      unsafe_allow_html=True,
  )
  play_auto_sound()
  time.sleep(2)
  st.session_state["show_welcome"] = False
  st.rerun()

# ---------------------------------------------------------
# الواجهة الرئيسية والهيدر والشاشة الترحيبية الدائمة
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero-banner">
        <h1>بوابة الكرك للطلبات - Karak Gate</h1>
        <p style="margin-top: 8px; font-size: 18px; font-weight: 600;">منصة التوصيل والخدمات الذكية الأولى في محافظة الكرك</p>
    </div>
""",
    unsafe_allow_html=True,
)

# أزرار التنقل الرئيسية بالكامل
col_1, col_2, col_3, col_4, col_5 = st.columns(5)
with col_1:
  if st.button("الرئيسية", use_container_width=True):
    st.session_state["main_nav"] = "الرئيسية"
    st.rerun()
with col_2:
  if st.button("واجهة الزبائن", use_container_width=True):
    st.session_state["main_nav"] = "الزبائن"
    st.rerun()
with col_3:
  if st.button("واجهة المتاجر", use_container_width=True):
    st.session_state["main_nav"] = "المتاجر"
    st.rerun()
with col_4:
  if st.button("واجهة السائقين", use_container_width=True):
    st.session_state["main_nav"] = "السائقين"
    st.rerun()
with col_5:
  if st.button("الإدارة المركزية", use_container_width=True):
    st.session_state["main_nav"] = "الإدارة"
    st.rerun()

st.markdown("---")

# ---------------------------------------------------------
# الرئيسية
# ---------------------------------------------------------
if st.session_state["main_nav"] == "الرئيسية":
  st.markdown("### أقسام المنصة")
  st.markdown(
      """
        <div class="categories-bar">
            <div class="cat-pill">مطاعم</div>
            <div class="cat-pill">ماركت</div>
            <div class="cat-pill">حلويات</div>
            <div class="cat-pill">خضروات وفواكه</div>
            <div class="cat-pill">صيدليات ومستلزمات طبية</div>
            <div class="cat-pill">لحوم</div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown("### البحث السريع عن المتاجر والأصناف")
  search_query = st.text_input("ابحث عن وجبة، متجر، أو صنف...", "")

  st.markdown("### المتاجر والعروض المتاحة")
  query_str = "SELECT id, name, category, rating, delivery_time, delivery_fee, image_url, offer, lat, lon FROM stores"
  if search_query:
    query_str += f" WHERE name LIKE '%{search_query}%' OR category LIKE '%{search_query}%'"
  c.execute(query_str)
  stores_main = c.fetchall()

  if not stores_main:
    st.info("لا توجد متاجر مطابقة للبحث حالياً.")
  else:
    for store in stores_main:
      (
          s_id,
          s_name,
          s_cat,
          s_rating,
          s_time,
          s_fee,
          s_img,
          s_offer,
          s_lat,
          s_lon,
      ) = store
      col_img, col_det = st.columns([1, 5])
      with col_img:
        st.markdown(
            render_image_safely(
                s_img, width="95px", height="95px", border_radius="12px"
            ),
            unsafe_allow_html=True,
        )
      with col_det:
        st.markdown(
            f"#### {s_name}"
            " &nbsp;&nbsp;<span"
            " style='background:#FEF3C7;color:#D97706;padding:2px"
            f" 8px;border-radius:6px;font-size:14px;'>⭐ {s_rating}</span>",
            unsafe_allow_html=True,
        )
        st.write(
            f"التصنيف: {s_cat} | وقت التوصيل: {s_time} | أجور التوصيل: {s_fee}"
            f" | خريطة المتجر GPS: https://maps.google.com/?q={s_lat},{s_lon}"
        )
        st.markdown(
            f"<span style='color:#FF6600; font-weight:600;'>العرض:"
            f" {s_offer}</span>",
            unsafe_allow_html=True,
        )
      st.markdown("---")

# ---------------------------------------------------------
# 1. واجهة الزبائن
# ---------------------------------------------------------
elif st.session_state["main_nav"] == "الزبائن":
  st.subheader("بوابة الزبائن وتتبع الطلبات")

  cust_t1, cust_t2, cust_t3, cust_t4 = st.tabs([
      "بياناتك وتحديد الموقع",
      "تصفح المتاجر والأصناف",
      "السلة وتفاصيل الفاتورة",
      "تتبع رحلة الطلب",
  ])

  with cust_t1:
    st.markdown("#### تحديد موقعك الجغرافي الحالي تلقائياً")
    geo_html = """
        <div style="padding: 10px 0;">
            <button onclick="getLocation()" style="background-color: #FF6600; color: white; padding: 10px 20px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">📍 اضغط هنا لتحديد موقعي الحالي تلقائياً (GPS)</button>
            <p id="geo_status" style="margin-top: 8px; font-size: 14px; color: #555;"></p>
            <script>
            function getLocation() {
                const status = document.getElementById("geo_status");
                if (!navigator.geolocation) {
                    status.innerHTML = "خاصية تحديد الموقع غير مدعومة في متصفحك.";
                    return;
                }
                status.innerHTML = "جاري تحديد موقعك الحالي...";
                navigator.geolocation.getCurrentPosition((position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    status.innerHTML = "تم بنجاح! الإحداثيات المكتشفة: خط العرض " + lat.toFixed(4) + "، خط الطول " + lon.toFixed(4) + " (يرجى إدخالها أدناه وحفظ البيانات)";
                }, () => {
                    status.innerHTML = "تعذر الحصول على موقعك. يرجى السماح للمتصفح بالوصول للموقع.";
                });
            }
            </script>
        </div>
        """
    components.html(geo_html, height=100)

    with st.form("cust_form_auto"):
      c_name = st.text_input("الاسم الكامل:")
      c_phone = st.text_input("رقم الهاتف:", value="0797088219")
      c_address = st.text_area("العنوان بالتفصيل (مثل: الكرك، المرج، قرب...):")

      col_lat, col_lon = st.columns(2)
      with col_lat:
        c_lat = st.number_input(
            "خط العرض (Latitude)", value=31.1852, format="%.6f"
        )
      with col_lon:
        c_lon = st.number_input(
            "خط الطول (Longitude)", value=35.7048, format="%.6f"
        )

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
    st.markdown("### المتاجر والأصناف المتاحة")
    c.execute(
        "SELECT id, name, category, rating, delivery_time, delivery_fee,"
        " image_url, offer, lat, lon FROM stores"
    )
    stores = c.fetchall()
    for store in stores:
      (
          s_id,
          s_name,
          s_cat,
          s_rating,
          s_time,
          s_fee,
          s_img,
          s_offer,
          s_lat,
          s_lon,
      ) = store
      col_img, col_det = st.columns([1, 5])
      with col_img:
        st.markdown(
            render_image_safely(
                s_img, width="85px", height="85px", border_radius="10px"
            ),
            unsafe_allow_html=True,
        )
      with col_det:
        st.markdown(
            f"#### {s_name} (التقييم: {s_rating})", unsafe_allow_html=True
        )
        st.write(
            f"التصنيف: {s_cat} | وقت التوصيل: {s_time} | التوصيل: {s_fee}"
        )

      with st.expander(f"عرض أصناف وعروض {s_name}"):
        c.execute(
            "SELECT id, item_name, price, discount, quantity, unit, image_url"
            " FROM items WHERE TRIM(store_name) = TRIM(?)",
            (s_name,),
        )
        items = c.fetchall()
        if not items:
          st.info(
              f"لا توجد أصناف مضافة لهذا المتجر ({s_name}) بعد، أو تأكد من مطابقة"
              " اسم المتجر عند إضافة الصنف."
          )
        else:
          for itm in items:
            i_id, i_name, i_price, i_disc, i_qty, i_unit, i_img = itm
            col_i_img, col_it1, col_it2 = st.columns([1, 3, 1])
            with col_i_img:
              st.markdown(
                  render_image_safely(
                      i_img, width="60px", height="60px", border_radius="8px"
                  ),
                  unsafe_allow_html=True,
              )
            with col_it1:
              st.write(
                  f"• **{i_name}**\n- السعر: **{i_price} JD**\n- العرض:"
                  f" {i_disc}\n- المتوفر: {i_qty} {i_unit}"
              )
            with col_it2:
              if st.button("إضافة للسلة", key=f"btn_add_{s_id}_{i_id}"):
                if (
                    st.session_state["cart_store"]
                    and st.session_state["cart_store"] != s_name
                ):
                  st.session_state["cart_items"] = []
                st.session_state["cart_store"] = s_name
                st.session_state["cart_items"].append({
                    "name": i_name,
                    "price": i_price,
                    "store": s_name,
                })
                st.success("تمت الإضافة للسلة!")
                st.rerun()
            st.markdown("---")
      st.markdown("---")

  with cust_t3:
    st.markdown("### السلة وتفاصيل الفاتورة الشفافة")
    cart_items = st.session_state.get("cart_items", [])
    cart_store = st.session_state.get("cart_store", "")

    if not cart_items:
      st.info("السلة فارغة.")
    else:
      st.write(f"المتجر: **{cart_store}**")
      subtotal = sum(item["price"] for item in cart_items)
      for idx, c_itm in enumerate(cart_items):
        st.write(f"• {c_itm['name']} — {c_itm['price']} JD")

      delivery_fee_val = 0.75
      service_fee = 0.25
      total_bill = subtotal + delivery_fee_val + service_fee

      st.markdown(
          f"""
            <div style="background:#F3F4F6; padding:15px; border-radius:10px; margin:10px 0; border: 1px solid #E5E7EB;">
                <b>تفاصيل الفاتورة:</b><br>
                • مجموع المنتجات: <b>{subtotal:.2f} JD</b><br>
                • أجور التوصيل: <b>{delivery_fee_val:.2f} JD</b><br>
                • رسوم الخدمة: <b>{service_fee:.2f} JD</b><br>
                <hr style="margin:8px 0;">
                <b>المجموع الكلي النهائي: <span style="color:#FF6600; font-size:18px;">{total_bill:.2f} JD</span></b>
            </div>
            """,
          unsafe_allow_html=True,
      )

      with st.form("payment_form_final"):
        pay_choice = st.radio(
            "طريقة الدفع:",
            ["نقداً عند الاستلام", "تحويل كليك (CliQ) - 0797088219"],
        )
        if st.form_submit_button("إرسال الطلب نهائياً"):
          client = st.session_state.get(
              "client_info",
              {
                  "name": "زبون الكرك",
                  "phone": "0797088219",
                  "address": "الكرك",
                  "lat": 31.185,
                  "lon": 35.705,
              },
          )
          items_description = ", ".join(
              [f"{i['name']} ({i['price']} JD)" for i in cart_items]
          )
          c.execute(
              """INSERT INTO orders (store_name, customer_name, phone, address, items_desc, payment_method, total_price, status, cust_lat, cust_lon) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (
                  cart_store,
                  client["name"],
                  client["phone"],
                  client["address"],
                  items_description,
                  pay_choice,
                  total_bill,
                  "قيد المعالجة",
                  client["lat"],
                  client["lon"],
              ),
          )
          conn.commit()
          st.success("تم إرسال الطلب بنجاح!")

          wa_client_msg = (
              f"تأكيد طلب من بوابة الكرك:\nالمتجر: {cart_store}\nالمنتجات:"
              f" {items_description}\nالمجموع الكلي: {total_bill:.2f} JD\nاسم"
              f" الزبون: {client['name']} - هاتف: {client['phone']}"
          )
          encoded_client_wa = urllib.parse.quote(wa_client_msg)
          whatsapp_btn_html = (
              f'<a href="https://wa.me/962797088219?text={encoded_client_wa}"'
              ' target="_blank" style="background:#25D366; color:white;'
              ' padding:10px 18px; border-radius:8px; text-decoration:none;'
              ' font-weight:bold; display:inline-block; margin-top:10px;">إرسال'
              ' تفاصيل الطلب عبر واتساب 0797088219</a>'
          )
          st.markdown(whatsapp_btn_html, unsafe_allow_html=True)

          st.session_state["cart_items"] = []
          st.session_state["cart_store"] = ""

  with cust_t4:
    st.markdown("### تتبع رحلة الطلب من المتجر وحتى الاستلام")
    c.execute("""SELECT o.id, o.store_name, o.status, s.lat, s.lon, o.cust_lat, o.cust_lon 
                 FROM orders o LEFT JOIN stores s ON o.store_name = s.name""")
    orders_track = c.fetchall()
    if not orders_track:
      st.info("لا توجد طلبات نشطة حالياً للتتبع.")
    for tr in orders_track:
      t_id, t_store, t_status, s_lat, s_lon, c_lat, c_lon = tr
      if not s_lat:
        s_lat, s_lon = 31.1852, 35.7048
      st.markdown(
          f"""
            <div style="background:white; padding:12px; border-radius:8px; border:1px solid #ddd; margin-bottom:10px;">
                <b>طلب #{t_id} — المتجر: {t_store}</b><br>
                الحالة: <span style="color:#FF6600;">{t_status}</span><br>
                <b>مسار الرحلة (GPS):</b><br>
                &nbsp;&nbsp;• موقع انطلاق المتجر: https://maps.google.com/?q={s_lat},{s_lon} ➔ موقع التوصيل للزبون: https://maps.google.com/?q={c_lat},{c_lon}
            </div>
            """,
          unsafe_allow_html=True,
      )

# ---------------------------------------------------------
# 2. واجهة المتاجر
# ---------------------------------------------------------
elif st.session_state["main_nav"] == "المتاجر":
  st.subheader("واجهة المتاجر والطلبات الواردة")

  store_pass_input = st.text_input(
      "أدخل كلمة سر لوحة المتاجر:", type="password", key="store_login_pass"
  )
  if store_pass_input == get_setting("store_pass"):
    play_auto_sound()
    st.success("تم تسجيل الدخول بنجاح! (تم تفعيل جرس التنبيه تلقائياً)")

    c.execute(
        "SELECT id, store_name, items_desc, status, total_price FROM orders"
    )
    for os_item in c.fetchall():
      st.markdown(
          f"""
            <div style="background:#FFF; padding:12px; border-radius:8px; border:1px solid #ddd; margin-bottom:10px;">
                <b>طلب رقم #{os_item[0]}</b> | المتجر: {os_item[1]}<br>
                <b>الطلب:</b> {os_item[2]} | المجموع: {os_item[4]} JD<br>
                الحالة: <b>{os_item[3]}</b>
            </div>
            """,
          unsafe_allow_html=True,
      )
  elif store_pass_input != "":
    st.error("كلمة السر خاطئة!")

# ---------------------------------------------------------
# 3. واجهة السائقين
# ---------------------------------------------------------
elif st.session_state["main_nav"] == "السائقين":
  st.subheader("واجهة السائقين وعمليات التوصيل")

  drv_pass_input = st.text_input(
      "أدخل كلمة سر لوحة السائقين:", type="password", key="drv_login_pass"
  )
  if drv_pass_input == get_setting("driver_pass"):
    play_auto_sound()
    st.success("تم تسجيل الدخول بنجاح! (تم تفعيل جرس التنبيه تلقائياً)")

    c.execute("""SELECT o.id, o.store_name, o.customer_name, o.phone, o.address, o.status, o.total_price, o.items_desc, s.lat, s.lon, o.cust_lat, o.cust_lon 
                 FROM orders o LEFT JOIN stores s ON o.store_name = s.name""")
    deliveries = c.fetchall()
    if not deliveries:
      st.info("لا توجد طلبات توصيل متاحة حالياً.")
    for do in deliveries:
      (
          d_id,
          d_store,
          d_cust,
          d_phone,
          d_addr,
          d_status,
          d_total,
          d_items,
          s_lat,
          s_lon,
          c_lat,
          c_lon,
      ) = do
      if s_lat is None:
        s_lat, s_lon = 31.1852, 35.7048

      st.markdown(
          f"""
            <div style="background:#FFF; padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px;">
                <b>طلب توصيل رقم #{d_id}</b><br>
                المتجر: {d_store} | الزبون: {d_cust} (هاتف: {d_phone})<br>
                العنوان: {d_addr}<br>
                التفاصيل: {d_items}<br>
                <b>قيمة الحساب الإجمالية للتحصيل نقداً: <span style="color:#FF6600;">{d_total:.2f} JD</span></b><br>
                الحالة: <b>{d_status}</b><br>
                موقع المتجر للاستلام: https://maps.google.com/?q={s_lat},{s_lon} ➔ موقع الزبون للتسليم: https://maps.google.com/?q={c_lat},{c_lon}
            </div>
            """,
          unsafe_allow_html=True,
      )

      if st.button(
          f"تحديث الطلب #{d_id} إلى 'تم التوصيل بنجاح'", key=f"d_up_btn_{d_id}"
      ):
        c.execute(
            "UPDATE orders SET status = 'تم التوصيل بنجاح' WHERE id = ?",
            (d_id,),
        )
        conn.commit()
        st.success("تم التحديث!")
        st.rerun()
  elif drv_pass_input != "":
    st.error("كلمة السر خاطئة!")

# ---------------------------------------------------------
# 4. الإدارة المركزية
# ---------------------------------------------------------
elif st.session_state["main_nav"] == "الإدارة":
  st.subheader("لوحة الإدارة المركزية والتحكم الشامل")

  admin_pass_input = st.text_input(
      "أدخل كلمة سر لوحة الإدارة:", type="password", key="adm_login_pass"
  )
  if admin_pass_input == get_setting("admin_pass"):
    play_auto_sound()
    st.success("تم تسجيل الدخول بنجاح. (تم تفعيل جرس التنبيه تلقائياً)")

    adm_t1, adm_t2, adm_t3, adm_t4, adm_t5, adm_t6, adm_t7 = st.tabs([
        "الطلبات وواتساب التأكيد",
        "التقرير المالي اليومي",
        "إضافة وتعديل وحذف تاجر",
        "إضافة وتعديل وحذف صنف",
        "إدارة السائقين",
        "كلمات السر",
        "قاعدة البيانات",
    ])

    with adm_t1:
      c.execute(
          "SELECT id, store_name, customer_name, total_price, status,"
          " items_desc, phone FROM orders"
      )
      orders_adm = c.fetchall()
      if not orders_adm:
        st.info("لا توجد طلبات.")
      for ao in orders_adm:
        st.write(
            f"طلب #{ao[0]} | المتجر: {ao[1]} | الزبون: {ao[2]} | المجموع:"
            f" {ao[3]} JD | الحالة: {ao[4]}"
        )

        wa_text = (
            f"إشعار رسمي من بوابة الكرك (رقم الإرسال: 0797088219):\nطلب جديد"
            f" #{ao[0]}\nالمتجر: {ao[1]}\nالمنتجات: {ao[5]}\nالمجموع المطلوب:"
            f" {ao[3]} JD\nيرجى الجاهزية الفورية للتوصيل!"
        )
        encoded_wa = urllib.parse.quote(wa_text)
        whatsapp_adm_btn = (
            f'<a href="https://wa.me/962797088219?text={encoded_wa}"'
            ' target="_blank" style="background:#25D366; color:white; padding:6px'
            ' 12px; border-radius:5px; text-decoration:none; font-size:13px;'
            ' display:inline-block; margin-bottom:5px;">إرسال واتساب تأكيد للطلب'
            ' عبر الرقم 0797088219</a>'
        )
        st.markdown(whatsapp_adm_btn, unsafe_allow_html=True)

        if st.button(f"تأكيد الطلب #{ao[0]}", key=f"adm_cnf_btn_{ao[0]}"):
          c.execute(
              "UPDATE orders SET status = 'تم التأكيد وجاري التجهيز' WHERE id"
              " = ?",
              (ao[0],),
          )
          conn.commit()
          st.rerun()
        st.markdown("---")

    with adm_t2:
      st.markdown("### 📊 التقرير المالي اليومي الشامل")
      c.execute(
          "SELECT id, store_name, customer_name, total_price, payment_method,"
          " status FROM orders"
      )
      all_orders_fin = c.fetchall()

      total_orders_count = len(all_orders_fin)
      total_revenue = sum(o[3] for o in all_orders_fin) if all_orders_fin else 0.0

      col_f1, col_f2 = st.columns(2)
      with col_f1:
        st.metric(
            label="إجمالي عدد الطلبات المسجلة", value=total_orders_count
        )
      with col_f2:
        st.metric(
            label="إجمالي العائدات المالية اليومية",
            value=f"{total_revenue:.2f} JD",
        )

      st.markdown("---")
      st.markdown("#### تفاصيل العمليات والمدفوعات اليومية:")
      if not all_orders_fin:
        st.info("لا توجد بيانات مالية مسجلة لعرضها اليوم.")
      else:
        for f_item in all_orders_fin:
          st.write(
              f"• **طلب #{f_item[0]}** | المتجر: {f_item[1]} | الزبون:"
              f" {f_item[2]} | القيمة: **{f_item[3]:.2f} JD** | طريقة الدفع:"
              f" {f_item[4]} | الحالة: {f_item[5]}"
          )

    with adm_t3:
      st.markdown("### إضافة تاجر جديد")
      so_name = st.text_input("اسم المحل أو المتجر:", key="adm_so_name")
      so_cat = st.selectbox(
          "التصنيف:",
          [
              "مطاعم",
              "ماركت",
              "حلويات",
              "خضروات وفواكه",
              "صيدليات ومستلزمات طبية",
              "لحوم",
          ],
          key="adm_so_cat",
      )
      so_time = st.text_input(
          "وقت التوصيل:", value="20-30 دقيقة", key="adm_so_time"
      )
      so_fee = st.text_input("رسوم التوصيل:", value="0.75 دينار", key="adm_so_fee")
      so_offer = st.text_input(
          "العرض الخاص:", value="عرض مميز", key="adm_so_offer"
      )
      so_img_file = st.file_uploader(
          "صورة المتجر:", type=["jpg", "jpeg", "png"], key="adm_store_file_up"
      )
      if st.button("حفظ المتجر الجديد"):
        if so_name:
          img_p = save_uploaded_image(so_img_file)
          c.execute(
              "INSERT INTO stores (name, category, delivery_time,"
              " delivery_fee, offer, image_url) VALUES (?, ?, ?, ?, ?, ?)",
              (so_name, so_cat, so_time, so_fee, so_offer, img_p),
          )
          conn.commit()
          st.success("تمت إضافة المتجر بنجاح!")
          st.rerun()

      st.markdown("---")
      st.markdown("### تعديل أو حذف تاجر موجود")
      c.execute("SELECT id, name FROM stores")
      stores_mod = c.fetchall()
      if stores_mod:
        st_sel_mod = st.selectbox(
            "اختر المتجر للتعديل أو الحذف:", stores_mod, format_func=lambda x: x[1]
        )
        if st_sel_mod:
          c.execute(
              "SELECT name, delivery_fee, offer FROM stores WHERE id = ?",
              (st_sel_mod[0],),
          )
          curr_st_data = c.fetchone()
          new_st_name = st.text_input(
              "اسم المتجر المعدل:", value=curr_st_data[0], key="mod_st_n"
          )
          new_st_fee = st.text_input(
              "أجور التوصيل:", value=curr_st_data[1], key="mod_st_f"
          )
          new_st_offer = st.text_input(
              "العرض:", value=curr_st_data[2], key="mod_st_o"
          )
          col_m1, col_m2 = st.columns(2)
          with col_m1:
            if st.button("حفظ تعديلات المتجر"):
              c.execute(
                  "UPDATE stores SET name = ?, delivery_fee = ?, offer = ? WHERE"
                  " id = ?",
                  (new_st_name, new_st_fee, new_st_offer, st_sel_mod[0]),
              )
              conn.commit()
              st.success("تم التحديث!")
              st.rerun()
          with col_m2:
            if st.button("حذف هذا التاجر نهائياً"):
              c.execute("DELETE FROM stores WHERE id = ?", (st_sel_mod[0],))
              conn.commit()
              st.success("تم حذف التاجر!")
              st.rerun()

    with adm_t4:
      st.markdown("### إضافة صنف جديد للمتاجر")
      c.execute("SELECT name FROM stores")
      st_list = [r[0] for r in c.fetchall()]
      if st_list:
        sel_st_item = st.selectbox(
            "اختر المتجر لصنف الصنف:", st_list, key="adm_sel_st_item"
        )
        itm_name = st.text_input("اسم الصنف أو الوجبة:", key="adm_itm_name")
        itm_price = st.number_input(
            "السعر بالدينار:", value=2.0, step=0.25, key="adm_itm_price"
        )
        itm_disc = st.text_input(
            "العرض أو الخصم:", value="بدون خصم", key="adm_itm_disc"
        )
        itm_qty = st.text_input("الكمية المتوفرة:", value="10", key="adm_itm_qty")
        itm_unit = st.selectbox(
            "وحدة الكمية:",
            ["حبة", "كيلو", "باكيت", "صندوق", "وجبة", "لتر"],
            key="adm_itm_unit",
        )
        itm_img = st.file_uploader(
            "صورة الصنف:", type=["jpg", "jpeg", "png"], key="adm_item_file_up"
        )
        if st.button("إضافة الصنف للمتجر عبر الإدارة"):
          if itm_name:
            img_ip = save_uploaded_image(itm_img)
            c.execute(
                "INSERT INTO items (store_name, item_name, price, discount,"
                " quantity, unit, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    sel_st_item,
                    itm_name,
                    itm_price,
                    itm_disc,
                    itm_qty,
                    itm_unit,
                    img_ip,
                ),
            )
            conn.commit()
            st.success("تمت إضافة الصنف بنجاح!")
            st.rerun()

      st.markdown("---")
      st.markdown("### تعديل أو حذف صنف موجود")
      c.execute(
          "SELECT id, store_name, item_name, price, quantity, unit FROM items"
      )
      items_all = c.fetchall()
      if not items_all:
        st.info("لا توجد أصناف مضافة.")
      else:
        sel_itm_mod = st.selectbox(
            "اختر الصنف للتعديل/الحذف:",
            items_all,
            format_func=lambda x: f"{x[1]} ➔ {x[2]} ({x[3]} JD)",
        )
        if sel_itm_mod:
          new_i_name = st.text_input(
              "اسم الصنف المعدل:", value=sel_itm_mod[2], key="mod_i_n"
          )
          new_i_price = st.number_input(
              "السعر المعدل:",
              value=sel_itm_mod[3],
              step=0.25,
              key="mod_i_p",
          )
          new_i_qty = st.text_input(
              "الكمية المعدلة:", value=sel_itm_mod[4], key="mod_i_q"
          )
          col_ti1, col_ti2 = st.columns(2)
          with col_ti1:
            if st.button("حفظ تعديل الصنف"):
              c.execute(
                  "UPDATE items SET item_name = ?, price = ?, quantity = ? WHERE"
                  " id = ?",
                  (new_i_name, new_i_price, new_i_qty, sel_itm_mod[0]),
              )
              conn.commit()
              st.success("تم تعديل الصنف بنجاح!")
              st.rerun()
          with col_ti2:
            if st.button("حذف هذا الصنف نهائياً"):
              c.execute("DELETE FROM items WHERE id = ?", (sel_itm_mod[0],))
              conn.commit()
              st.success("تم حذف الصنف!")
              st.rerun()

    with adm_t5:
      st.markdown("### إدارة السائقين")
      d_name = st.text_input("اسم السائق:")
      d_phone = st.text_input("رقم الهاتف:", value="0797088219")
      d_veh = st.text_input("نوع المركبة:", value="سكوتر")
      if st.button("حفظ السائق الجديد"):
        if d_name:
          c.execute(
              "INSERT INTO drivers (name, phone, vehicle) VALUES (?, ?, ?)",
              (d_name, d_phone, d_veh),
          )
          conn.commit()
          st.success("تمت إضافة السائق!")
          st.rerun()

    with adm_t6:
      with st.form("change_pass_form"):
        new_adm = st.text_input(
            "كلمة سر الإدارة الجديدة:", value=get_setting("admin_pass")
        )
        new_str = st.text_input(
            "كلمة سر المتاجر الجديدة:", value=get_setting("store_pass")
        )
        new_drv = st.text_input(
            "كلمة سر السائقين الجديدة:", value=get_setting("driver_pass")
        )
        if st.form_submit_button("تحديث كلمات السر"):
          c.execute(
              "UPDATE settings SET value = ? WHERE key = 'admin_pass'",
              (new_adm,),
          )
          c.execute(
              "UPDATE settings SET value = ? WHERE key = 'store_pass'",
              (new_str,),
          )
          c.execute(
              "UPDATE settings SET value = ? WHERE key = 'driver_pass'",
              (new_drv,),
          )
          conn.commit()
          st.success("تم التحديث!")

    with adm_t7:
      if st.button("حذف جميع الطلبات وتصفير النظام"):
        c.execute("DELETE FROM orders")
        conn.commit()
        st.success("تم التصفير!")
        st.rerun()

  elif admin_pass_input != "":
    st.error("كلمة سر الإدارة غير صحيحة!")