
import aiohttp
import asyncio
import datetime
import math

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
                        waittime = 15
                        if newschedules == Data['splatdrone/global'].get('schedules'):
                            Log.warn(f"Got same schedules as before! Retrying in {waittime}s...")
                            await asyncio.sleep(waittime)
                            if waittime < 240: waittime *= 2
                            continue
                        Data['splatdrone/global']['schedules'] = newschedules
                        return
                    else:
                        waittime = 1
                        Log.error(f"Failed to retrieve schedules from https://splatoon3.ink/ ({response.status})! Retrying in {waittime}m...")
                        await asyncio.sleep(waittime * 60)
                        if waittime < 32: waittime *= 2
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
