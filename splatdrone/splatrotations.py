
import aiohttp
import asyncio
import datetime
import dateutil
import math
import re
import traceback

from data import Data
from utils import Log, format_time_short

Log = Log()
Data = Data()

class SplatFetcher():
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    def _initialize(self):
        pass
        
    async def fetchdata(self):
        schedules_url = "https://splatoon3.ink/data/schedules.json"
        Log.debug("Fetching new rotation data from https://splatoon3.ink/...")
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(schedules_url) as response:
                    if response.status == 200:
                        newschedules = await response.json()
                        if newschedules == Data['splatdrone/global'].get('schedules'):
                            Log.warn("Got same schedules as before! Retrying in 10s...")
                            await asyncio.sleep(10)
                            continue
                        Data['splatdrone/global']['schedules'] = newschedules
                        return
                    else:
                        Log.error(f"Failed to retrieve schedules from https://splatoon3.ink/ ({response.status})! Retrying in 5m...")
                        await asyncio.sleep(5*60)
                        continue

    async def request_loop(self):
        if not Data['splatdrone/global'].get('schedules'):
            await self.fetchdata()
        # fetch data loop
        while True:
            # calculate time until next rot, and wait that long
            nextrot = datetime.datetime.fromisoformat(Data['splatdrone/global']['schedules']['data']['regularSchedules']['nodes'][0]['endTime'])
            nextrot += datetime.timedelta(seconds=25)
            nextrotin = (nextrot - datetime.datetime.now(datetime.timezone.utc))
            sleeptime = 3
            sleepamount = max(0, math.floor(nextrotin.total_seconds()/sleeptime)) + 1
            Log.debug(f"Fetching next rotation in {format_time_short(nextrotin)}...")
            for i in range(sleepamount):
                await asyncio.sleep(sleeptime)
            # fetch new data if it's time
            if datetime.datetime.now(datetime.timezone.utc) > nextrot:
                await self.fetchdata()

def parse_rot(input_str:str):
    result = {
        "mode": None,
        "next": False,
        "time": None,
        "offset": None
    }
    tokens = input_str.split()
    time_12h_pattern = re.compile(r'^\d{1,2}(:\d{2})?\s*(am|pm)$', re.IGNORECASE)
    time_24h_pattern = re.compile(r'^\d{1,2}:\d{2}$')
    offset_pattern = re.compile(r'^\+\d+$')
    # check mode
    if any(item in tokens for item in ['turf','turfwar','fest','splatfest']):
        result['mode'] = 'turf'
    elif any(item in tokens for item in ['open','ranked','anarchy','anarchyopen']):
        result['mode'] = 'open'
    elif any(item in tokens for item in ['series','rankedseries','anarchyseries']):
        result['mode'] = 'series'
    elif any(item in tokens for item in ['xbattle','xrank','x','xseries','xranked']):
        result['mode'] = 'xbattle'
    elif any(item in tokens for item in ['salmonrun','srun','salmon','sammies']):
        result['mode'] = 'salmonrun'
    else:
        result['mode'] = 'unknown'
    # check time args
    for token in tokens:
        token = token.lower().strip()
        # check next
        if token == "next":
            result["next"] = True
            continue
        # check offset
        if offset_pattern.match(token):
            result["offset"] = int(token[1:])
            continue
        # check 12h time
        if time_12h_pattern.match(token):
            result["time"] = token
            continue
        # check 24h time
        elif time_24h_pattern.match(token):
            result["time"] = token
            continue
    # build time
    now = datetime.datetime.now()
    base_time = now
    if result["time"]:
        try:
            parsed_time = dateutil.parser.parse(result["time"], fuzzy=True, default=now)
            if parsed_time < now:
                parsed_time += datetime.timedelta(days=1)
            base_time = parsed_time
        except Exception as e:
            base_time = now
    elif result["next"]:
        base_time = now + datetime.timedelta(hours=2)
    # apply offset
    if result["offset"] is not None:
        base_time += datetime.timedelta(hours=result["offset"] * 2)
    return result["mode"], base_time

def get_offset(time:datetime) -> int | None:
    try:
        start_time = Data['splatdrone/global']['schedules']['data']['regularSchedules']['nodes'][0]['startTime']
        start_time = dateutil.parser.isoparse(start_time).replace(tzinfo=datetime.timezone.utc)
        time_utc = time.astimezone(datetime.timezone.utc)
        time_difference = time_utc - start_time
        if time_difference.total_seconds() >= 0:
            return int(time_difference.total_seconds() // (60*60*2))
        else:
            return 0
    except (KeyError, ValueError, AttributeError) as e:
        Log.error(traceback.format_exc())
        return None

def get_rot(offset:int=0) -> dict|None:
    if not Data['splatdrone/global'].get('schedules'):
        return
    rot = {}
    rot['turf'] = Data['splatdrone/global']['schedules']['data']['regularSchedules']['nodes'][offset]
    rot['anarchy'] = Data['splatdrone/global']['schedules']['data']['bankaraSchedules']['nodes'][offset]
    rot['xrank'] = Data['splatdrone/global']['schedules']['data']['xSchedules']['nodes'][offset]
    return rot
