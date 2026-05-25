
import datetime
import dateutil
import re
import traceback

from data import Data
from utils import Log

Log = Log()
Data = Data()

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
