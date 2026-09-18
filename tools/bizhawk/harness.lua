-- Playtest harness: drive the build from Lua, screenshot it, and write a log
-- the caller can read back.
--
-- Loaded by tools/playtest.py, which passes the walk to run in
-- work/playtest/walk.txt and collects work/playtest/*.png afterwards.
--
-- Design notes, because both are things that bite:
--
--  * Waits are on STATE, not frame counts.  A fixed "advance 600 frames" walk
--    breaks the first time a scene gains or loses a frame, and every scene here
--    will as the script changes length.  wait_for() polls a predicate and gives
--    up loudly.
--  * Nothing asserts.  The harness reports; the caller decides.  A walk that
--    halts on the first surprise tells you about one problem per run, and the
--    point of automating this is to come back with all of them.

local RAM = dofile(OUT_DIR .. "/ram.lua")

local log_lines = {}
local shots = 0
local domain = nil

local function log(fmt, ...)
  local line = string.format(fmt, ...)
  log_lines[#log_lines + 1] = line
  console.log(line)
end

-- The Genesis cores do not agree on what to call work RAM, so ask.
local function pick_domain()
  local names = memory.getmemorydomainlist()
  local want = { ["68K RAM"] = true, ["Main RAM"] = true, ["RAM"] = true }
  local seen = {}
  for i = 0, #names do
    local n = names[i]
    if n then
      seen[#seen + 1] = n
      if want[n] and not domain then domain = n end
    end
  end
  log("memory domains: %s", table.concat(seen, ", "))
  if not domain then
    domain = names[0]
    log("WARNING: no work-RAM domain recognised, falling back to %s", tostring(domain))
  end
  memory.usememorydomain(domain)
  log("reading state from domain %s", domain)
end

local function peek(sym)
  local s = RAM[sym]
  if not s then return nil end
  if s.size == 1 then return memory.read_u8(s.off) end
  if s.size == 2 then return memory.read_u16_be(s.off) end
  return memory.read_u32_be(s.off)
end

local function state()
  return string.format(
    "frame=%d mode=%s window=%s windows=%s panels=%s money=%s",
    emu.framecount(),
    tostring(peek("Game_Mode_Routine")), tostring(peek("Window_Index")),
    tostring(peek("Windows_Opened_Num")), tostring(peek("Panel_Num")),
    tostring(peek("Current_Money")))
end

local function frames(n)
  for _ = 1, n do emu.frameadvance() end
end

-- Hold a button for `hold` frames, then release for `gap`.  The release
-- matters: the engine reads Joypad_Pressed as an edge, so a button held
-- across a menu transition is read twice.
local function tap(button, hold, gap)
  hold = hold or 4
  gap = gap or 12
  for _ = 1, hold do
    joypad.set({ [button] = true }, 1)
    emu.frameadvance()
  end
  frames(gap)
end

local function wait_for(label, pred, limit)
  limit = limit or 900
  for i = 1, limit do
    if pred() then
      log("  reached %s after %d frames  (%s)", label, i, state())
      return true
    end
    emu.frameadvance()
  end
  log("  TIMEOUT waiting for %s after %d frames  (%s)", label, limit, state())
  return false
end

local function shot(label)
  shots = shots + 1
  local name = string.format("%02d_%s.png", shots, label)
  client.screenshot(OUT_DIR .. "/" .. name)
  log("  shot %s  (%s)", name, state())
end

-- ---------------------------------------------------------------------
-- The walk.  Deliberately shallow for a first run: reaching the field and
-- opening the camp menu exercises the strip renderer, the window fold and the
-- meseta field, which is where every layout bug this month has been.
-- ---------------------------------------------------------------------
local function walk()
  -- Buttons come from the game's own equates, not from guesswork:
  -- ButtonCancel = $10 = B, ButtonSpeak = $20 = C, ButtonCamp = $40 = A.
  -- The first version of this walk advanced dialogue with B and opened the
  -- menu with C, and sat on the START screen for forty taps.
  local CONFIRM, CANCEL, MENU = "C", "B", "A"

  log("== boot ==")
  frames(150)
  shot("boot")

  -- Press Start until the START/CONTINUE window appears.  Timing this by
  -- frame count put the first attempt into the attract demo instead: it ran
  -- all the way to field control with Current_Money still 0, which is the
  -- giveaway that no game had begun.
  log("== title ==")
  local at_menu = false
  for i = 1, 30 do
    tap("Start", 4, 30)
    if peek("Windows_Opened_Num") > 0 then
      log("  start menu up after %d presses  (%s)", i, state())
      at_menu = true
      break
    end
  end
  shot("start_menu")
  if not at_menu then log("  WARNING: no start menu; the walk will drift") end

  log("== new game ==")
  -- Money is 0 until a game is actually initialised, so it is the one signal
  -- that says the demo was not entered by mistake.
  local started = false
  for i = 1, 20 do
    tap(CONFIRM, 4, 45)
    if peek("Current_Money") > 0 then
      log("  new game after %d confirms  (%s)", i, state())
      started = true
      break
    end
  end
  shot("new_game")
  if not started then
    log("  ERROR: Current_Money never became non-zero - no game started")
    return
  end

  log("== opening ==")
  local settled, reached = 0, false
  for i = 1, 300 do
    tap(CONFIRM, 3, 10)
    if peek("Game_Mode_Routine") == 12 and peek("Windows_Opened_Num") == 0 then
      settled = settled + 1
      if settled >= 8 then
        log("  field control after %d taps  (%s)", i, state())
        reached = true
        break
      end
    else
      settled = 0
    end
    if i % 60 == 0 then shot(string.format("opening_%d", i)) end
  end
  if not reached then log("  never settled into field control  (%s)", state()) end
  shot("field")

  log("== camp menu: the Meseta field ==")
  tap(MENU, 4, 60)
  shot("camp")
  frames(30)
  shot("camp_settled")

  -- Walk the top-level entries. Screenshot before opening each so the Meseta
  -- line is captured against several different highlighted rows.
  for i = 1, 5 do
    tap("Down", 3, 24)
    shot(string.format("camp_row_%d", i))
  end
  tap(CONFIRM, 4, 40)
  shot("camp_entered")
  tap(CANCEL, 4, 40)
  shot("camp_back")
end

-- ---------------------------------------------------------------------
pick_domain()
log("harness start: %s", state())
local ok, err = pcall(walk)
if not ok then log("WALK ERROR: %s", tostring(err)) end
log("harness done: %d screenshot(s), %s", shots, state())

local f = io.open(OUT_DIR .. "/log.txt", "w")
f:write(table.concat(log_lines, "\n") .. "\n")
f:close()

client.exit()
