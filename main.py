import os
from os import environ, path
from typing import NamedTuple, List, Dict, Optional

import tweepy
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI()

base_dir = os.path.dirname(__file__)

templates = Jinja2Templates(directory="templates")

TW_CK = environ.get('TW_CK')
TW_CS = environ.get('TW_CS')
TW_AT = environ.get('TW_AT')
TW_AS = environ.get('TW_AS')

FETCH_USER_SIZE = 200
MAX_FETCH_PAGE_PER_USER = 10


class BoothInfo(NamedTuple):
    user_name: str
    pos_hiragana: str
    pos_number: str
    pos_kan: str


class User(NamedTuple):
    id: int
    screen_name: str
    display_name: str


class MatchedBooth(NamedTuple):
    info: BoothInfo
    user: User


def load_booth_info(path: str) -> List[BoothInfo]:
    with open(path, encoding='utf8') as f:
        lines = f.readlines()
    result = []
    for line in lines[1:]:
        elems = line.split(',')
        if len(elems) != 4:
            continue
        kan, hira, num, tw = line.split(',')
        tw = tw.strip()
        if not tw:
            continue
        tw = tw.replace('http://twitter.com', '').replace('https://twitter.com', '').replace('/', '')
        if ':' in tw:
            continue
        result.append(BoothInfo(
            user_name=tw,
            pos_hiragana=hira,
            pos_number=num,
            pos_kan=kan,
        ))
    return result


def fetch_following(auth: tweepy.OAuth1UserHandler, user_name: str) -> List[User]:
    v1 = tweepy.API(auth)
    users = []
    for user in tweepy.Cursor(v1.get_friends, screen_name=user_name, count=FETCH_USER_SIZE).pages(MAX_FETCH_PAGE_PER_USER):
        users.append(User(id=user.id, screen_name=user.screen_name, display_name=user.name))
    return users


auth = tweepy.OAuth1UserHandler(
    TW_CK, TW_CS, TW_AT, TW_AS
)

boothInfoList = load_booth_info(base_dir + '/assets/list.csv')


class RespBoothList(BaseModel):
    boothList: List[MatchedBooth]


cache: Dict[str, List[MatchedBooth]] = {}


async def find_booth(event: str, screen_name: str) -> List[MatchedBooth]:
    if cache.get(screen_name):
        return cache[screen_name]
    following = fetch_following(auth, screen_name)
    following_map: Dict[str, User] = {u.screen_name: u for u in following}
    matched_booth_list = []
    for boothInfo in boothInfoList:
        user = following_map.get(boothInfo.user_name)
        if user:
            matched_booth_list.append(MatchedBooth(info=boothInfo, user=user))
    cache[screen_name] = matched_booth_list
    return matched_booth_list


@app.get('/booth/find', response_model=RespBoothList)
async def booth_find(event: str, screen_name: str):
    return {"boothList": await find_booth(event, screen_name)}


@app.get('/', response_class=HTMLResponse)
def index():

    with open('static/index.html') as f:
        return f.read()


@app.get('/noah2', response_class=HTMLResponse)
async def noah2(request: Request, screen_name: Optional[str] = None):
    if screen_name:
        screen_name = screen_name.replace('@', '')
        matched_booth_list = await find_booth(event='noah2', screen_name=screen_name)
    else:
        matched_booth_list = []
        screen_name = ''
    return templates.TemplateResponse("noah2.html", {"request": request, "screen_name": screen_name, "booth_list": matched_booth_list})


app.mount("/static", StaticFiles(directory="static"), name="static")
