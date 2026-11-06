-- BoarBeQuiet for World of Warcraft: Forever.
-- Mutes the boar squeal and the other boar voice sounds. /bbq on and /bbq off
-- turn the mute on and off.
local addonName, ns = ...

-- The sound facts come from the client data of Forever build 1.60.1.70790
-- (wago.tools DB2 exports, checked on 2026-11-06):
-- * boar.m2 and pig.m2 take their voice from CreatureSoundData 66. All 33
--   boar.m2 displays and all 4 pig.m2 displays use it. Of the creature sound
--   sets and spell visuals, only that set plays these files, so the mute
--   silences boars and pigs and no other creature.
-- * The aggro sound 545134 plays at the start of a boar fight. Its spectrogram
--   is a stack of rising harmonics for about 1.6 seconds, so it is most likely
--   the squeal.
-- * Aggro 2 and aggro 3 are in no sound kit on this build. The addon mutes
--   them in case a server hotfix adds them.
-- * CreatureSoundData 10432 is a second boar voice (the "maldraxxus boar"
--   files). No creature model or display on this build uses it, so these
--   files do not play now. The addon mutes them in case a hotfix gives a
--   boar this voice. Only that sound set holds these files.
-- MuteSoundFile works on a FileDataID. A mute lasts through /reload and a
-- relog, but not through a client restart, so the addon mutes at each load.
local VOICE_FILES = {
    545134, -- sound/creature/boar/mwildboaraggro1.ogg (the squeal)
    545133, -- sound/creature/boar/mwildboaraggro2.ogg
    545128, -- sound/creature/boar/mwildboaraggro3.ogg
    545136, -- sound/creature/boar/mwildboarattack1.ogg
    545135, -- sound/creature/boar/mwildboarattack2.ogg
    545129, -- sound/creature/boar/mwildboarattack3.ogg
    545137, -- sound/creature/boar/mwildboarwound1.ogg
    545127, -- sound/creature/boar/mwildboarwound2.ogg
    545131, -- sound/creature/boar/mwildboarwound3.ogg
    545130, -- sound/creature/boar/mwildboarwoundcritical1.ogg
    545132, -- sound/creature/boar/mwildboardeath1.ogg
    -- sound/creature/maldraxxusboar/mon_maldraxxusboar_<kind>_<n>_<kit>.ogg
    3597806, 3597808, 3597810, -- aggro 00 to 02
    3597868, 3597870, 3597872, -- alert 00 to 02
    3597818, 3597820, 3597822, 3597824, 3597826, 3597828, 3597830, -- attack 00 to 06
    3597848, 3597850, 3597852, -- death 00 to 02
    3597884, 3597886, 3597888, 3597890, 3597892, 3597894, 3597896, -- wound 00 to 06
    3597878, 3597880, 3597882, -- woundcritical 00 to 02
    -- A similar squeal from a spell. Only Polymorph (Pig), spell 28272, plays
    -- this file (sound kit 3036), so the mute touches no other spell.
    568873, -- sound/spells/polymorphpig.ogg
}

local DEFAULTS = {
    enabled = true,
}

-- Settings from version 1.0.0, which had the Charge mute, the swap sound and
-- the debug log. The load removes them from the saved table.
local OLD_KEYS = { "charge", "swap", "debug", "log" }

--- Mutes or unmutes each voice file.
-- @param mute boolean True mutes the files. False unmutes them.
local function setMuted(mute)
    local apply = UnmuteSoundFile
    if mute then
        apply = MuteSoundFile
    end
    for _, fileID in ipairs(VOICE_FILES) do
        apply(fileID)
    end
end

--- Turns the mute on or off. Off unmutes each file that the addon muted.
-- @param on boolean The new state.
local function setEnabled(on)
    if ns.db.enabled == on then
        return
    end
    ns.db.enabled = on
    setMuted(on)
end

--- Prints the state and the commands.
local function printStatus()
    if ns.db.enabled then
        print(addonName .. ": on. Boar and pig voices are muted.")
    else
        print(addonName .. ": off. Boar and pig voices play.")
    end
    print("  Commands: /bbq on, /bbq off")
end

local frame = CreateFrame("Frame")

--- Loads the saved table and mutes the boar. SavedVariables do not exist
-- until ADDON_LOADED fires for this addon.
-- @param _ table The frame. This function does not use it.
-- @param event string The event name.
-- @param loadedName string The name of the addon that loaded.
frame:SetScript("OnEvent", function(_, event, loadedName)
    if event ~= "ADDON_LOADED" or loadedName ~= addonName then
        return
    end
    frame:UnregisterEvent("ADDON_LOADED")
    BoarBeQuietDB = BoarBeQuietDB or {}
    ns.db = BoarBeQuietDB
    for _, key in ipairs(OLD_KEYS) do
        ns.db[key] = nil
    end
    for key, value in pairs(DEFAULTS) do
        if ns.db[key] == nil then
            ns.db[key] = value
        end
    end
    if ns.db.enabled then
        setMuted(true)
    end
end)
frame:RegisterEvent("ADDON_LOADED")

SLASH_BOARBEQUIET1 = "/bbq"
SLASH_BOARBEQUIET2 = "/boarbequiet"

--- Handles the slash command.
-- @param message string The text after the command.
SlashCmdList.BOARBEQUIET = function(message)
    local command = strtrim(message or ""):lower()
    if command == "on" then
        setEnabled(true)
    elseif command == "off" then
        setEnabled(false)
    end
    printStatus()
end
