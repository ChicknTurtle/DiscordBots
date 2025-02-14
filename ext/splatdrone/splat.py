
import random
import json
import requests
from datetime import datetime, timezone
import discord

from data import Data
from utils import *

Log = Log()
Data = Data()

def get_image_url(weapon:str):
    if weapon in Data['splatdrone/global'].get('weaponImageCache', {}):
        return Data['splatdrone/global']['weaponImageCache'][weapon]
    base_url = "https://splatoonwiki.org/w/api.php"
    filename = f"S3 Weapon Main {weapon}.png"
    params = {
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json"
    }
    response = requests.get(base_url, params=params).json()
    pages = response.get("query", {}).get("pages", {})
    for page in pages.values():
        if "imageinfo" in page:
            url = page["imageinfo"][0]["url"]
            Data['splatdrone/global'].setdefault('weaponImageCache', {})
            Data['splatdrone/global']['weaponImageCache'][weapon] = url
            Log.debug(f"Splatdrone | Added new weapon image to cache: {weapon}")
            return url
    return None

def get_random_title(seed=None) -> tuple[str,str]:
    seeded_random = random.Random(seed) if seed else random
    with open('assets/splatoon/title_adjectives.txt') as file:
        adjectives:list[str] = file.read().splitlines()
    with open('assets/splatoon/title_subjects.txt') as file:
        subjects:list[str] = file.read().splitlines()
    return (seeded_random.choice(adjectives), seeded_random.choice(subjects))

