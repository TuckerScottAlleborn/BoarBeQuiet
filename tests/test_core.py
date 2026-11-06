"""Tests for Core.lua.

The tests run Core.lua in Lua 5.1, the Lua version of the game, with stubs for
the game API. A pass proves the logic. It does not prove the behavior in the game.

Run: python tests/test_core.py
Needs: pip install lupa
Set BBQ_CORE to the path of another Core.lua to test that copy instead.
"""
import os
import unittest

from lupa import lua51

CORE = os.environ.get("BBQ_CORE") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "Core.lua")

VOICE_COUNT = 38  # 11 boar.m2 voice files + 26 second boar voice + Polymorph (Pig)
CHARGE_FILES = [569236, 568268]
CHARGE_RANKS = [7371, 26177, 26178, 26179, 26201, 27685]
SQUEAL = 545134
POLYMORPH_PIG = 568873
GROWL = 14916

STUBS = r"""
calls = { mute = {}, unmute = {}, playsound = {}, playfile = {}, printed = {} }
secret = {}          -- issecretvalue flags this one value
play_ok = true       -- what PlaySound and PlaySoundFile return
play_error = nil     -- when set, PlaySound and PlaySoundFile raise it

function issecretvalue(v) return v == secret end
function date() return "12:00:00" end
function print(...)
    local parts = {}
    for i = 1, select("#", ...) do parts[i] = tostring((select(i, ...))) end
    calls.printed[#calls.printed + 1] = table.concat(parts, " ")
end
function MuteSoundFile(id) calls.mute[#calls.mute + 1] = id end
function UnmuteSoundFile(id) calls.unmute[#calls.unmute + 1] = id end
function PlaySound(id)
    if play_error then error(play_error) end
    calls.playsound[#calls.playsound + 1] = id
    return play_ok
end
function PlaySoundFile(path, channel)
    if play_error then error(play_error) end
    calls.playfile[#calls.playfile + 1] = path .. "|" .. tostring(channel)
    return play_ok
end
SOUNDKIT = { READY_CHECK = 8960 }
function strtrim(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end
-- The live client returns extra values after these four.
function GetBuildInfo() return "1.60.1", "70790", "Oct 30 2026", 16001, "", "" end
C_AddOns = { GetAddOnMetadata = function() return "@project-version@" end }
SlashCmdList = {}

frame = nil
function CreateFrame()
    local f = { events = {}, unitEvents = {} }
    function f:RegisterEvent(e) self.events[e] = true end
    function f:RegisterUnitEvent(e, unit) self.unitEvents[e] = unit end
    function f:UnregisterEvent(e) self.events[e] = nil end
    function f:SetScript(_, fn) self.onEvent = fn end
    frame = f
    return f
end
function fire(event, ...) frame.onEvent(frame, event, ...) end
"""


class Addon:
    """One fresh copy of the addon in its own Lua state."""

    def __init__(self, saved=None):
        self.lua = lua51.LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(STUBS)
        self.g = self.lua.globals()
        compile_chunk = self.lua.eval(
            "function(src) local f, err = loadstring(src, '=Core.lua')"
            " if not f then error(err) end return f end")
        with open(CORE, encoding="utf-8") as fh:
            compile_chunk(fh.read())("BoarBeQuiet", self.lua.table())
        if saved is not None:
            self.g.BoarBeQuietDB = self.lua.table_from(saved)

    def load(self):
        self.g.fire("ADDON_LOADED", "BoarBeQuiet")

    def fire(self, event, *args):
        self.g.fire(event, *args)

    def pet_cast(self, spell_id):
        self.g.fire("UNIT_SPELLCAST_SUCCEEDED", "pet", "cast-guid", spell_id)

    def command(self, text):
        self.g.SlashCmdList.BOARBEQUIET(text)

    @staticmethod
    def _list(table):
        return [table[i] for i in range(1, len(table) + 1)]

    @property
    def db(self):
        return self.g.BoarBeQuietDB

    @property
    def log(self):
        return self._list(self.db.log)

    @property
    def muted(self):
        return self._list(self.g.calls.mute)

    @property
    def unmuted(self):
        return self._list(self.g.calls.unmute)

    @property
    def sounds(self):
        return self._list(self.g.calls.playsound)

    @property
    def files(self):
        return self._list(self.g.calls.playfile)

    @property
    def printed(self):
        return self._list(self.g.calls.printed)


