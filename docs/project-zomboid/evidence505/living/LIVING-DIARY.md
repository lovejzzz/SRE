# Hearth Studio — three days lived as the resident

Request (2026-10-16): live in the house like a real person for three days, notice what daily
life needs, and add it. Lived in Claude's built-in browser (http://127.0.0.1:8883, own test
profile, not the user's browser save) through the same buttons and keys a player uses
(`test-results/live-driver.js`, no state edits). Game time Day 18 15:01 → Day 21 15:44.

## Days

- **Day 18 (afternoon, wounded).** Came back inside after the zombie attack (HP 28, seven
  scratches). Drank, swapped dirty dressings for clean bandages, rested, cooked a chicken leg
  in the oven (one burnt), watched TV, used the toilet, slept. The zombie corpse stays in the
  entry; nothing can move it.
- **Day 19.** Toilet, breakfast (fruit), desk (the computer can't be used), trainer (no exercise
  action), piano (no progress or mood effect), cold beans for lunch, rest, chicken and cheese
  for dinner, toilet, bed. HP rose slowly.
- **Day 20.** Wounds healed, so I took off seven bandages and now carried 13 dirty ones. Showered
  with water only: wetness 99.9 and nothing to dry with. Fruit for breakfast. Drinking at the
  kitchen sink only worked from one side. Cold beans from the can for lunch, then a long walk
  round the bar to the bin. Cheese and an apple for dinner, which left the fridge with
  oranges and water. The toilet needed nine position attempts.
- **Day 21.** Last orange and an apple for breakfast, cold beans for lunch (the third tin meal).
  Three days complete at 15:44, HP 91.

## What daily life was missing (35 notes, grouped)

| Need | Observed | Now |
| --- | --- | --- |
| Toothbrush / toothpaste | Not in the house; no brush action | **Added**: stocked in the mirror cabinet; **Brush teeth** at a basin (≈3.5 game min, 0.3 L) and a "Teeth brushed N h ago" line in health |
| Toilet paper | None anywhere | **Added**: 3 rolls; each visit uses one; without a roll, hands end up dirtier (−15) |
| Soap at basin / kitchen sink | Water-only rinse | **Added**: soap in the bathroom cabinet and on the counter; **Wash hands with soap** takes hands to 100 % (water alone stops at 80 %) and uses one use of soap |
| Towel after showering | Wet at 99.9 with no towel | **Stocked**: two bath towels; the existing soap shower and towel drying now have the items they need (verified 100 → 0 wetness) |
| Hygiene | Stayed at 100 for a whole day | **Fixed**: wears off 1.5 %/game hour (not while showering) |
| Dirty bandages | 13 carried, no way to clean them | **Added**: **Wash N × dirty bandage** at any sink turns them back into clean bandages (water-limited off mains) |
| Burnt / spoiled food | Bin refused it | **Fixed**: burnt or rotten food is rubbish (fresh food is never offered); toothbrush, toothpaste and toilet paper are never treated as junk |
| Toilet approach | Pan faced the basin across a 40 cm gap; ~17 cm usable band | **Re-laid**: toilet on the back wall beside the basin, shifted to leave a ~67 cm walkway to the shower; worked on the first attempt |
| Pantry | 3 days of tins and fruit, no staples | **Stocked**: bread, peanut butter, jam, cereal, crackers, 4 soups, 6 potatoes, milk ×2 (arrives full), butter, carrots |
| Plates, bowls, mugs | None | **Stocked** in the breakfast-bar storage (2 each) |
| Clothes | Three T-shirts only | **Stocked**: 2 trousers, 4 underpants, 4 pairs of socks in the bed drawers |
| Something to read | No books or radio | **Stocked**: 2 books, 2 crossword magazines on the media console |

## Found and fixed along the way

- **Re-applying the home restocked it.** The Workshop's "Use as my home" applied without the
  resident flag, so stock was reset to the authored plan every time. The fridge went back to
  7 apples and 2 chicken legs, and the bathroom cabinet refilled while I was carrying its
  contents. Now any re-apply of the same scene keeps the resident's stock
  (`preservesResidentStock`). The live test save was restocked by my rebuilds before the fix.
  I left that as it is rather than editing the save.
- **East/west PZ fixtures face the wrong way in 3D.** The `W` toilet tile (Facing W, attached
  to the east wall) renders facing the east wall (`toilet-w-tile-faces-wall.jpg`). Every
  recipe key matches its tile Facing, but the 3D transform rotates E/W the opposite way for
  PZ tiles. This affects all E/W toilets, sinks, counters and fridges, so it is left as a
  separate fix. The bathroom uses only N/S orientations.

## Still missing (not done here)

Corpse disposal; a "take several" control; cooking in the pot (rice, soup, kettle for tea or
coffee); a usable desk computer; trainer exercise; piano progress; laundry and wearing clothes;
groceries arriving over time; a bin closer to the cooking side.

Evidence: `bathroom-after.jpg`, `toilet-front-after.jpg`, `toilet-w-tile-faces-wall.jpg`,
earlier `after-lunch-paused-1311.jpg`, `beans-opened-inventory.jpg`.