def setup(bot:discord.AutoShardedBot):

    splat_group = bot.create_group("splat", "General Splatoon-related commands.")

    # Setup weapon data
    weapons:dict = [] # data of each main weapon (not kit specific)
    weapon_variants:dict = [] # data of each main weapon variant (kit specific)
    weapon_classes:dict = [] # data of each weapon class
    weapon_class_names:list[str] = [] # single, plural, and alias names of each weapon class
    weapon_class_names1:list[str] = [] # single names of each weapon class
    weapon_class_names2:list[str] = [] # plural names of each weapon class
    with open('assets/splatoon/weapons.json') as file:
        weapondata:dict = json.load(file)
    all_subs:dict = weapondata['subs']
    all_specials:dict = weapondata['specials']
    for weaponclass in weapondata['classes']:
        weapon_classes.append(weaponclass)
        weapon_class_names.append(weaponclass['name'].lower())
        weapon_class_names1.append(weaponclass['name'])
        weapon_class_names.append(weaponclass['name2'].lower())
        weapon_class_names2.append(weaponclass['name2'])
        weapon_class_names.extend([alias.lower() for alias in weaponclass['aliases']])
        for weapon in weaponclass['weapons']:
            weapons.append(weapon)
            for variant in weapon['variants']:
                weapon_variants.append(variant)
    
    def get_weapon_variant(name:str) -> dict|None:
        """Get a weapon variant from name or alias"""
        name = name or ''
        name = name.lower()
        replace = [' ','+','-','.']
        for char in replace:
            name = name.replace(char, '')
        for variant in weapon_variants:
            names = [variant['name'].lower().replace(' ', ''), ]
            names.extend([alias.lower().replace(' ', '') for alias in variant['aliases']])
            if get_weapon_class(variant['name'])['name'] == 'Dualies':
                names = [f"{n}s" for n in names] + names
            if name in names:
                return variant
        return None

    def get_sub(name:str) -> dict|None:
        """Get a sub weapon from name"""
        name = name or ''
        return(all_subs.get(name, None))

    def get_special(name:str) -> dict|None:
        """Get a special weapon from name"""
        name = name or ''
        return(all_specials.get(name, None))

    def get_weapon_class(name:str) -> dict|None:
        """Get a weapon variant's weapon class"""
        name = name or ''
        name = name.lower()
        for weapon_class in weapon_classes:
            for weapon in weapon_class['weapons']:
                for variant in weapon['variants']:
                    if name == variant['name'].lower() or name in [alias.lower() for alias in variant['aliases']]:
                        return weapon_class
        return None
    
    # rw
    @splat_group.command(name="rw", description="Choose a random weapon with optional filters")
    async def splat_rw_command(ctx:discord.ApplicationContext,
                               amount=discord.Option(int, min_value=1, max_value=8, default=1, description="Amount of weapons to choose"),
                               class_filter=discord.Option(str, name='class_filter', required=False, choices=weapon_class_names2, description="Filter by a class"),
                               sub_filter=discord.Option(str, name='sub_filter', required=False, choices=list(all_subs.keys())+['Any Bomb'], description="Filter by a sub weapon"),
                               special_filter=discord.Option(str, name='special_filter', required=False, choices=list(all_specials.keys()), description="Filter by a special weapon"),
                               get_class=discord.Option(bool, name='get_class', required=False, description="Get a random weapon class instead of weapon. All filter options will be ignored")):
        responses = []
        for i in range(amount):
            if get_class == True:
                randomclass = random.choice(weapon_classes)['name2']
                #responses.append(f"Your random weapon class is **{randomclass}**!")
                responses.append(randomclass)
                continue
            valid_variants = weapon_variants
            if class_filter:
                valid_variants = [variant for variant in weapon_variants if get_weapon_class(variant['name'])['name2'].lower() == class_filter.lower()]
            if sub_filter:
                if sub_filter == 'Any Bomb':
                    valid_variants = [variant for variant in valid_variants if get_sub(variant['sub']).get('bomb')]
                else:
                    valid_variants = [variant for variant in valid_variants if variant['sub'].lower() == sub_filter.lower()]
            if special_filter:
                valid_variants = [variant for variant in valid_variants if variant['special'].lower() == special_filter.lower()]
            if valid_variants:
                randomweapon = random.choice(valid_variants)
            else:
                await ctx.respond(f"No weapons matched the selected filters! Try with less filters.", ephemeral=True)
                return
            
            sub = get_sub(randomweapon['sub'])
            special = get_special(randomweapon['special'])
            sub_emote = (f"<:sub:{sub['emote']}>")
            special_emote = (f"<:special:{special['emote']}>")
            
            responses.append((randomweapon['name'], f"{sub_emote} {special_emote}"))
        
        if get_class is True:
            if amount == 1:
                await ctx.respond(f"Your random weapon class is **{responses[0]}**!")
            else:
                await ctx.respond(f"Your random weapon classes are {', '.join([f"**{response}**" for response in responses])}!")
        else:
            if amount == 1:
                await ctx.respond(f"Your random weapon is **{responses[0][0]}**! {responses[0][1]}")
            else:
                result = "Your random weapons are:"
                for i in range(1, amount+1):
                    if i == 1:
                        result = f"{result}\n1. **{responses[i-1][0]}** {responses[i-1][1]}"
                    else:
                        result = f"{result}\n- **{responses[i-1][0]}** {responses[i-1][1]}"
                await ctx.respond(result)

    @splat_group.command(name="kit", description="View a weapon's kit")
    async def splat_kit_command(ctx:discord.ApplicationContext,
                          weapon=discord.Option(str, name='weapon', required=True, description="Weapon name, aliases supported")):
        weapon_data = get_weapon_variant(weapon)
        if weapon_data:
            sub = get_sub(weapon_data['sub'])
            special = get_special(weapon_data['special'])
            sub_emote = (f"<:sub:{sub['emote']}>")
            special_emote = (f"<:special:{special['emote']}>")
            wiki = weapon_data['name'].replace(' ', '_')
            embed:discord.Embed = bot.newembed(
                f"{weapon_data['name']}",
                f"{sub_emote} {weapon_data['sub']}\n{special_emote} {weapon_data['special']} ({weapon_data['special-points']}p)\n-# [Inkipedia Page](<https://splatoonwiki.org/wiki/{wiki}>)"
            )
            image_url = get_image_url(weapon_data['name'])
            if image_url:
                embed.set_thumbnail(url=image_url)
            await ctx.respond('', embed=embed)
        else:
            await ctx.respond(f"No weapon found for `{weapon}`\n-# If you believe this should be a valid alias, let me know with **/bot suggest**", ephemeral=True)

    @splat_group.command(name="title", description="Get a random title")
    async def splat_title_command(ctx:discord.ApplicationContext,
                                  daily=discord.Option(bool, default=False, description="View your daily title"),
                                  user=discord.Option(discord.User, default=None, description="View someone else's daily title. Does nothing if daily=False")):
        if daily:
            user:discord.User = user or ctx.author
            who = 'Your' if user == ctx.author else f"{user.display_name}'s"
            adjective, subject = get_random_title(f"{user.id}-{datetime.now(timezone.utc).date()}")
            await ctx.respond(f"{who} daily title is **{adjective} {subject}**!")
        else:
            adjective, subject = get_random_title()
            await ctx.respond(f"Your random title is **{adjective} {subject}**!")
    splat_title_command.helpdesc="Daily title uses UTC timezone (same as Splatoon daily reset)"
