from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.logger import Logger
from app_state import app_state
from core.generate import generate_password


class AddPasswordScreen(Screen):
    site_field = ObjectProperty(None)
    pwd_field = ObjectProperty(None)
    length_field = ObjectProperty(None)  # optional TextInput fallback
    length_slider = ObjectProperty(None)  # preferred Slider control
    info_text = StringProperty("")

    def on_pre_enter(self, *args):
        self.info_text = ""
        if self.site_field:
            self.site_field.text = ""
        if self.pwd_field:
            self.pwd_field.text = ""
        if self.length_field:
            self.length_field.text = "12"

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

    def do_save(self):
        if not app_state.vault:
            self.info_text = "Vault not loaded"
            return
        site = (self.site_field.text or "") if self.site_field else ""
        pwd = (self.pwd_field.text or "") if self.pwd_field else ""
        if not site or not pwd:
            self.info_text = "Site & password required"
            return
        try:
            app_state.vault.add(site, pwd)
            self.info_text = f"Saved {site}"
            try:
                from kivy.app import App

                App.get_running_app().show_status(f"Saved {site}")
            except Exception:
                pass
        except Exception as e:
            Logger.exception("Add password failed")
            self.info_text = f"Error: {e}"

    def goto_home(self):
        if "HOME" in self.manager.screen_names:
            self.manager.current = "HOME"
