#!/usr/bin/env python3
"""
build_ninefold.py — generate the Ninefold datapacks from items-manifest.json.

Input: items-manifest.json (items, names, head textures) and shared/ (the Zhinjio tab).
Children are the single source of truth; the all-in-one (AIO) is the
byte-identical UNION of the five module trees plus the shared global/ninefold files.

Output layout per module (a standalone loadable datapack):
    <out>/ninefold_<module>/
        pack.mcmeta                                    (min_format/max_format [121,0])
        pack.png
        data/<namespace>/recipe/stack_<item>.json      shaped 3x3 -> bundle head
        data/<namespace>/advancement/<item>.json       display advancement (leaf-chain)
        data/<namespace>/advancement/recipes/misc/stack_<item>.json   recipe-unlock twin
        data/<namespace>/advancement/<module>.json     module root node (under global:zhinjio)
        data/<namespace>/advancement/capstone.json     module capstone ("obtained each")
        data/global/advancement/{root,zhinjio}.json     shared communal tab (union-dedupes)
        data/ninefold/advancement/completionist.json    grand capstone (shared, all 85)

Per DESIGN.md this is a pure datapack: recipes + advancements + components, zero client assets.
"""
import argparse, base64, hashlib, json, os, shutil, struct, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "items-manifest.json")
ICONS = os.path.join(HERE, "assets", "icons")   # <pack>-icon.png, copied in as each pack's pack.png


def pack_icon(pack_name):
    path = os.path.join(ICONS, "%s-icon.png" % pack_name)
    if not os.path.exists(path):
        raise SystemExit("missing pack icon: %s" % path)
    return path
LICENSES = [os.path.join(HERE, n) for n in ("LICENSE", "LICENSE.original")]  # MIT notices, shipped in every pack
GLOBAL_SRC = os.path.join(HERE, "shared")  # shared Zhinjio tab nodes (root, zhinjio)
FIXED_DT = (2026, 1, 1, 0, 0, 0)   # deterministic zip timestamps -> stable SHA-1

# ---------- bundle-head profile (texture value + deterministic id) ----------

def profile(texture_hash):
    """player_head profile block: base64 SKIN-url value (byte-identical to v1.1.4) +
    a deterministic 4-int UUID derived from the texture hash (stable rebuilds; identical
    within an item so bundles stack; unique across items so different bundles don't)."""
    url = "http://textures.minecraft.net/texture/%s" % texture_hash
    value = base64.b64encode(
        ('{"textures":{"SKIN":{"url":"%s"}}}' % url).encode()).decode()
    # id: deterministic 4-int UUID from a hash of the texture string. Hashing the string
    # (not parsing it as hex) is robust to Mojang's variable-length hashes, and gives a
    # value stable across rebuilds and unique per texture (so distinct bundles never stack).
    pid = list(struct.unpack(">4i", hashlib.sha256(texture_hash.encode()).digest()[:16]))
    return {"id": pid, "properties": [{"name": "textures", "value": value}]}


def readable(item_id):
    return item_id.replace("_", " ").title()

# ---------- per-item file generators ----------

# The bundle is music disc 13 drawn as a player head (item_model + profile). It was a real player_head
# until 2026-11-23, but placing a block counts as a use, so placing a bundle paid out its use_remainder
# and kept the head: a dupe (ItemStack.useOn in 26.3). v1.0 used a poisonous potato, but opening a
# bundle then counted as eating one (diet and eat-only advancements). Disc 13 is the most common disc,
# no recipe ingredient or trade item, and with jukebox_playable removed it can't be played (Mark and
# NiceRon, 2026-11-23).
BUNDLE_BASE = "minecraft:music_disc_13"


def recipe(it):
    """Shaped 3x3 of the item -> 1 bundle head with all components (DESIGN §3/§5)."""
    return {
        "type": "minecraft:crafting_shaped",
        "category": "misc",
        "pattern": ["###", "###", "###"],
        "key": {"#": [it["mc_item"]]},
        "result": {
            "id": BUNDLE_BASE,
            "count": 1,
            "components": {
                "minecraft:item_model": "minecraft:player_head",
                "minecraft:max_stack_size": 64,
                "minecraft:rarity": "common",
                "!minecraft:jukebox_playable": {},
                "minecraft:profile": profile(it["texture_hash"]),
                "minecraft:item_name": {"text": it["bundle_name"], "color": "white"},
                "minecraft:consumable": {
                    "consume_seconds": 0,
                    "animation": "block",
                    "sound": "minecraft:item.bundle.drop_contents",
                    "has_consume_particles": False,
                },
                "minecraft:use_remainder": {"id": it["mc_item"], "count": 9},
                # per-item tag drives the capstone "obtained each bundle" criteria (DESIGN §3/§6)
                "minecraft:custom_data": {"ninefold": "%s/%s" % (it["module"], it["id"])},
            },
        },
    }


