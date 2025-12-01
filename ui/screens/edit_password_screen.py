from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.logger import Logger
from app_state import app_state
from core.generate import generate_password


class EditPasswordScreen(Screen):
    site_spinner = ObjectProperty(None)
    pwd_field = ObjectProperty(None)
    info_text = StringProperty("")
    length_field = ObjectProperty(None)  # optional TextInput fallback
    length_slider = ObjectProperty(None)  # preferred Slider control
    sites = ListProperty([])

    def on_pre_enter(self, *args):
        self.refresh_sites()
        self.info_text = ""
        if self.pwd_field:
            self.pwd_field.text = ""

    def refresh_sites(self):
        if app_state.vault:
            self.sites = app_state.vault.get_sites()
        else:
            self.sites = []
        if self.site_spinner and self.sites:
            self.site_spinner.values = self.sites
            self.site_spinner.text = self.sites[0]

    def do_generate(self):
        # Prefer slider value; fall back to text length field
        if self.length_slider:
            length = int(getattr(self.length_slider, "value", 12) or 12)
        else:
            try:
                length = int(self.length_field.text) if self.length_field else 12
            except Exception:
                length = 12
        try:
            pwd = generate_password(length)
            if self.pwd_field:
                self.pwd_field.text = pwd
            self.info_text = f"Generated {length} chars"
        except Exception as e:
            self.info_text = f"Gen error: {e}"

    def do_update(self):
        if not (app_state.vault and self.site_spinner):
            self.info_text = "No vault"
            return
        site = self.site_spinner.text
        pwd = (self.pwd_field.text or "") if self.pwd_field else ""
        if not pwd:
            self.info_text = "Password required"
            return
        try:
            app_state.vault.add(site, pwd)
            self.info_text = "Updated"
            try:
                from kivy.app import App

                App.get_running_app().show_status("Password updated")
            except Exception:
                pass
        except Exception as e:
            Logger.exception("Update failed")
            self.info_text = f"Error: {e}"

    def go_home(self):
        if "HOME" in self.manager.screen_names:
            self.manager.current = "HOME"
