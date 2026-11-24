# Encyclopedia plan (proposal, waiting for Jordan's OK)

Today (Kanto): one long walkthrough page in parts. Place names link to their part; Pokémon and items link to an index at
the end that lists everywhere they turn up. All of it is built from the game's own data by `facts.py` + `build.py`.

## Proposed: one linked site for every region

One artifact holding many small pages (it can hold hundreds), all generated from the data, so it never goes stale:

| Page | What's on it | Links out to |
|---|---|---|
| **Home** | the regions, search box, the lists below | everything |
| **Walkthrough** (one per region, in parts) | the story in order, as now | place pages, Pokémon, items, trainers |
| **Place** (one per town / route / cave) | intro, map picture if wanted, wild Pokémon, items, trainers, people, shops, where the exits lead | neighbouring places, the walkthrough part, Pokémon, items, trainers |
| **Pokémon** (one per species) | icon, types, evolutions, everywhere it's found in every region (how, levels, rate), which trainers use it | places, evolutions, trainers |
| **Item** (one per item) | what it does (the game's own text), where it's found, given, sold, won | places, trainers |
| **Trainer** (Gym Leaders, Elite Four, rivals, bosses) | every battle with them: place, team, levels, rewards | places, Pokémon |
| **Lists** | all Pokémon by number, all items by kind, all Gym Leaders by region | the pages above |

How the pages link: everything a table names is a link (a Pokémon to its page, an item to its page, a place to its
page). Place pages link to their neighbours through their exits, so you can walk the region page by page. Walkthrough
parts stay the story order; place pages are the reference.

Each region's walkthrough is written from its own source game's walkthrough (HGSS for Johto, ORAS for Hoenn, and so on);
the reference pages need no writing at all, they come straight from the data.