def display_adv(it, ns):
    """Display advancement — leaf hanging off its chain predecessor (or the module node
    for chain heads). No gating: independent full-stack unlock (DESIGN §6)."""
    parent = "%s:%s" % (ns, it["parent"]) if it.get("parent") else "%s:%s" % (ns, it["module"])
    return {
        "display": {
            "icon": {"id": it["mc_item"]},
            "title": it["adv_title"],
            "description": {"text": "Obtain a full stack of %s" % readable(it["id"])},
            "announce_to_chat": False,
        },
        "parent": parent,
        "criteria": {
            it["id"]: {
                "trigger": "minecraft:inventory_changed",
                "conditions": {"items": [{"items": [it["mc_item"]], "count": it["max_stack"]}]},
            }
        },
    }


def recipe_unlock_adv(it, ns):
    """Hidden twin under minecraft:recipes/root — same full-stack criterion, grants recipe."""
    return {
        "parent": "minecraft:recipes/root",
        "criteria": {
            "unlock_recipe": {
                "trigger": "minecraft:inventory_changed",
                "conditions": {"items": [{"items": [it["mc_item"]], "count": it["max_stack"]}]},
            }
        },
        "requirements": [["unlock_recipe"]],
        "rewards": {"recipes": ["%s:stack_%s" % (ns, it["id"])]},
    }

# ---------- structural nodes ----------

def module_node(mod, mod_meta, rep_item):
    """The module root ('Ninefold: Seeds') under the shared global:zhinjio tab."""
    return {
        "display": {
            "icon": {"id": rep_item["mc_item"]},
            "title": mod_meta["display"],
            "description": "%s — nine become one" % mod_meta["display"],
            "show_toast": False,
            "announce_to_chat": False,
        },
        "parent": "global:zhinjio",
        "criteria": {"trigger": {"trigger": "minecraft:tick"}},
    }


def obtained_criterion(it):
    """inventory_changed matching the bundle head via its per-item custom_data (DESIGN §6).
    Persistent checkbox — once obtained (any source: craft, gift, loot) it stays checked."""
    return {
        "trigger": "minecraft:inventory_changed",
        "conditions": {"items": [{
            "items": [BUNDLE_BASE],
            "predicates": {"minecraft:custom_data": "{ninefold:'%s/%s'}" % (it["module"], it["id"])},
        }]},
    }


def capstone(mod_meta, items, rep_item):
    """Per-module capstone: 'obtained each bundle', goal frame, hangs as a distinguished
    leaf off the module node (never AS the parent — that would hide descendants; DESIGN §6)."""
    ns = mod_meta["namespace"]
    return {
        "display": {
            "icon": {"id": rep_item["mc_item"]},
            "title": mod_meta["capstone_title"],
            "description": {"text": "Obtain every bundle in %s" % mod_meta["display"]},
            "frame": "goal",
            "show_toast": True,
            "announce_to_chat": False,
        },
        "parent": "%s:%s" % (ns, mod_meta["module"]),
        "criteria": {it["id"]: obtained_criterion(it) for it in items},
    }


def grand_capstone(gc, all_items):
    """Shared ninefold:completionist — all 85 bundles, challenge frame, announced.
    Parent is global:zhinjio so it works in à-la-carte installs (criteria test inventory,
    not sibling advancements). Shipped byte-identical in every module (DESIGN §6/§8)."""
    return {
        "display": {
            "icon": {"id": "minecraft:nether_star"},
            "title": gc["title"],
            "description": {"text": "Obtain every Ninefold bundle — all 85"},
            "frame": "challenge",
            "show_toast": True,
            "announce_to_chat": True,
        },
        "parent": "global:zhinjio",
        "criteria": {it["id"]: obtained_criterion(it) for it in all_items},
    }

# ---------- filesystem / packaging ----------

def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def copy_licenses(root):
    for path in LICENSES:
        if not os.path.exists(path):
            raise SystemExit("missing license file: %s" % path)
        shutil.copy2(path, os.path.join(root, os.path.basename(path)))


def pack_mcmeta(description):
    return {"pack": {"description": description, "min_format": [121, 0], "max_format": [121, 0]}}


def rep_item_for(items):
    """Representative item = the branch-0, chain-head (icon for the module node/capstone)."""
    heads = [i for i in items if not i.get("parent")]
    return sorted(heads, key=lambda i: (i.get("branch", 0), i.get("chain_pos", 0)))[0]