class LoadTests(unittest.TestCase):
    def test_load_mutes_each_voice_file_once(self):
        a = Addon()
        a.load()
        self.assertEqual(len(a.muted), VOICE_COUNT)
        self.assertEqual(len(set(a.muted)), VOICE_COUNT)
        self.assertIn(SQUEAL, a.muted)
        self.assertIn(POLYMORPH_PIG, a.muted)
        self.assertEqual(a.unmuted, [])

    def test_load_sets_defaults(self):
        a = Addon()
        a.load()
        self.assertEqual((a.db.enabled, a.db.charge, a.db.swap, a.db.debug),
                         (True, False, False, False))

    def test_load_keeps_saved_settings(self):
        a = Addon({"enabled": False, "swap": 12345})
        a.load()
        self.assertEqual(a.muted, [])
        self.assertEqual(a.db.swap, 12345)

    def test_saved_charge_setting_mutes_charge_files(self):
        a = Addon({"charge": True})
        a.load()
        self.assertEqual(len(a.muted), VOICE_COUNT + len(CHARGE_FILES))
        for file_id in CHARGE_FILES:
            self.assertIn(file_id, a.muted)

    def test_other_addon_load_is_ignored(self):
        a = Addon()
        a.fire("ADDON_LOADED", "SomeOtherAddon")
        self.assertIsNone(a.db)
        self.assertEqual(a.muted, [])

    def test_pet_cast_before_load_does_nothing(self):
        a = Addon()
        a.pet_cast(CHARGE_RANKS[0])
        self.assertIsNone(a.db)

    def test_events(self):
        a = Addon()
        events = a.g.frame.events
        self.assertTrue(events["ADDON_LOADED"])
        self.assertTrue(events["PLAYER_LOGIN"])
        self.assertEqual(a.g.frame.unitEvents["UNIT_SPELLCAST_SUCCEEDED"], "pet")
        a.load()
        self.assertIsNone(events["ADDON_LOADED"])


