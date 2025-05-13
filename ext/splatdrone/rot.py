import datetime
import discord
from PIL import Image

from data import Data
from utils import Log, load_image, image_to_bufferimg, stack_images_horizontally, overlay_center
from splatdrone.splatrotations import SplatFetcher, get_offset, get_rot

Log = Log()
Data = Data()
SplatFetcher = SplatFetcher()

emojis = {
    # Modes
    'Splat Zones':'<:SplatZones:1356643525239771249>',
    'Tower Control':'<:TowerControl:1356643575558963371>',
    'Rainmaker':'<:Rainmaker:1356643600548757634>',
    'Clam Blitz':'<:ClamBlitz:1356643619775316110>',
    'ModeNotFound':'<:ModeNotFound:1357165817048993952>',

    # Maps
    'Barnacle & Dime':'<:BarnacleDime:1357167334875201609>',
    'Bluefin Depot':'<:BluefinDepot:1357167677369745449>',
    'Brinewater Springs':'<:BrinewaterSprings:1357167930986598553>',
    'Crableg Capital':'<:CrablegCapital:1357168046661435463>',
    'Eeltail Alley':'<:EeltailAlley:1357168344419143711>',
    'Flounder Heights':'<:FlounderHeights:1357168429521567784>',
    'Hagglefish Market':'<:HagglefishMarket:1357169405355753502>',
    'Hammerhead Bridge':'<:HumpbackPumpTrack:1357169725968482304>',
    'Humpback Pump Track':'<:HumpbackPumpTrack:1357169725968482304>',
    'Inkblot Art Academy':'<:InkblotArtAcademy:1357169809896509541>',
    'Lemuria Hub':'<:LemuriaHub:1357169937713729629>',
    'Mahi-Mahi Resort':'<:MahiMahiResort:1357170671989428445>',
    'MakoMart':'<:MakoMart:1357170965901213958>',
    'Manta Maria':'<:MantaMaria:1357171295397085254>',
    'Marlin Airport':'<:MarlinAirport:1357171400850542674>',
    'Mincemeat Metalworks':'<:MincemeatMetalworks:1357171484669382818>',
    'Museum d\'Alfonsino':'<:MuseumdAlfonsino:1357171603485495377>',
    'Robo ROM-en':'<:RoboROMen:1357178143802396782>',
    'Scorch Gorge':'<:ScorchGorge:1357178376590332096>',
    'Shipshape Cargo Co.':'<:ShipshapeCargoCo:1357178503149129821>',
    'Sturgeon Shipyard':'<:SturgeonShipyard:1357178967018180668>',
    'Um\'ami Ruins':'<:UmamiRuins:1357179081501835386>',
    'Undertow Spillway':'<:UndertowSpillway:1357179296648790099>',
    'Wahoo World':'<:WahooWorld:1357179396477157416>',
    'Grand Splatlands Bowl':'<:GrandSplatlandsBowl:1357169102807896235>',

    'Bonerattle Arena':'<:BonerattleArena:1357167785972731904>',
    'Gone Fission Hydroplant':'<:GoneFissionHydroplant:1357168933312008232>',
    'Salmonid Smokeyard':'<:SalmonidSmokeyard:1357178263914676375>',
    'Sockeye Station':'<:SockeyeStation:1357178645679968266>',
    'Spawning Grounds':'<:SpawningGrounds:1357178790199165002>',

    'StageNotFound':'<:StageNotFound:1357177641891008753>',
}
images = {
    'Splat Zones':'assets/splatoon/icons/splatzones.png',
    'Tower Control':'assets/splatoon/icons/towercontrol.png',
    'Rainmaker':'assets/splatoon/icons/rainmaker.png',
    'Clam Blitz':'assets/splatoon/icons/clamblitz.png',
}

