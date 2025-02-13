
import random
import json
import discord

from utils import *

Log = Log()

def setup(bot:discord.AutoShardedBot):

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
    @bot.command(name="rw", description="Give a random weapon", integration_types={discord.IntegrationType.guild_install,discord.IntegrationType.user_install})
    async def rw_command(ctx:discord.ApplicationContext, weaponclass=discord.Option(str, name='class', required=False, choices=weapon_class_names2, description="Filter by a class"), sub=discord.Option(str, required=False, choices=list(all_subs.keys())+['Any Bomb'], description="Filter by a sub weapon"), special=discord.Option(str, required=False, choices=list(all_specials.keys()), description="Filter by a special weapon"), getclass=discord.Option(bool, required=False, description="Get a random weapon class instead of weapon. All other options will be ignored")):
        if getclass == True:
            randomclass = random.choice(weapon_classes)['name2']
            await ctx.respond(f"Your random weapon class is **{randomclass}**!")
            return
        valid_variants = weapon_variants
        if weaponclass:
            valid_variants = [variant for variant in weapon_variants if get_weapon_class(variant['name'])['name2'].lower() == weaponclass.lower()]
        if sub:
            if sub == 'Any Bomb':
                valid_variants = [variant for variant in valid_variants if get_sub(variant['sub']).get('bomb')]
            else:
                valid_variants = [variant for variant in valid_variants if variant['sub'].lower() == sub.lower()]
        if special:
            valid_variants = [variant for variant in valid_variants if variant['special'].lower() == special.lower()]
        if valid_variants:
            randomweapon = random.choice(valid_variants)
        else:
            await ctx.respond(f"No weapons matched the selected filters! Try with less filters.", ephemeral=True)
            return
        
        sub = get_sub(randomweapon['sub'])
        special = get_special(randomweapon['special'])
        sub_emote = (f"<:sub:{sub['emote']}>")
        special_emote = (f"<:special:{special['emote']}>")
        
        await ctx.respond(f"Your random weapon is **{randomweapon['name']}**! {sub_emote} {special_emote}")

    @bot.command(name="kit", description="View a weapon's kit", integration_types={discord.IntegrationType.guild_install,discord.IntegrationType.user_install})
    async def kit_command(ctx: discord.ApplicationContext, weapon=discord.Option(str, name='weapon', required=True, description="Weapon name, aliases supported")):
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
            image_url = weapon_data.get('image')
            if image_url:
                embed.set_thumbnail(url=image_url)
            await ctx.respond('', embed=embed)
        else:
            await ctx.respond(f"No weapon found for `{weapon}`\n-# If you believe this should be a valid alias, let me know with **/bot suggest**", ephemeral=True)
    