# Ninefold

Craft 9 of a food, seed, plant or mob drop into one satchel. Right-click the satchel to get the 9 back.

Ninefold is a pure datapack for Minecraft 26.3. It is the successor to FoodBundler, and grew out of [efeketket's Stackraft](https://modrinth.com/datapack/stackraft), with the author's blessing.

## Modules

Ninefold comes as one all-in-one pack, or as five modules that each work on their own:

| Module | Items | Capstone advancement |
|---|---|---|
| Seeds | 5 | Seed Sovereign |
| Raw Food | 25 | Larder Legend |
| Cooked Food | 9 | Executive Chef |
| Mob Drops | 20 | Trophy Hunter |
| Plants | 26 | Green Thumb |

Collect every satchel in all five for **The Whole Nine Yards**.

<details>
<summary>Full item list</summary>

- **Seeds:** wheat seeds, beetroot seeds, pumpkin seeds, melon seeds, cocoa beans
- **Raw Food:** egg, blue egg, brown egg, honeycomb, red mushroom, brown mushroom, apple, potato, beetroot, chorus fruit, carrot, golden carrot, sugar cane, pumpkin, sweet berries, glow berries, kelp, raw beef, raw chicken, raw mutton, raw porkchop, raw rabbit, raw salmon, raw cod, tropical fish
- **Cooked Food:** cookie, bread, steak, cooked chicken, cooked mutton, cooked porkchop, cooked rabbit, cooked salmon, cooked cod
- **Mob Drops:** ender pearl, blaze rod, breeze rod, string, rotten flesh, spider eye, gunpowder, phantom membrane, leather, feather, rabbit hide, sea pickle, verdant froglight, pearlescent froglight, ochre froglight, armadillo scute, turtle scute, shulker shell, ink sac, glow ink sac
- **Plants:** allium, azure bluet, dandelion, lily of the valley, oxeye daisy, poppy, red tulip, orange tulip, white tulip, pink tulip, blue orchid, closed eyeblossom, open eyeblossom, lilac, peony, rose bush, sunflower, torchflower, wither rose, leaf litter, pink petals, wildflowers, chorus flower, spore blossom, cactus, cactus flower

</details>

## How it works

- Hold a full stack of an item and you unlock its satchel recipe, with an advancement.
- Craft 9 of the item into one satchel. Satchels stack to 64.
- Right-click a satchel to get the 9 items back.
- Satchels look like heads, but can't be placed. Keep them in chests.
- Advancements appear under Zhinjio in the "Installed Datapacks" tab.

## Vanilla friendly

No resource pack and no client install. No functions either: Ninefold is only recipes and advancements, so nothing runs every tick.

## Building from source

The datapacks are generated from `items-manifest.json` by `build_ninefold.py` (Python 3, no dependencies):

```
python3 build_ninefold.py --zip
```

This writes the five modules and the all-in-one, as folders and zips, to `build/`. Zips are deterministic, so the same source always gives the same SHA-1.

Releases are published on [Modrinth](https://modrinth.com/datapack/ninefold).

## FoodBundler

FoodBundler v1.1.4 (Minecraft 1.21.6 to 1.21.8) was the last release under the old name. It is preserved at the tag `foodbundler-v1.1.4` and on [Modrinth](https://modrinth.com/datapack/foodbundler), where it is archived.

## Support

Thanks so much to [NiceRon](https://modrinth.com/user/NiceRon) and the crew at [Explorer's Eden](https://modrinth.com/organization/explorers-eden) for letting me use their Discord for chat support, and for all the help and mentoring while I learned how this stuff works.

## Credits

Inspired by [efeketket's Stackraft](https://modrinth.com/datapack/stackraft). The original license is kept in `LICENSE.original`.<br/>
Head textures courtesy of the amazing community at Minecraft-Heads.com:

[![Minecraft-Heads.com](https://images.minecraft-heads.com/banners/minecraft-heads.webp)](https://minecraft-heads.com/)