mode_config = {
    "turf": {
        "rot_key": "turf",
        "index": None,
        "has_mode": False,
        "color": 0xcff622,
        "gametype_img": 'assets/splatoon/icons/turfwar.png',
        "desc_title": "Turf War Rotation"
    },
    "open": {
        "rot_key": "anarchy",
        "index": 1,
        "has_mode": True,
        "color": 0xf54910,
        "gametype_img": 'assets/splatoon/icons/anarchy.png',
        "desc_title": "Anarchy Open Rotation"
    },
    "series": {
        "rot_key": "anarchy",
        "index": 0,
        "has_mode": True,
        "color": 0xf54910,
        "gametype_img": 'assets/splatoon/icons/anarchy.png',
        "desc_title": "Anarchy Series Rotation"
    },
    "xbattle": {
        "rot_key": "xrank",
        "index": None,
        "has_mode": True,
        "color": 0x0fdb9b,
        "gametype_img": 'assets/splatoon/icons/xbattle.png',
        "desc_title": "X Battle Rotation"
    },
}

def get_mode_data(rot, mode):
    config = mode_config.get(mode)
    if not config:
        return None
    if config["rot_key"] == "xrank":
        setting = rot[config["rot_key"]]["xMatchSetting"]
    elif config["rot_key"] == "turf":
        setting = rot[config["rot_key"]]["regularMatchSetting"]
    else:
        setting = rot[config["rot_key"]]["bankaraMatchSettings"][config["index"]]
    map1 = setting["vsStages"][0]["name"]
    map1_img = load_image(setting["vsStages"][0]["image"]["url"])
    map2 = setting["vsStages"][1]["name"]
    map2_img = load_image(setting["vsStages"][1]["image"]["url"])
    mode_name = setting["vsRule"]["name"]
    return {
        "map1": map1,
        "map2": map2,
        "map1_img": map1_img,
        "map2_img": map2_img,
        "mode_name": mode_name,
        "config": config
    }

