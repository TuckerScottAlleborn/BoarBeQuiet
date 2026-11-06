# BoarBeQuiet

BoarBeQuiet is an addon for World of Warcraft: Forever. It mutes the boar squeal and the rest of the boar voice. Footsteps and weapon hits still play.

## What it does

- It mutes the 11 voice files of the boar: the squeal at the start of a fight, the attack grunts, the wound sounds and the death sound. Pigs use the same voice, so the pig voice is muted too.
- It mutes the squeal of the spell Polymorph (Pig). No other spell plays that file.
- It also mutes the 26 files of a second boar voice. No creature uses that voice on build 70790. The mute is there in case a hotfix gives a boar that voice.

## Commands

| Command | Result |
|---|---|
| `/bbq` | Shows the state and the commands. |
| `/bbq on`, `/bbq off` | Turns the mute on or off. Off unmutes each file that the addon muted. |

`/boarbequiet` is the long form of `/bbq`.

## Limits

- A mute lasts through `/reload` and a relog, but not through a client restart. The addon mutes again at each load.
- If the addon is turned off in the AddOns list, the boar stays silent until the client restarts. Run `/bbq off` first to hear the boar at once.

## Future enhancements

Version 1.0.0 had two more features. In a live test the first one did not work, so version 1.1.0 keeps only the main mute. The code of both is in the tag `v1.0.0`.

- **A mute for the sound of the boar's Charge.** `/bbq charge on` muted `sound/spells/challengingshout.ogg` (569236) and `sound/spells/taunt.ogg` (568268), the two files of SpellVisual 519. In the live test the Charge sound still played, so the sound comes from a file that is not on that list. Growl, Taunt, Challenging Shout, Demoralizing Shout and Roar, Battle Cry, Piercing Howl and Cower also play those two files. Thus a good mute needs a file that only Charge plays.
- **A swap sound for the pet's Charge.** `/bbq swap <sound>` played a SoundKit ID, a `SOUNDKIT` name or a file when the player's own boar pet used Charge. The live test showed that an addon can see the pet's Charge: the addon saw 10 casts of rank 1 (7371), and it ignored Growl (14916). The game makes the cast data of other units secret, so a swap can work only for the player's own pet. The game has no API that replaces a sound file, so a true swap needs the Charge mute and a second sound.

## Where the sound IDs come from

The IDs come from the client data of Forever build 1.60.1.70790, through the wago.tools DB2 exports. `Core.lua` lists each file with its path. The data paths are:

- Creature voice: `CreatureModelData.SoundID` 66 (boar.m2 and pig.m2) to `CreatureSoundData` 66 to `SoundKitEntry` to the FileDataID. No boar or pig display has its own `SoundID`.
- Spell sound: `SpellXSpellVisual` to `SpellVisualEvent` to `SpellVisualKitEffect` with `EffectType` 5 (a sound kit) to `SoundKitEntry`.
- Coverage: each sound file with "boar", "pig" or "hog" in its path was checked against the Forever sound kits. The files in a kit are the boar.m2 voice, the unused second boar voice, the Polymorph (Pig) squeal, quillboar voices, and doodad or ambient sounds. The addon mutes the first three groups.

## Tests

Run `python tests/test_core.py`. It needs `pip install lupa`, which embeds Lua 5.1, the Lua version of the game. The 14 tests load `Core.lua` with stubs for the game API, fire the game events, and run each command. A pass proves the logic. It does not prove the behavior in the game. Four broken copies of `Core.lua` made the tests fail, so the tests can catch a fault. GitHub Actions runs the tests on each push.

## Releases

A tag starts a release, for example `git tag v1.1.0` and then `git push origin v1.1.0`. GitHub Actions runs the tests. Then the BigWigs packager builds the zip, puts the tag in `## Version`, and attaches the zip to a GitHub release. The zip does not include the `tests` folder.

The packager also uploads the zip to CurseForge when both of these are in place:

- The TOC has the line `## X-Curse-Project-ID: <id>`, with the ID of the CurseForge project.
- The repository has a secret `CF_API_KEY` with a CurseForge API token.

## What a live test showed

On 2026-11-06 version 1.0.0 ran in the Forever client 1.60.1 on a hunter with a boar pet. The test had three sessions, and !BugGrabber was on for all of them.

- BugGrabber recorded no Lua error from the addon.
- The tester reports that `/bbq on` works: the boar is quiet.
- `/bbq charge on` did not silence the Charge sound. See "Future enhancements".

## What is not verified

- The tester checked the mute with a boar pet. A wild boar uses the same voice files (`CreatureSoundData` 66), so it is most likely quiet too.
- Server hotfixes can change the sound data, and the DB2 exports do not include them.

## License

MIT. See `LICENSE`.
