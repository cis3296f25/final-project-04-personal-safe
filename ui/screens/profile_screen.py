import json
import os
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.logger import Logger
from kivy.app import App
from app_state import app_state
from core import masterPassword as mp

PROFILE_FILE = "user_profile.json"

def load_profile():
    try:
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        Logger.exception("Failed loading profile")
    return {}


def save_profile_to_disk(profile_dict):
    try:
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile_dict, f)
        Logger.info(f"Profile saved to {PROFILE_FILE}")
    except Exception as e:
        Logger.exception("Failed saving profile")


class ProfileScreen(Screen):
    email = StringProperty("")
    display_name = StringProperty("")

    def on_pre_enter(self, *args):
        profile = load_profile()

        if getattr(app_state, "profile", None):
            profile = {**profile, **getattr(app_state, "profile", {})}

        self.email = profile.get("email", "")
        self.display_name = profile.get("display_name", "")

    def save_profile(self):
        profile = {"email": self.email, "display_name": self.display_name}

        try:
            app_state.profile = profile
        except Exception:
            pass
        save_profile_to_disk(profile)
        Logger.info(f"Profile saved: {profile}")
        try:
            mp.setRecoveryEmail(self.email)
            Logger.info(f"Recovery email updated in master password: {self.email}")
        except Exception:
            Logger.exception("Failed to update recovery email in master password")

        if "HOME" in self.manager.screen_names:
            self.manager.current = "HOME"
