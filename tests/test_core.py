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
SQUEAL = 545134
POLYMORPH_PIG = 568873
OLD_CHARGE_FILES = [569236, 568268]  # muted by /bbq charge on in version 1.0.0

STUBS = r"""
calls = { mute = {}, unmute = {}, sounds = 0, printed = {} }

function print(...)
    local parts = {}
    for i = 1, select("#", ...) do parts[i] = tostring((select(i, ...))) end
    calls.printed[#calls.printed + 1] = table.concat(parts, " ")
end
function MuteSoundFile(id) calls.mute[#calls.mute + 1] = id end
function UnmuteSoundFile(id) calls.unmute[#calls.unmute + 1] = id end
function PlaySound() calls.sounds = calls.sounds + 1; return true end
function PlaySoundFile() calls.sounds = calls.sounds + 1; return true end
function strtrim(s) return (s:gsub("^%s+", ""):gsub("%s+$", "")) end
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
            self.g.BoarBeQuietDB = self.to_lua(saved)

    def to_lua(self, value):
        if isinstance(value, dict):
            return self.lua.table_from({k: self.to_lua(v) for k, v in value.items()})
        if isinstance(value, list):
            return self.lua.table_from([self.to_lua(v) for v in value])
        return value

    def load(self):
        self.g.fire("ADDON_LOADED", "BoarBeQuiet")

    def fire(self, event, *args):
        self.g.fire(event, *args)

    def command(self, text):
        self.g.SlashCmdList.BOARBEQUIET(text)

    @staticmethod
    def _list(table):
        return [table[i] for i in range(1, len(table) + 1)]

    @property
    def db(self):
        return self.g.BoarBeQuietDB

    @property
    def muted(self):
        return self._list(self.g.calls.mute)

    @property
    def unmuted(self):
        return self._list(self.g.calls.unmute)

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

    def test_load_turns_the_mute_on_by_default(self):
        a = Addon()
        a.load()
        self.assertTrue(a.db.enabled)

    def test_load_keeps_a_saved_off(self):
        a = Addon({"enabled": False})
        a.load()
        self.assertFalse(a.db.enabled)
        self.assertEqual(a.muted, [])

    def test_load_removes_the_settings_of_version_1_0_0(self):
        a = Addon({"enabled": True, "charge": True, "swap": 12345, "debug": True,
                   "log": ["12:00:00 pet cast 7371 Charge"]})
        a.load()
        for key in ("charge", "swap", "debug", "log"):
            self.assertIsNone(a.db[key], key)
        self.assertTrue(a.db.enabled)
        self.assertEqual(len(a.muted), VOICE_COUNT)
        for file_id in OLD_CHARGE_FILES:
            self.assertNotIn(file_id, a.muted)

    def test_other_addon_load_is_ignored(self):
        a = Addon()
        a.fire("ADDON_LOADED", "SomeOtherAddon")
        self.assertIsNone(a.db)
        self.assertEqual(a.muted, [])

    def test_only_addon_loaded_is_registered(self):
        a = Addon()
        frame = a.g.frame
        self.assertEqual(list(frame.events.keys()), ["ADDON_LOADED"])
        self.assertEqual(len(list(frame.unitEvents.keys())), 0)
        a.load()
        self.assertIsNone(frame.events["ADDON_LOADED"])

    def test_other_events_are_ignored(self):
        a = Addon()
        a.load()
        a.fire("PLAYER_LOGIN")
        a.fire("UNIT_SPELLCAST_SUCCEEDED", "pet", "cast-guid", 7371)
        self.assertEqual(len(a.muted), VOICE_COUNT)
        self.assertEqual(a.g.calls.sounds, 0)


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
        self.assertEqual(a.printed[-2], "BoarBeQuiet: off. Boar and pig voices play.")
        a.command("on")
        self.assertTrue(a.db.enabled)
        self.assertEqual(len(a.muted), 2 * VOICE_COUNT)
        self.assertEqual(a.printed[-2], "BoarBeQuiet: on. Boar and pig voices are muted.")

    def test_on_while_on_changes_nothing(self):
        self.a.command("on")
        self.assertEqual(len(self.a.muted), VOICE_COUNT)

    def test_off_while_off_changes_nothing(self):
        a = self.a
        a.command("off")
        a.command("off")
        self.assertEqual(len(a.unmuted), VOICE_COUNT)

    def test_commands_ignore_case_and_spaces(self):
        self.a.command("  OFF ")
        self.assertFalse(self.a.db.enabled)

    def test_status_lists_the_commands(self):
        a = self.a
        for text in ("", "nonsense"):
            a.command(text)
            self.assertEqual(a.printed[-2:], ["BoarBeQuiet: on. Boar and pig voices are muted.",
                                              "  Commands: /bbq on, /bbq off"])

    def test_commands_of_version_1_0_0_do_nothing(self):
        a = self.a
        for text in ("charge on", "swap 12345", "swap off", "debug"):
            a.command(text)
        self.assertEqual(len(a.muted), VOICE_COUNT)
        self.assertEqual(a.unmuted, [])
        self.assertEqual(a.g.calls.sounds, 0)
        for key in ("charge", "swap", "debug"):
            self.assertIsNone(a.db[key], key)


if __name__ == "__main__":
    unittest.main(verbosity=2)
