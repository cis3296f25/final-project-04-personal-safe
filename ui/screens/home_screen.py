from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, StringProperty, ObjectProperty
from kivy.logger import Logger
from app_state import app_state

class HomeScreen(Screen):
    entries = ListProperty([])  # list of (site, password)
    status = StringProperty("Ready")
    entries_grid = ObjectProperty(None)  # bound to ids.entries_grid in KV
    vault_header = StringProperty("Your Vault")
    
    def on_pre_enter(self, *args):
        self.refresh_entries()

    def refresh_entries(self):
        profile_name = ""
        if getattr(app_state, "profile", None):
            profile_name = app_state.profile.get("display_name", "").strip()
        prefix = f"{profile_name}'s " if profile_name else "Your "
        
        if not app_state.vault:
            self.entries = []
            self.status = "Vault not loaded"
            self.vault_header = f"{profile_name}'s Vault" if profile_name else "Your Vault"
            self._render_entries()
            return
        try:
            self.entries = app_state.vault.items()
            if not self.entries:
                self.status = f"{profile_name}'s Vault empty" if profile_name else "Your Vault"
            else:
                self.status = f"{profile_name}'s Vault - {len(self.entries)} entries"
            self.vault_header = f"{profile_name}'s Vault" if profile_name else "Your Vault"
            self._render_entries()

        except Exception as e:
            Logger.exception("Failed refreshing entries")
            self.status = f"Error: {e}"

    def _render_entries(self):
        # Populate the entries_grid with labels for each entry
        grid = self.entries_grid
        if not grid:
            return
        grid.clear_widgets()
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button

        for site, password in self.entries:
            masked = "•" * min(len(password), 16)
            row = BoxLayout(
                orientation="horizontal", spacing=8, size_hint_y=None, height=30
            )
            site_lbl = Label(
                text=f"[b]{site}[/b]",
                markup=True,
                size_hint_x=None,
                width=140,
                color=(0.15, 0.25, 0.55, 1),
                halign="left",
                valign="middle",
                text_size=(140, 30),
            )
            pwd_lbl = Label(
                text=masked,
                size_hint_x=1,
                color=(0.05, 0.05, 0.05, 1),
                halign="left",
                valign="middle",
                shorten=True,
                shorten_from="right",
            )
            # Ensure halign/valign apply by keeping text_size synced to widget size
            pwd_lbl.bind(size=lambda inst, _val: setattr(inst, "text_size", inst.size))
            toggle_btn = Button(
                text="Show",
                size_hint_x=None,
                width=80,
            )

            def on_toggle(
                instance,
                site=site,
                password=password,
                masked_val=masked,
                label_ref=pwd_lbl,
            ):
                if label_ref.text == masked_val:
                    label_ref.text = password
                    instance.text = "Hide"
                else:
                    label_ref.text = masked_val
                    instance.text = "Show"

            toggle_btn.bind(on_release=on_toggle)

            row.add_widget(site_lbl)
            row.add_widget(pwd_lbl)
            row.add_widget(toggle_btn)
            grid.add_widget(row)

    # Navigation helpers (assumes screens added with these names)
    def goto_add(self):
        if "ADD" in self.manager.screen_names:
            self.manager.current = "ADD"

    def goto_edit(self):
        if "EDIT" in self.manager.screen_names:
            self.manager.current = "EDIT"

    def goto_delete(self):
        if "DELETE" in self.manager.screen_names:
            self.manager.current = "DELETE"

    def goto_profile(self):
        Logger.info("HomeScreen: goto_profile called")
        if not self.manager:
            Logger.error("HomeScreen: no manager! Cannot switch screens")
            return
        Logger.info(f"HomeScreen: manager screens = {self.manager.screen_names}")
        if "PROFILE" in self.manager.screen_names:
            self.manager.current = "PROFILE"
        else:
            Logger.error("HomeScreen: PROFILE screen not found")

    def goto_backup_export(self):
        if "BACKUP_EXPORT" in self.manager.screen_names:
            self.manager.current = "BACKUP_EXPORT"
            
    def goto_backup_import(self):
        if "BACKUP_IMPORT" in self.manager.screen_names:
            self.manager.current = "BACKUP_IMPORT"