class LogTests(unittest.TestCase):
    def test_no_log_without_debug(self):
        a = Addon()
        a.load()
        a.fire("PLAYER_LOGIN")
        a.pet_cast(CHARGE_RANKS[0])
        self.assertEqual(a.log, [])

    def test_log_records_load_login_and_charge_but_not_growl(self):
        a = Addon({"debug": True})
        a.load()
        a.fire("PLAYER_LOGIN")
        a.pet_cast(GROWL)
        a.pet_cast(7371)
        self.assertEqual(a.log, [
            "12:00:00 loaded @project-version@ enabled true charge false swap false",
            "12:00:00 login 1.60.1 70790 16001",
            "12:00:00 pet cast 7371 Charge",
        ])

    def test_each_charge_rank_is_logged(self):
        a = Addon({"debug": True})
        a.load()
        for rank in CHARGE_RANKS:
            a.pet_cast(rank)
        self.assertEqual(a.log[1:], ["12:00:00 pet cast %d Charge" % r for r in CHARGE_RANKS])

    def test_secret_spell_id_is_logged_and_plays_nothing(self):
        a = Addon({"debug": True, "swap": 12345})
        a.load()
        a.pet_cast(a.g.secret)
        self.assertEqual(a.log[-1], "12:00:00 pet cast <secret>")
        self.assertEqual(a.sounds, [])

    def test_log_keeps_the_last_200_lines(self):
        a = Addon({"debug": True})
        a.load()
        for _ in range(250):
            a.pet_cast(CHARGE_RANKS[0])
        self.assertEqual(len(a.log), 200)
        self.assertNotIn("loaded", a.log[0])


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.a = Addon()
        self.a.load()

    def test_slash_command_names(self):
        self.assertEqual(self.a.g.SLASH_BOARBEQUIET1, "/bbq")
        self.assertEqual(self.a.g.SLASH_BOARBEQUIET2, "/boarbequiet")

    def test_off_unmutes_each_muted_file_and_on_mutes_again(self):
        a = self.a
        muted_at_load = list(a.muted)
        a.command("off")
        self.assertFalse(a.db.enabled)
        self.assertEqual(sorted(a.unmuted), sorted(muted_at_load))
        a.command("on")
        self.assertTrue(a.db.enabled)
        self.assertEqual(len(a.muted), 2 * VOICE_COUNT)

    def test_on_while_on_changes_nothing(self):
        self.a.command("on")
        self.assertEqual(len(self.a.muted), VOICE_COUNT)

    def test_off_also_unmutes_charge_files(self):
        a = self.a
        a.command("charge on")
        a.command("off")
        self.assertEqual(len(a.unmuted), VOICE_COUNT + len(CHARGE_FILES))

    def test_charge_on_and_off(self):
        a = self.a
        a.command("charge on")
        self.assertTrue(a.db.charge)
        self.assertEqual(a.muted[-2:], CHARGE_FILES)
        a.command("charge off")
        self.assertFalse(a.db.charge)
        self.assertEqual(a.unmuted, CHARGE_FILES)

    def test_charge_while_off_waits_for_on(self):
        a = self.a
        a.command("off")
        muted_before = len(a.muted)
        a.command("charge on")
        self.assertTrue(a.db.charge)
        self.assertEqual(len(a.muted), muted_before)
        a.command("on")
        self.assertEqual(a.muted[-2:], CHARGE_FILES)

    def test_commands_ignore_case_and_spaces(self):
        self.a.command("  CHARGE   On ")
        self.assertTrue(self.a.db.charge)

    def test_swap_soundkit_id_previews_then_plays_on_charge_only(self):
        a = self.a
        a.command("swap 12345")
        self.assertEqual(a.db.swap, 12345)
        self.assertEqual(a.sounds, [12345])
        a.pet_cast(GROWL)
        self.assertEqual(a.sounds, [12345])
        a.pet_cast(CHARGE_RANKS[0])
        self.assertEqual(a.sounds, [12345, 12345])

    def test_swap_soundkit_name(self):
        self.a.command("swap ready_check")
        self.assertEqual(self.a.db.swap, 8960)
        self.assertEqual(self.a.sounds, [8960])

    def test_swap_file_path_plays_on_sfx_channel(self):
        path = r"Interface\AddOns\BoarBeQuiet\swap.ogg"
        self.a.command("swap " + path)
        self.assertEqual(self.a.db.swap, path)
        self.assertEqual(self.a.files, [path + "|SFX"])

    def test_swap_preview_not_played_keeps_old_swap(self):
        a = self.a
        a.command("swap 12345")
        a.g.play_ok = False
        a.command("swap 999")
        self.assertEqual(a.db.swap, 12345)
        self.assertIn("did not play 999", a.printed[-1])

    def test_swap_preview_error_keeps_old_swap(self):
        a = self.a
        a.g.play_error = "boom"
        a.command("swap 999")
        self.assertFalse(a.db.swap)
        self.assertIn("boom", a.printed[-1])

    def test_swap_error_on_charge_turns_swap_off(self):
        a = self.a
        a.command("swap 12345")
        a.g.play_error = "boom"
        a.pet_cast(CHARGE_RANKS[0])
        self.assertFalse(a.db.swap)
        self.assertIn("Swap is now off", a.printed[-1])

    def test_swap_does_not_play_while_off(self):
        a = self.a
        a.command("swap 12345")
        a.command("off")
        a.pet_cast(CHARGE_RANKS[0])
        self.assertEqual(a.sounds, [12345])

    def test_swap_off(self):
        a = self.a
        a.command("swap 12345")
        a.command("swap off")
        self.assertFalse(a.db.swap)
        a.pet_cast(CHARGE_RANKS[0])
        self.assertEqual(a.sounds, [12345])

    def test_swap_without_a_sound_prints_help(self):
        self.a.command("swap")
        self.assertFalse(self.a.db.swap)
        self.assertIn("give a SoundKit ID", self.a.printed[-1])

    def test_debug_toggles(self):
        a = self.a
        a.command("debug")
        self.assertTrue(a.db.debug)
        self.assertEqual(a.printed[-1], "BoarBeQuiet: debug on")
        a.command("debug")
        self.assertFalse(a.db.debug)

    def test_status_and_unknown_command_print_the_state(self):
        a = self.a
        for text in ("", "nonsense"):
            a.command(text)
            self.assertIn("BoarBeQuiet: on. Boar and pig voices are muted.", a.printed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
