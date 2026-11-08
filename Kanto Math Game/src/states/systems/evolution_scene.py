"""The evolution (and Egg hatching) scene."""

import pygame
from src.states.base import GameState
from src.ui.widgets import Button
from src.ui.panels import CommandButton
from src.ui import theme
from src.utils import Utils
from src.config import WHITE, GREEN
from src.pokemon.data import Pokemon


# [REF-0041: Evolution Logic]
class EvolutionState(GameState):
    def __init__(
        self, game, pokemon_to_evolve, evolution_id, team_index, next_form="normal", context="party", return_state=None, consume_catch_count=False,
        choices=None
    ):
        """choices: evolution entries ("SOLGALEO", "LUNALA") when more than one is ready; the player
        picks one on this screen (Jordan: Cosmoem)."""
        super().__init__(game)
        self.consume_catch_count = consume_catch_count
        self.pokemon = pokemon_to_evolve
        self.evolution_id = evolution_id
        self.team_index = team_index
        self.return_state = return_state
        self.context = context
        self.next_form = next_form
        self.phase = "DECISION"
        self.on_line_finish = {}
        self.options_buttons = {}

        self.timer = 0
        self.scale = 1.0
        self.alpha = 255
        self.evolved_pokemon_obj = None
        self.original_name = pokemon_to_evolve.name
        self.is_hatching = (self.original_name == "Mystery Egg") or getattr(pokemon_to_evolve, "is_egg", False)
        if getattr(pokemon_to_evolve, "is_egg", False):  # a Day Care Egg hatching (no YES / NO)
            self.original_name = "Egg"
            self.phase = "START"
            self.timer = 60

        from src.ui.scene_backdrop import SceneBackdrop
        self.backdrop = SceneBackdrop((game.width, game.height), hatching=self.is_hatching)  # (one of a few, at random)
        box = Utils.get_full_dialogue_rect(game)
        btn_w, btn_h = 180, 64  # (the battle's YES / NO)
        self.btn_yes = CommandButton((box.right - 2 * btn_w - 46, box.centery - btn_h // 2, btn_w, btn_h), "YES",
                                     game.assets.fonts["button"], self.evolve_yes, bg_color=theme.POKEMON,
                                     visible=False, autosize=False)
        self.btn_no = CommandButton((box.right - btn_w - 28, box.centery - btn_h // 2, btn_w, btn_h), "NO",
                                    game.assets.fonts["button"], self.evolve_no, bg_color=theme.FIGHT,
                                    visible=False, autosize=False)
        # Branch choice: one button per evolution in place of YES.
        self.choice_buttons = []
        for k, entry in enumerate(choices or []):
            base, form = (entry.rsplit("_", 1) + ["normal"])[:2] if "_" in entry else (entry, "normal")
            pid = game.name_to_id.get(base.upper())
            if not pid:
                continue
            label = base.replace("-", " ").upper() + ("" if form == "normal" else f" ({form.title()})")
            self.choice_buttons.append(Button(
                rect=(box.right - 150 - 230 * (len(choices) - k), box.centery - 30, 220, btn_h), text=label,
                font=game.assets.fonts["tiny"], callback=lambda p=pid, f=form.lower(): self.choose(p, f),
                bg_color=GREEN, visible=False, autosize=False))
        if len(self.choice_buttons) < 2:
            self.choice_buttons = []

    def choose(self, pid, form):
        self.evolution_id, self.next_form = pid, form
        for btn in self.choice_buttons:
            btn.set_visibility(False)
        self.evolve_yes()

    def evolve_yes(self):
        self.phase = "START"
        self.btn_yes.set_visibility(False)
        self.btn_no.set_visibility(False)
        self.timer = 60
        if self.pokemon.cry:
            self.pokemon.cry.play()

    def evolve_no(self):
        self.pokemon.evo_due = False  # asked again at its next level-up
        # Not again this round, or declining would just bring the same question back.
        self.game.evo_declined = getattr(self.game, "evo_declined", set()) | {id(self.pokemon)}
        self._return()

    def start(self):
        self.game.ui_manager.add_element(self.btn_yes)
        self.game.ui_manager.add_element(self.btn_no)
        for btn in self.choice_buttons:
            self.game.ui_manager.add_element(btn)
        if self.phase == "DECISION":
            self.btn_yes.set_visibility(not self.choice_buttons)
            self.btn_no.set_visibility(True)
            for btn in self.choice_buttons:
                btn.set_visibility(True)

    def handle_events(self, events):
        pass

    def update(self):
        self.backdrop.update()
        if self.phase == "DECISION":
            return

        self.timer -= 1

        if self.phase == "START" and self.timer <= 0:
            self.phase = "GROW"
            self.timer = 50

        elif self.phase == "GROW":
            self.scale += 0.05
            self.alpha = max(0, self.alpha - 10)
            if self.timer <= 0:
                self.phase = "FLASH"
                self.timer = 20
                raw_data = self.game.loader.fetch_specific(
                    self.evolution_id, form=self.next_form,
                    is_shiny=self.pokemon.is_shiny
                )
                self.evolved_pokemon_obj = Pokemon(
                    raw_data, self.game.assets, size_mult=1.5
                )
                # What the Pokémon has earned stays with it through evolution.
                for attr in ("level", "xp", "friendship", "affection", "everstone", "counters", "condition", "sheen", "ribbons",
                             "gmax_factor", "caught_region", "ivs", "moves", "move_pool", "status", "ability_slot",
                             "gender", "tera_type", "held_item"):
                    if hasattr(self.pokemon, attr):
                        setattr(self.evolved_pokemon_obj, attr, getattr(self.pokemon, attr))

        elif self.phase == "FLASH":
            if self.timer <= 0:
                self.phase = "REVEAL"
                self.timer = 60
                if self.evolved_pokemon_obj and self.evolved_pokemon_obj.cry:
                    self.evolved_pokemon_obj.cry.play()
                self.scale = 3.0
                self.alpha = 0

        elif self.phase == "REVEAL":
            self.scale = max(1.0, self.scale - 0.1)
            self.alpha = min(255, self.alpha + 15)
            if self.timer <= 0:
                self.phase = "END"
                self.timer = 180  # (long enough to read it, over the fanfare)
                # The congratulations fanfare (Jordan, 11-02: "no song"; it's cued by text box lines,
                # and this screen draws its own).
                music = getattr(self.game, "music", None)
                if music is not None:
                    music.jingle("congrats_evolve")
                if self.evolved_pokemon_obj:
                    if self.context == "pc":
                        self.game.story_manager.pc_pokemon[self.team_index] = self.evolved_pokemon_obj
                    else:
                        self.game.story_manager.player_team[self.team_index] = self.evolved_pokemon_obj

                    # Damage carries over (a fainted Pokemon stays fainted), like the games.
                    old_max = self.pokemon.get_max_hp()
                    new_max = self.evolved_pokemon_obj.get_max_hp()
                    old_hp = self.pokemon.current_hp
                    self.evolved_pokemon_obj.current_hp = (
                        0 if old_hp <= 0 else max(1, min(new_max, old_hp + new_max - old_max)))
                    if getattr(self.pokemon, "is_egg", False):  # hatched: full of energy, and fond of you
                        self.evolved_pokemon_obj.current_hp = new_max
                        self.evolved_pokemon_obj.friendship = 3
                        self.evolved_pokemon_obj.caught_level = 1
                    self.game.data.add_pokemon(self.evolved_pokemon_obj)
                    self._maybe_shedinja()

                    if self.evolved_pokemon_obj.is_shiny:
                        non_shiny_raw = self.game.loader.fetch_specific(
                            self.evolved_pokemon_obj.id,
                            form=self.evolved_pokemon_obj.form,
                            is_shiny=False
                        )
                        non_shiny_pokemon = Pokemon(non_shiny_raw, self.game.assets, size_mult=0.1)
                        self.game.data.add_pokemon(non_shiny_pokemon)

                    if self.consume_catch_count:
                        current_count = self.game.story_manager.catch_counts.get(self.pokemon.id, 0)
                        if current_count >= 5:
                            self.game.story_manager.catch_counts[self.pokemon.id] = current_count - 5

        elif self.phase == "END" and self.timer <= 0:
            self._return()

    def _maybe_shedinja(self):
        """Nincada -> Ninjask also leaves a Shedinja behind (as in the games). It is a new
        Pokemon built from the Nincada (same level, IVs, shininess, home region); it joins the
        party, or goes to the PC when the party is full, and both land in the Pokedex."""
        if self.pokemon.id != 290 or self.evolution_id != 291:
            return
        story = self.game.story_manager
        nincada = self.pokemon
        shiny = bool(getattr(nincada, "is_shiny", False))
        shed = Pokemon(self.game.loader.fetch_specific(292, is_shiny=shiny), self.game.assets, size_mult=2.5)
        shed.is_shiny = shiny
        shed.level = nincada.level
        for attr in ("ivs", "caught_region"):
            if hasattr(nincada, attr):
                setattr(shed, attr, getattr(nincada, attr))
        shed.current_hp = shed.get_max_hp()
        if len(story.player_team) < 6:
            story.player_team.append(shed)
            self.shedinja_where = "party"
        else:
            story.deposit_to_pc(shed)
            self.shedinja_where = "pc"
        self.game.data.add_pokemon(shed)
        self.shedinja_added = True

    def _return(self):
        pygame.event.clear()
        # Several Pokemon can be ready at once (as in the games): evolve the next one first.
        if self.context == "party":
            from src.states.overworld import evolve_ready_party
            back_to = self.return_state or self.game.states.get("play")
            if back_to is not None and evolve_ready_party(self.game, back_to):
                return
        self.game.evo_declined = set()
        if self.return_state:
            if hasattr(self.return_state, "is_resuming"):
                self.return_state.is_resuming = True
            if hasattr(self.return_state, "show_progression_menu"):
                self.return_state.show_progression_menu()
            self.game.change_state(self.return_state)
        else:
            self.game.change_state(self.game.states["play"])

    def draw(self):
        from src.ui.scene_backdrop import text_band
        center_x, center_y = self.game.width // 2, self.game.height // 2
        self.backdrop.draw(self.game.screen, (center_x, center_y))
        if self.phase != "DECISION":
            text_band(self.game.screen, self.game.height * 0.8, 100)

        if self.phase == "DECISION":
            img = self.pokemon.image
            rect = img.get_rect(center=(center_x, center_y))
            self.game.screen.blit(img, rect)

            box_rect = Utils.get_full_dialogue_rect(self.game)
            theme.draw_textbox(self.game.screen, box_rect)
            if self.is_hatching:
                text = f"What? The {self.original_name} is hatching!"
            else:
                text = f"What? {self.original_name} is evolving!"
            from src.ui.dialogue import wrap_text
            f = self.game.assets.fonts["dialog"]
            rows = wrap_text(text, f, box_rect.width * 0.55)
            lh = int(f.get_linesize() * 1.2)
            top = box_rect.centery - lh * len(rows) // 2
            for k, row in enumerate(rows):
                theme.shadow_text(self.game.screen, row, f, box_rect.x + 40, top + k * lh)
            self.game.ui_manager.draw(self.game.screen)
            return

        if self.phase in ["START", "GROW"]:
            img = pygame.transform.rotozoom(self.pokemon.image, 0, self.scale)
            img.set_alpha(self.alpha)
            rect = img.get_rect(center=(center_x, center_y))
            self.game.screen.blit(img, rect)

            msg = "Hatching..." if self.is_hatching else self.game.assets.get_text("evolving", name=self.original_name)
            if isinstance(msg, list):
                msg = " ".join(msg)

            Utils.draw_text_outline(
                self.game.screen,
                msg,
                self.game.assets.fonts["med"],
                WHITE,
                center_x,
                self.game.height * 0.8,
            )

        elif self.phase == "FLASH":
            self.game.screen.fill(WHITE)

        elif self.phase in ["REVEAL", "END"]:
            if self.evolved_pokemon_obj:
                img = pygame.transform.rotozoom(
                    self.evolved_pokemon_obj.image, 0, self.scale
                )
                img.set_alpha(self.alpha)
                rect = img.get_rect(center=(center_x, center_y))
                self.game.screen.blit(img, rect)

                if self.is_hatching:
                    text = f"Congratulations! The Egg hatched into {self.evolved_pokemon_obj.name}!"
                else:
                    text = self.game.assets.get_text(
                        "evolved",
                        old_name=self.original_name,
                        new_name=self.evolved_pokemon_obj.name,
                    )
                if isinstance(text, list):
                    text = " ".join(text)

                Utils.draw_multiline_text(
                    self.game.screen,
                    text,
                    self.game.assets.fonts["s_med"],
                    WHITE,
                    center_x,
                    self.game.height * 0.8,
                    max_width=self.game.width - 40,
                )
