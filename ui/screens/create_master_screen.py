import re
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.logger import Logger
from core import masterPassword as mp
from core.vault import Vault
from app_state import app_state
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


class CreateMasterScreen(Screen):
    pwd1_field = ObjectProperty(None)
    pwd2_field = ObjectProperty(None)
    email_field = ObjectProperty(None)
    error_text = StringProperty("")

    def on_pre_enter(self, *args):
        self.error_text = ""
        if self.pwd1_field:
            self.pwd1_field.text = ""
        if self.pwd2_field:
            self.pwd2_field.text = ""
        if self.email_field:
            self.email_field.text = ""

    def _validate(self, p1: str, p2: str) -> str | None:
        if not p1 or not p2:
            return "Both fields required"
        if p1.strip() != p1:
            return "No leading/trailing spaces"
        if len(p1) < 8:
            return "Use at least 8 characters"
        if p1 != p2:
            return "Passwords do not match"
        return None

    def do_create(self):
        p1 = (self.pwd1_field.text or "") if self.pwd1_field else ""
        p2 = (self.pwd2_field.text or "") if self.pwd2_field else ""
        err = self._validate(p1, p2)
        email = (self.email_field.text or "").strip() if self.email_field else ""
        
        if err:
            self.error_text = err
            return
        
        if email:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                self.error_text = "Please enter a valid email address"
                return

        try:
            Logger.info("CreateMaster: creating master password")
            mp.createMasterPassword(p1)

            try:
                if hasattr(mp, "setRecoveryEmail"):
                    mp.setRecoveryEmail(email)
                else:
                    Logger.warning("CreateMaster: mp.setRecoveryEmail not found; email not persisted")
            except Exception:
                Logger.exception("CreateMaster: mp.setRecoveryEmail failed")
            #update app_state
            try:
                app_state.profile = {**(getattr(app_state, "profile", {}) or {}), "email": email}
            except Exception:
                Logger.exception("CreateMaster: failed to update app_state.profile")

            app_state.vault = Vault(p1)
            app_state.master_password = p1
            Logger.info("CreateMaster: master password created")

        except Exception as e:
            Logger.exception("Create master failed")
            self.error_text = f"Error: {e}"

    def goto_home(self):
        if "HOME" in self.manager.screen_names:
            self.manager.current = "HOME"

    def _show_info(self, title: str, message: str):
        box = BoxLayout(orientation="vertical", padding=10, spacing=10)
        box.add_widget(Label(text=message))
        btn = Button(text="OK", size_hint=(1, 0.25))
        box.add_widget(btn)
        p = Popup(title=title, content=box, size_hint=(0.8, 0.4))
        btn.bind(on_release=lambda *_: p.dismiss())
        p.open()