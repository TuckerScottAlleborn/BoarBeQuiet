# BoarBeQuiet

BoarBeQuiet is an addon for World of Warcraft: Forever. It mutes the boar squeal and the rest of the boar voice. Footsteps and weapon hits still play.

## What it does

- It mutes the 11 voice files of the boar: the squeal at the start of a fight, the attack grunts, the wound sounds and the death sound. Pigs use the same voice, so the pig voice is muted too.
- It mutes the squeal of the spell Polymorph (Pig). No other spell plays that file.
- It also mutes the 26 files of a second boar voice. No creature uses that voice on build 70790. The mute is there in case a hotfix gives a boar that voice.

## Commands

The addon has one switch. It mutes all of the sounds above, or none of them.

| Command | Result |
|---|---|
| `/bbq` | Shows the state and the commands. |
| `/bbq on` | Mutes all of the sounds. This is the default. |
| `/bbq off` | Unmutes all of the sounds. |

`/boarbequiet` is the long form of `/bbq`.

## Limits

- A mute lasts through `/reload` and a relog, but not through a client restart. The addon mutes again at each load.
- If the addon is turned off in the AddOns list, the boar stays silent until the client restarts. Run `/bbq off` first to hear the boar at once.

## Future enhancements

Version 1.0.0 tried two more features. In a live test the Charge mute did not work, so version 1.1.0 keeps only the one switch. The code of both is in the tag `v1.0.0`. A later version can add them again:

- **Muting specific sounds.** A setting for each sound, for example the sound of the boar's Charge, in addition to the main switch. Version 1.0.0 muted `sound/spells/challengingshout.ogg` (569236) and `sound/spells/taunt.ogg` (568268) for the Charge, the two files of SpellVisual 519. In the live test the Charge sound still played, so the sound comes from a different file. Growl, Taunt, Challenging Shout, Demoralizing Shout and Roar, Battle Cry, Piercing Howl and Cower also play those two files. Thus a good mute needs a file that only Charge plays.
- **Replacement sounds.** Play a sound of the player's choice in place of a muted sound. Version 1.0.0 did this for the Charge of the player's own boar pet (`/bbq swap <sound>`). The live test showed that an addon can see the pet's Charge: the addon saw 10 casts of rank 1 (7371), and it ignored Growl (14916). The game makes the cast data of other units secret, so a replacement for a spell can work only for the player's own pet. The game has no API that replaces a sound file, so a replacement is always a mute plus a second sound.

## Contributing

Help is welcome, most of all with finding sound files. Both future enhancements need the FileDataID of each sound, and the Charge sound is the first one to find.

1. Look for candidate files in the Forever client data, for example in the wago.tools DB2 tables in "Where the sound IDs come from".
2. Test a file in the game. `/run MuteSoundFile(<FileDataID>)` mutes one file until the client restarts, and `/run UnmuteSoundFile(<FileDataID>)` unmutes it. If the sound stops, that is the file.
3. Open an issue or a pull request with the FileDataID, the file path and the sound that it plays. Run `python tests/test_core.py` before a pull request.

Code changes are welcome too. Please keep the main switch as the default behavior.

## Where the sound IDs come from

The IDs come from the client data of Forever build 1.60.1.70790, through the wago.tools DB2 exports. `Core.lua` lists each file with its path. The data paths are:

- Creature voice: `CreatureModelData.SoundID` 66 (boar.m2 and pig.m2) to `CreatureSoundData` 66 to `SoundKitEntry` to the FileDataID. No boar or pig display has its own `SoundID`.
- Spell sound: `SpellXSpellVisual` to `SpellVisualEvent` to `SpellVisualKitEffect` with `EffectType` 5 (a sound kit) to `SoundKitEntry`.
- Coverage: each sound file with "boar", "pig" or "hog" in its path was checked against the Forever sound kits. The files in a kit are the boar.m2 voice, the unused second boar voice, the Polymorph (Pig) squeal, quillboar voices, and doodad or ambient sounds. The addon mutes the first three groups.

## Tests

Run `python tests/test_core.py`. It needs `pip install lupa`, which embeds Lua 5.1, the Lua version of the game. The 14 tests load `Core.lua` with stubs for the game API, fire the game events, and run each command. A pass proves the logic. It does not prove the behavior in the game. Four broken copies of `Core.lua` made the tests fail, so the tests can catch a fault. GitHub Actions runs the tests on each push.

## Releases

A tag starts a release, for example `git tag v1.2.0` and then `git push origin v1.2.0`. GitHub Actions runs the tests. Then the BigWigs packager builds the zip, puts the tag in `## Version`, and attaches the zip to a GitHub release. The zip does not include the `tests` folder.

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
