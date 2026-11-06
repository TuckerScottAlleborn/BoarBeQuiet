# BoarBeQuiet

BoarBeQuiet is an addon for World of Warcraft: Forever. It mutes the boar squeal and the rest of the boar voice. Footsteps and weapon hits still play.

## What it does

- It mutes the 11 voice files of the boar: the squeal at the start of a fight, the attack grunts, the wound sounds and the death sound. Pigs use the same voice, so the pig voice is muted too.
- It mutes the squeal of the spell Polymorph (Pig). No other spell plays that file.
- It also mutes the 26 files of a second boar voice. No creature uses that voice on build 70790. The mute is there in case a hotfix gives a boar that voice.
- `/bbq charge on` also mutes the two spell sounds of the boar's Charge. Many other spells use the same two files, for example Taunt, Growl, Challenging Shout, and Demoralizing Shout and Roar. Thus this option is off by default.
- `/bbq swap <sound>` plays a different sound when the player's own boar pet uses Charge. The sound can be a SoundKit ID, a `SOUNDKIT` name such as `READY_CHECK`, or a file path such as `Interface\AddOns\BoarBeQuiet\swap.ogg`. The command plays the sound once as a preview. If the game does not play it, the old setting stays.

## Limits

- The game has no API that replaces a sound file. A swap is a mute plus a second sound.
- The swap works only for the player's own pet. The game makes the cast data of each other unit secret (the `SecretWhenUnitSpellCastRestricted` rule), so an addon cannot see a wild boar's Charge.
- A mute lasts through `/reload` and a relog, but not through a client restart. The addon mutes again at each load.
- If the addon is turned off in the AddOns list, the boar stays silent until the client restarts. Run `/bbq off` first to hear the boar at once.
- A swap file must be in place before login or `/reload`. Put the file in the addon folder, run `/reload`, and then run `/bbq swap` with its path.
- The preview needs the game sound on. If the sound channel is muted, the game does not play the preview, and the command keeps the old setting.

## Commands

| Command | Result |
|---|---|
| `/bbq` | Shows the state and the commands. |
| `/bbq on`, `/bbq off` | Turns all mutes on or off. Off unmutes each file that the addon muted. |
| `/bbq charge on`, `/bbq charge off` | Mutes or unmutes the shared Charge spell sounds. |
| `/bbq swap <sound>`, `/bbq swap off` | Sets or clears the swap sound for the pet's Charge. |
| `/bbq debug` | Turns the debug log on or off. The log records the load, the login and each Charge of the pet. It goes to `SavedVariables\BoarBeQuiet.lua` on `/reload` or logout. |

`/boarbequiet` is the long form of `/bbq`.

## Where the sound IDs come from

The IDs come from the client data of Forever build 1.60.1.70790, through the wago.tools DB2 exports. `Core.lua` lists each file with its path. The data paths are:

- Creature voice: `CreatureModelData.SoundID` 66 (boar.m2 and pig.m2) to `CreatureSoundData` 66 to `SoundKitEntry` to the FileDataID. No boar or pig display has its own `SoundID`.
- Spell sound: `SpellXSpellVisual` to `SpellVisualEvent` to `SpellVisualKitEffect` with `EffectType` 5 (a sound kit) to `SoundKitEntry`.
- Coverage: each sound file with "boar", "pig" or "hog" in its path was checked against the Forever sound kits. The files in a kit are the boar.m2 voice, the unused second boar voice, the Polymorph (Pig) squeal, quillboar voices, and doodad or ambient sounds. The addon mutes the first three groups.
- The pet's Charge: the "Pet - Boar" skill line (211) teaches the six ranks in `PET_CHARGE`.

## Tests

Run `python tests/test_core.py`. It needs `pip install lupa`, which embeds Lua 5.1, the Lua version of the game. The 30 tests load `Core.lua` with stubs for the game API, fire the game events, and run each command. A pass proves the logic. It does not prove the behavior in the game. Four broken copies of `Core.lua` made the tests fail, so the tests can catch a fault. GitHub Actions runs the tests on each push.

## Releases

A tag starts a release, for example `git tag v1.0.0` and then `git push origin v1.0.0`. GitHub Actions runs the tests. Then the BigWigs packager builds the zip, puts the tag in `## Version`, and attaches the zip to a GitHub release. The zip does not include the `tests` folder.

The packager also uploads the zip to CurseForge when both of these are in place:

- The TOC has the line `## X-Curse-Project-ID: <id>`, with the ID of the CurseForge project.
- The repository has a secret `CF_API_KEY` with a CurseForge API token.

## What a live test showed

On 2026-11-06 the addon ran in the Forever client 1.60.1 on a hunter with a boar pet. The test had three sessions, and !BugGrabber was on for all of them.

- BugGrabber recorded no Lua error from the addon. The load, the login and each pet cast ran without a fault.
- The addon saw each Charge of the pet: 10 casts of rank 1 (7371). It ignored the pet's Growl (14916). Thus the cast data of the pet is not secret, as the code expects.
- The tester reports that the addon works when the pet uses Charge.

## What is not verified

- Nobody has heard a wild boar with the addon on. A wild boar uses the same voice files as the pet (`CreatureSoundData` 66), so it is most likely quiet too.
- The squeal is `sound/creature/boar/mwildboaraggro1.ogg` (545134). A spectrogram of the file shows a squeal. If a boar still squeals with the addon on, the source is a file that is not on the list.
- `/bbq swap` and `/bbq charge on` have not run in a live client.
- Server hotfixes can change the sound data, and the DB2 exports do not include them.

## License

MIT. See `LICENSE`.
