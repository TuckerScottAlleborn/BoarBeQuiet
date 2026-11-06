-- BoarBeQuiet for World of Warcraft: Forever.
-- Mutes the boar squeal and the other boar voice sounds. It can also play a
-- replacement sound when the player's own boar pet uses Charge.
local addonName, ns = ...

-- The sound facts come from the client data of Forever build 1.60.1.70790
-- (wago.tools DB2 exports, checked on 2026-11-06):
-- * boar.m2 and pig.m2 take their voice from CreatureSoundData 66. All 33
--   boar.m2 displays and all 4 pig.m2 displays use it. Of the creature sound
--   sets and spell visuals, only that set plays these files, so the mute
--   silences boars and pigs and no other creature.
-- * The aggro sound 545134 plays at the start of a boar fight. Its spectrogram
--   is a stack of rising harmonics for about 1.6 seconds, so it is most likely
--   the squeal. Nobody has heard it in a live client yet.
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

-- The spell sounds of the boar's Charge: SpellVisual 519, which the six ranks
-- of the pet's Charge and the mob buff Boar Charge (3385) use. Many other
-- spells play the same two files, so this group is off by default.
local CHARGE_FILES = {
    569236, -- sound/spells/challengingshout.ogg: also Challenging Shout, Battle Cry, Piercing Howl
    568268, -- sound/spells/taunt.ogg: also Taunt, Growl, Demoralizing Shout and Roar, Cower
}

-- The six ranks of the boar pet's Charge.
local PET_CHARGE = {
    [7371] = true,
    [26177] = true,
    [26178] = true,
    [26179] = true,
    [26201] = true,
    [27685] = true,
}

-- swap is false for silence, a number for a SoundKit ID, or a string for a file path.
local DEFAULTS = {
    enabled = true,
    charge = false,
    swap = false,
    debug = false,
}

local MAX_LOG_LINES = 200

--- Copies each missing default into the saved table.
-- @param db table The saved table.
-- @param defaults table The default values.
local function applyDefaults(db, defaults)
    for key, value in pairs(defaults) do
        if db[key] == nil then
            db[key] = value
        end
    end
end

--- Converts one value to text. A secret value never reaches tostring.
-- @param value any The value to describe.
-- @return string The text form.
local function describe(value)
    if issecretvalue(value) then
        return "<secret>"
    end
    return tostring(value)
end

