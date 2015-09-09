#
# developed by Sergey Markelov (2013)
#

import random

BING_URL = 'http://www.bing.com'

# common headers for all requests
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-us,en;q=0.5",
    "Accept-Charset": "utf-8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

class UserAgents:
    @staticmethod
    def generate(account):
        userAgents = UserAgents

        if hasattr(account, "ua_desktop"):
            userAgents.pc = account.ua_desktop
        else:
            userAgents.pc = random.choice(USER_AGENTS_PC)

        if hasattr(account, "ua_mobile"):
            userAgents.mobile = account.ua_mobile
        else:
            userAgents.mobile = random.choice(USER_AGENTS_MOBILE)

        return userAgents

USER_AGENTS_PC = (
    # Safari Mac OSX
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.5.17 (KHTML, like Gecko) Version/8.0.5 Safari/600.5.17",
    # Firefox Mac OSX
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:40.0) Gecko/20100101 Firefox/40.0",
    # Firefox Win7
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:40.0) Gecko/20100101 Firefox/40.0",
    # Firefox Win8.1
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:40.0) Gecko/20100101 Firefox/40.0",
    # Firefox Win10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:40.0) Gecko/20100101 Firefox/40.0",
    # Chrome Mac OSX
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    # Chrome Win7
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    # Chrome Win8.1
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    # Chrome Win10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36"
)

USER_AGENTS_MOBILE = (
    # Chrome Android 5.1.1 (Samsung Edge)
    "Mozilla/5.0 (Linux; Android 5.1.1; SM-G925V Build/LMY47X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.84 Mobile Safari/537.36",
    # Chrome Android 5.0 (Galaxy S5)
    "Mozilla/5.0 (Linux; Android 5.0; SM-G900V Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.84 Mobile Safari/537.36",
    # Chrome Android 4.4.4 (Moto X Gen1)
    "Mozilla/5.0 (Linux; Android 4.4.4; XT1060 Build/KXA21.12-L1.26-3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.84 Mobile Safari/537.36",
    # Chrome Android 4.3 (Galaxy S3)
    "Mozilla/5.0 (Linux; Android 4.3; SGH-T999L Build/JSS15J) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.94 Mobile Safari/537.36",
    # Chrome iOS 8 (iPhone 6)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) CriOS/45.0.2454.68 Mobile/12H321",
    # BlackBerry - BB10
    "Mozilla/5.0 (BB10; Touch) AppleWebKit/537.1+ (KHTML, like Gecko) Version/10.0.0.1337 Mobile Safari/537.1+",
    # Safari iOS 8 (iPhone 6C)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4",
    # Safari iOS 7
    "Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_2 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A4449d Safari/9537.53"
)