def setup(bot:discord.AutoShardedBot):

    #rot_group = bot.create_group("rot", "View current or future Splatoon 3 rotations.")

    @bot.command(name="rot", description="View current or future Splatoon 3 rotations.")
    async def rot_command(ctx:discord.ApplicationContext,
                          mode=discord.Option(str, default='overview', description="View rotation of a specific mode, default=overview", choices=[discord.OptionChoice("Rotation Overview","overview"), discord.OptionChoice("Turf War","turf"), discord.OptionChoice("Anarchy Open","open"), discord.OptionChoice("Anarchy Series","series"), discord.OptionChoice("X Battle","xbattle"), discord.OptionChoice("Salmon Run", "salmonrun")]),
                          offset=discord.Option(str, default='0', description="Specify which rotation to view, default=current", choices=[discord.OptionChoice("Current","current"), discord.OptionChoice("Next (+1)",'1'),discord.OptionChoice("+2",'2'),discord.OptionChoice("+3",'3'),discord.OptionChoice("+4",'4'),discord.OptionChoice("+5",'5'),discord.OptionChoice("+6",'6'),discord.OptionChoice("+7",'7'),discord.OptionChoice("+8",'8'),discord.OptionChoice("+9",'9'),discord.OptionChoice("+10",'10')])):
        offset = int(offset)
        rot = get_rot(offset)

        turf_map1 = rot['turf']['regularMatchSetting']['vsStages'][0]['name']
        turf_map2 = rot['turf']['regularMatchSetting']['vsStages'][1]['name']
        turf_map1_img = load_image(rot['turf']['regularMatchSetting']['vsStages'][0]['image']['url'])
        turf_map2_img = load_image(rot['turf']['regularMatchSetting']['vsStages'][1]['image']['url'])
        open_map1 = rot['anarchy']['bankaraMatchSettings'][1]['vsStages'][0]['name']
        open_map2 = rot['anarchy']['bankaraMatchSettings'][1]['vsStages'][1]['name']
        open_map1_img = load_image(rot['anarchy']['bankaraMatchSettings'][1]['vsStages'][0]['image']['url'])
        open_map2_img = load_image(rot['anarchy']['bankaraMatchSettings'][1]['vsStages'][1]['image']['url'])
        open_mode = rot['anarchy']['bankaraMatchSettings'][1]['vsRule']['name']
        series_map1 = rot['anarchy']['bankaraMatchSettings'][0]['vsStages'][0]['name']
        series_map2 = rot['anarchy']['bankaraMatchSettings'][0]['vsStages'][1]['name']
        series_map1_img = load_image(rot['anarchy']['bankaraMatchSettings'][0]['vsStages'][0]['image']['url'])
        series_map2_img = load_image(rot['anarchy']['bankaraMatchSettings'][0]['vsStages'][1]['image']['url'])
        series_mode = rot['anarchy']['bankaraMatchSettings'][0]['vsRule']['name']
        xbattle_map1 = rot['xrank']['xMatchSetting']['vsStages'][0]['name']
        xbattle_map2 = rot['xrank']['xMatchSetting']['vsStages'][1]['name']
        xbattle_map1_img = load_image(rot['xrank']['xMatchSetting']['vsStages'][0]['image']['url'])
        xbattle_map2_img = load_image(rot['xrank']['xMatchSetting']['vsStages'][1]['image']['url'])
        xbattle_mode = rot['xrank']['xMatchSetting']['vsRule']['name']

        rotstart = datetime.datetime.fromisoformat(rot['turf']['startTime'])
        rotend = datetime.datetime.fromisoformat(rot['turf']['endTime'])
        future = True if rotstart > datetime.datetime.now(datetime.timezone.utc) else False
        starttimestamp = round(rotstart.timestamp())
        endtimestamp = round(rotend.timestamp())
        endorstart = f"Starts <t:{starttimestamp}:R>" if future else f"Ends <t:{endtimestamp}:R>"

        embed:discord.Embed = bot.newembed()
        embed.set_footer(text="Rotation data from splatoon3.ink")

        if mode in mode_config:
            data = get_mode_data(rot, mode)
            config = data["config"]
            embed.color = config["color"]
            mode_emoji_part = ''
            if config["has_mode"]:
                mode_emoji = emojis.get(data["mode_name"], emojis['ModeNotFound'])
                mode_emoji_part = f"{mode_emoji} "
            map1_emoji = emojis.get(data["map1"], emojis['StageNotFound'])
            map2_emoji = emojis.get(data["map2"], emojis['StageNotFound'])
            embed.description = (f"## {config['desc_title']}\n<t:{starttimestamp}:t> - <t:{endtimestamp}:t>\n{endorstart}\n\n{mode_emoji_part}**{data['mode_name']}**\n{map1_emoji} **{data['map1']}** + {map2_emoji} **{data['map2']}**")
            gametype_img = discord.File(config["gametype_img"], filename="gametype_img.png")
            embed.set_thumbnail(url='attachment://gametype_img.png')
            map_img = stack_images_horizontally([data["map1_img"], data["map2_img"]], 10)
            mode_img_path = images.get(data["mode_name"])
            mode_img = mode_img_path and Image.open(mode_img_path)
            map_img = mode_img and overlay_center(map_img, mode_img, 0.75, 0.75) or map_img
            map_img = discord.File(image_to_bufferimg(map_img), filename="map_img.png")
            embed.set_image(url='attachment://map_img.png')
            files = [map_img, gametype_img]
        elif mode == 'overview':
            embed.description = f"# Rotation Overview\n<t:{starttimestamp}:t> - <t:{endtimestamp}:t>\n{endorstart}"
            files = []
        else:
            await ctx.respond("Not implemented :P")
            return

        await ctx.respond(embed=embed, files=files)

    # Start loop to fetch new rotation data
    async def start_fetch_loop():
        await SplatFetcher.request_loop()
    bot.loop.create_task(start_fetch_loop())