--- Adds one line to the saved debug log. The log reaches disk on /reload or logout.
-- Logging must never break the addon, so the body runs inside pcall.
-- @param ... any The values to log.
function ns.log(...)
    if not (ns.db and ns.db.debug) then
        return
    end
    local args = { n = select("#", ...), ... }
    local ok, err = pcall(function()
        local parts = {}
        for i = 1, args.n do
            parts[i] = describe(args[i])
        end
        local log = ns.db.log
        log[#log + 1] = date("%H:%M:%S") .. " " .. table.concat(parts, " ")
        while #log > MAX_LOG_LINES do
            table.remove(log, 1)
        end
    end)
    if not ok then
        print(addonName .. ": ns.log failed: " .. tostring(err))
    end
end

--- Mutes or unmutes each file in a list.
-- @param files table The FileDataIDs.
-- @param mute boolean True mutes the files. False unmutes them.
local function setMuted(files, mute)
    local apply = UnmuteSoundFile
    if mute then
        apply = MuteSoundFile
    end
    for _, fileID in ipairs(files) do
        apply(fileID)
    end
end

--- Mutes each group that the settings turn on.
-- This function never unmutes, so it cannot undo a mute that another addon made.
local function applyMutes()
    if not ns.db.enabled then
        return
    end
    setMuted(VOICE_FILES, true)
    if ns.db.charge then
        setMuted(CHARGE_FILES, true)
    end
end

--- Turns the addon on or off. Off unmutes each file that the addon muted.
-- @param on boolean The new state.
local function setEnabled(on)
    if ns.db.enabled == on then
        return
    end
    ns.db.enabled = on
    if on then
        applyMutes()
    else
        setMuted(VOICE_FILES, false)
        if ns.db.charge then
            setMuted(CHARGE_FILES, false)
        end
    end
    ns.log("enabled", on)
end

--- Turns the mute of the shared Charge spell sounds on or off.
-- @param on boolean The new state.
local function setCharge(on)
    if ns.db.charge == on then
        return
    end
    ns.db.charge = on
    if ns.db.enabled then
        setMuted(CHARGE_FILES, on)
    end
    ns.log("charge", on)
end

--- Converts the text of the swap command to a saved value.
-- @param text string A SoundKit ID, a SOUNDKIT name, or a file path.
-- @return number|string The SoundKit ID, or the file path.
local function parseSwap(text)
    local id = tonumber(text)
    if id then
        return id
    end
    local kit = SOUNDKIT and SOUNDKIT[text:upper()]
    if type(kit) == "number" then
        return kit
    end
    return text
end

--- Plays the replacement sound.
-- @return boolean True if the game accepted the sound.
local function playSwap()
    local swap = ns.db.swap
    if type(swap) == "number" then
        return PlaySound(swap) == true
    elseif type(swap) == "string" and swap ~= "" then
        return PlaySoundFile(swap, "SFX") == true
    end
    return false
end

local frame = CreateFrame("Frame")
local handlers = {}

--- Loads the saved table and mutes the boar. SavedVariables do not exist until this event fires.
-- @param loadedName string The name of the addon that loaded.
function handlers.ADDON_LOADED(loadedName)
    if loadedName ~= addonName then
        return
    end
    frame:UnregisterEvent("ADDON_LOADED")
    BoarBeQuietDB = BoarBeQuietDB or {}
    ns.db = BoarBeQuietDB
    ns.db.log = ns.db.log or {}
    applyDefaults(ns.db, DEFAULTS)
    applyMutes()
    ns.log("loaded", C_AddOns.GetAddOnMetadata(addonName, "Version"),
        "enabled", ns.db.enabled, "charge", ns.db.charge, "swap", ns.db.swap)
end

--- Logs the client version, build and interface version, which helps to read a test log.
function handlers.PLAYER_LOGIN()
    local version, build, _, interface = GetBuildInfo()
    ns.log("login", version, build, interface)
end

--- Plays the replacement sound when the player's own pet uses a rank of Charge.
-- Cast data of the player and of the player's pet is not secret
-- (SecretWhenUnitSpellCastRestricted in SecretPredicatesDocumentation.lua).
-- A spell that Blizzard flags as always secret still can be, so the guard stays.
-- @param _ string The unit. The registration makes it "pet".
-- @param _ string The cast GUID. This function does not use it.
-- @param spellID number The spell that the pet cast.
function handlers.UNIT_SPELLCAST_SUCCEEDED(_, _, spellID)
    if not ns.db then
        return
    end
    if issecretvalue(spellID) then
        ns.log("pet cast", spellID)
        return
    end
    -- Only Charge goes in the log. The pet casts Growl every few seconds, and
    -- those lines push the load and login lines out of the 200-line log.
    if PET_CHARGE[spellID] ~= true then
        return
    end
    ns.log("pet cast", spellID, "Charge")
    if not (ns.db.enabled and ns.db.swap) then
        return
    end
    local ok, result = pcall(playSwap)
    if ok then
        ns.log("swap played", result)
        return
    end
    -- A failed swap would fail on each Charge, so turn it off and say so once.
    ns.log("swap failed", result)
    print(addonName .. ": the swap sound failed (" .. tostring(result) .. "). Swap is now off.")
    ns.db.swap = false
end

--- Sends each event to its handler.
-- @param _ table The frame. This function does not use it.
-- @param event string The event name.
-- @param ... any The event payload.
local function onEvent(_, event, ...)
    local handler = handlers[event]
    if handler then
        handler(...)
    end
end

frame:SetScript("OnEvent", onEvent)
frame:RegisterEvent("ADDON_LOADED")
frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", "pet")

--- Prints the state and the commands.
local function printStatus()
    local db = ns.db
    print(addonName .. ": " .. (db.enabled and "on. Boar and pig voices are muted." or "off. Boar and pig voices play."))
    print("  Charge spell sounds: " .. (db.charge and "muted" or "not muted")
        .. ". Swap sound for the pet's Charge: " .. (db.swap and tostring(db.swap) or "off") .. ".")
    print("  Commands: /bbq on, /bbq off, /bbq charge on, /bbq charge off,"
        .. " /bbq swap <SoundKit ID, SOUNDKIT name or file path>, /bbq swap off, /bbq debug")
end

--- Sets the replacement sound, and plays it once as a preview.
-- @param text string The text after "swap".
local function commandSwap(text)
    if text == "" then
        print(addonName .. ": give a SoundKit ID, a SOUNDKIT name or a file path. /bbq swap off turns it off.")
        return
    end
    if text:lower() == "off" then
        ns.db.swap = false
        print(addonName .. ": swap off.")
        return
    end
    local previous = ns.db.swap
    ns.db.swap = parseSwap(text)
    local ok, played = pcall(playSwap)
    if ok and played then
        print(addonName .. ": swap set to " .. tostring(ns.db.swap) .. ". It plays when the pet uses Charge.")
        return
    end
    ns.db.swap = previous
    ns.log("swap preview failed", text, ok and "not played" or played)
    print(addonName .. ": the game did not play " .. text
        .. (ok and "" or (" (" .. tostring(played) .. ")")) .. ". Swap is unchanged.")
end

SLASH_BOARBEQUIET1 = "/bbq"
SLASH_BOARBEQUIET2 = "/boarbequiet"

--- Handles the slash command.
-- @param message string The text after the command.
SlashCmdList.BOARBEQUIET = function(message)
    local command, rest = strtrim(message or ""):match("^(%S*)%s*(.-)$")
    command = command:lower()
    if command == "on" then
        setEnabled(true)
        printStatus()
    elseif command == "off" then
        setEnabled(false)
        printStatus()
    elseif command == "charge" and (rest:lower() == "on" or rest:lower() == "off") then
        setCharge(rest:lower() == "on")
        printStatus()
    elseif command == "swap" then
        commandSwap(rest)
    elseif command == "debug" then
        ns.db.debug = not ns.db.debug
        print(addonName .. ": debug " .. (ns.db.debug and "on" or "off"))
    else
        printStatus()
    end
end