def build_module(mod, mod_meta, items, gc, all_items, out_root):
    ns = mod_meta["namespace"]
    mod_meta = dict(mod_meta, module=mod)
    root = os.path.join(out_root, "ninefold_%s" % mod)
    if os.path.isdir(root):
        shutil.rmtree(root)
    rep = rep_item_for(items)

    dump(os.path.join(root, "pack.mcmeta"), pack_mcmeta(mod_meta["display"]))
    shutil.copy2(pack_icon("ninefold_%s" % mod), os.path.join(root, "pack.png"))
    copy_licenses(root)

    adv = os.path.join(root, "data", ns, "advancement")
    rec = os.path.join(root, "data", ns, "recipe")
    for it in items:
        dump(os.path.join(rec, "stack_%s.json" % it["id"]), recipe(it))
        dump(os.path.join(adv, "%s.json" % it["id"]), display_adv(it, ns))
        dump(os.path.join(adv, "recipes", "misc", "stack_%s.json" % it["id"]), recipe_unlock_adv(it, ns))
    dump(os.path.join(adv, "%s.json" % mod), module_node(mod, mod_meta, rep))
    dump(os.path.join(adv, "capstone.json"), capstone(mod_meta, items, rep))

    # shared files (byte-identical across modules -> union dedupes in the AIO)
    gdst = os.path.join(root, "data", "global", "advancement")
    os.makedirs(gdst, exist_ok=True)
    for name in ("root.json", "zhinjio.json"):
        shutil.copy2(os.path.join(GLOBAL_SRC, name), os.path.join(gdst, name))
    dump(os.path.join(root, "data", "ninefold", "advancement", "completionist.json"),
         grand_capstone(gc, all_items))
    return root


def build_aio(module_dirs, out_root, description):
    """AIO = byte-identical union of every module tree (DESIGN §8)."""
    root = os.path.join(out_root, "ninefold")
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root)
    for md in module_dirs:
        for dirpath, _, files in os.walk(os.path.join(md, "data")):
            for fn in files:
                src = os.path.join(dirpath, fn)
                rel = os.path.relpath(src, md)
                dst = os.path.join(root, rel)
                if os.path.exists(dst):
                    # union-dedupe: identical shared files may legitimately recur
                    if open(src, "rb").read() != open(dst, "rb").read():
                        raise SystemExit("AIO union collision (differing bytes): %s" % rel)
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
    dump(os.path.join(root, "pack.mcmeta"), pack_mcmeta(description))
    shutil.copy2(pack_icon("ninefold"), os.path.join(root, "pack.png"))
    copy_licenses(root)
    return root


def zip_pack(pack_dir, out_zip):
    """Deterministic zip: sorted entries, fixed timestamps -> stable SHA-1."""
    files = []
    for dp, _, fns in os.walk(pack_dir):
        for fn in fns:
            full = os.path.join(dp, fn)
            files.append((os.path.relpath(full, pack_dir), full))
    files.sort()
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, full in files:
            zi = zipfile.ZipInfo(arc, date_time=FIXED_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            with open(full, "rb") as f:
                z.writestr(zi, f.read())
    return hashlib.sha1(open(out_zip, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "build"))
    ap.add_argument("--only", help="comma-separated module keys to build (default: all + AIO)")
    ap.add_argument("--zip", action="store_true", help="also produce deterministic .zip per pack")
    args = ap.parse_args()

    m = json.load(open(MANIFEST))
    items = list(m["items"].values()) if isinstance(m["items"], dict) else m["items"]
    by_mod = {}
    for it in items:
        by_mod.setdefault(it["module"], []).append(it)

    os.makedirs(args.out, exist_ok=True)
    only = set(args.only.split(",")) if args.only else None
    dirs, shas = [], {}
    for mod, mod_meta in m["modules"].items():
        if only and mod not in only:
            continue
        d = build_module(mod, mod_meta, sorted(by_mod[mod], key=lambda i: (i.get("branch", 0), i.get("chain_pos", 0))),
                         m["grand_capstone"], items, args.out)
        dirs.append(d)
        n = sum(len(fs) for _, _, fs in os.walk(d))
        print("  built %-28s %3d files" % ("ninefold_%s" % mod, n))
        if args.zip:
            shas["ninefold_%s" % mod] = zip_pack(d, "%s-%s.zip" % (d, m["version"]))

    if not only:
        aio = build_aio(dirs, args.out, m["project"])
        n = sum(len(fs) for _, _, fs in os.walk(aio))
        print("  built %-28s %3d files (union)" % ("ninefold (AIO)", n))
        if args.zip:
            shas["ninefold"] = zip_pack(aio, "%s-%s.zip" % (aio, m["version"]))

    if shas:
        print("\n  deterministic SHA-1:")
        for k in sorted(shas):
            print("    %-24s %s" % (k, shas[k]))


if __name__ == "__main__":
    main()
