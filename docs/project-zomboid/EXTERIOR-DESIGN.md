# Exterior design (`scene.exterior`)

A house's garden, planting and envelope details are part of the house: they are
saved in the scene document, exported and imported with it, editable in the Workshop
(**View → Exterior & garden**) and scriptable with build commands. Someone who
replicates a house (export/import, or a scripted build) gets the same exterior.

## Automatic vs designed

- **No `scene.exterior`**: automatic. Everything is generated deterministically from
  the plan (lawn and paving tiles, walls, roofs, doors), so two copies of the same
  house look the same. All houses saved before this section existed behave this way.
- **With `scene.exterior`**: a sparse override of the defaults below. Unset fields keep
  their defaults. **Reset to automatic** removes the section.

| Setting | Default | Meaning |
|---|---|---|
| `surroundings.enabled` | true | lane, drive, gate, neighbours' cottages |
| `meadow.enabled` | true | rough grass and wildflowers beyond the hedge |
| `treeLine.enabled` | true | distant woodland ring |
| `hills.enabled` | true | horizon hills |
| `hedge.enabled`, `hedge.height` | true, 1.05 m | clipped boundary hedge (0.4–2.5 m) |
| `borders.enabled`, `borders.planting` | true, `mixed` | planted beds: `mixed`, `lavender`, `box`, `meadow` |
| `lawn.blades` | true | 3D grass blades over the lawn |
| `gardenTrees.mode`, `.trees` | `auto` | `auto` (up to four, far from the house), `listed` (exact `{id,x,y,height?,seed?}` in grid cells), `none` |
| `climbers.mode`, `.walls` | `auto` | `auto` (every blank exterior run ≥ 4 m gets a trellis and ivy), `listed` (these wall ids), `none` |
| `scannedPlants.enabled` | true | scanned CC0 shrubs, ferns, weeds, dandelions, hose reel |
| `props.enabled` | true | door canopy, step, mat, bicycle, washing line… |
| `life.enabled` | true | birds, falling leaves |
| `envelope.parapet` / `plinth` / `sills` / `downpipes` / `waterButt` | true | building envelope details |
| `weathering` | 1 | facade streaks, splash-back and kerb grime strength, 0–1 |

## Build commands

```json
{"type":"exterior.set","exterior":{"hedge":{"height":1.6},"borders":{"planting":"lavender"},"weathering":0.4}}
{"type":"exterior.tree.add","tree":{"id":"oak","x":2,"y":15,"height":9,"seed":7}}
{"type":"exterior.tree.remove","id":"oak"}
{"type":"exterior.climber.set","wallId":"wall:level:0:N:7995:11407","on":true}
{"type":"exterior.reset"}
```

- Adding a tree switches trees to `listed`, starting from that tree alone. The
  automatic choice is not frozen into the save.
- Setting a climber does the same for climbers.

Invalid values are rejected before they reach a save: unknown sections or fields, wrong
types, out-of-range numbers, unknown plantings or modes, malformed or duplicate trees,
and unknown walls.

Code: `src/scene-exterior.js` (schema, validation, commands), `src/workshop-exterior-panel.js`
(UI), `src/exterior-landscape.js` and `src/exterior-architecture.js` (rendering).
