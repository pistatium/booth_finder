from typing import NamedTuple, List
from os import environ

import tweepy

TW_CK = environ.get('TW_CK')
TW_CS = environ.get('TW_CS')
TW_AT = environ.get('TW_AT')
TW_AS = environ.get('TW_AS')


class BoothInfo(NamedTuple):
    user_name: str
    pos_hiragana: str
    pos_number: str


def load_booth_info(path: str) -> List[BoothInfo]:
    with open(path, encoding='utf8') as f:
        lines = f.readlines()
    result = []
    for line in lines[1:]:
        elems = line.split(',')
        if len(elems) != 3:
            continue
        hira, num, tw = line.split(',')
        tw = tw.strip()
        if not tw:
            continue
        tw = tw.replace('http://twitter.com', '').replace('https://twitter.com', '').replace('/', '')
        if ':' in tw:
            continue
        result.append(BoothInfo(
            user_name=tw,
            pos_hiragana=hira,
            pos_number=num
        ))
    return result

def fetch_following(auth: tweepy.OAuth1UserHandler, user_name: str) -> List[str]:
    v1 = tweepy.API(auth)
    res = v1.lookup_users(screen_name=[user_name, ])

    v2 = tweepy.Client(auth)
    res = v2.get_users_followers(res[0].id)
    print(res)

if __name__ == '__main__':
    auth = tweepy.OAuth1UserHandler(
        TW_CK, TW_CS, TW_AT, TW_AS
    )

    res = fetch_following(auth, 'kimihiro_n')

    boothInfo = load_booth_info('assets/list.csv')
