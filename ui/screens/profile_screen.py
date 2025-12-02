import json
import os
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.logger import Logger
from kivy.app import App
from app_state import app_state
from core import masterPassword as mp
from core import twofactor as tf
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image as UImage
from kivy.core.image import Image as CoreImage
from kivy.lang import Builder
from kivy.factory import Factory
import base64
import io
from kivy.metrics import dp

Builder.load_file("ui/kv/components.kv")

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
    twofa_status = StringProperty("")

    def on_pre_enter(self, *args):
        profile = load_profile()

        if getattr(app_state, "profile", None):
            profile = {**profile, **getattr(app_state, "profile", {})}

        self.email = profile.get("email", "")
        self.display_name = profile.get("display_name", "")
        # Load 2FA status for UI
        self.twofa_status = "Enabled" if profile.get("2fa_enabled") else "Disabled"

    def save_profile(self):
        profile = load_profile()
        if not isinstance(profile, dict):
            profile = {}
        profile.update({"email": self.email, "display_name": self.display_name})

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

    def enable_2fa(self):
        profile = load_profile()
        account = self.email or self.display_name or "user"
        issuer = "PersonalSafe"
        secret = tf.generate_secret()
        uri = tf.provisioning_uri(secret, account_name=account, issuer=issuer)
        data_uri = tf.make_qr_data_uri(uri)

        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        if data_uri:
            try:
                b64 = data_uri.split(",", 1)[1]
                png = base64.b64decode(b64)
                buf = io.BytesIO(png)
                ci = CoreImage(buf, ext="png")
                img_widget = UImage(
                    texture=ci.texture,
                    size_hint=(1, None),
                    height=dp(180),
                    allow_stretch=True,
                    keep_ratio=True,
                )
                content.add_widget(img_widget)
            except Exception:
                pass

        content.add_widget(
            Label(
                text=f"Secret: {secret}",
                size_hint_y=None,
                height=dp(28),
                color=(0, 0, 0, 1),
            )
        )

        # instructions
        instruction = Label(
            text="Open your authenticator app and scan the QR or enter the secret.",
            size_hint_y=None,
            height=dp(28),
            color=(0, 0, 0, 1),
        )
        content.add_widget(instruction)

        # code input
        from kivy.uix.textinput import TextInput

        code_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            hint_text="6-digit code",
            halign="center",
        )
        content.add_widget(code_input)

        btn_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        confirm = Button(text="Confirm")
        cancel = Button(text="Cancel")
        btn_box.add_widget(cancel)
        btn_box.add_widget(confirm)
        content.add_widget(btn_box)

        popup = Factory.CustomPopup(
            title="Enable 2FA", size_hint=(None, None), size=(520, 420)
        )
        # set the popups content to the custom content
        popup.content = content

        def _on_cancel(*_):
            popup.dismiss()

        def _on_confirm(*_):
            code = code_input.text.strip()
            ok = tf.verify_code(secret, code, window=1)
            if ok:
                profile = load_profile()
                profile["2fa_enabled"] = True
                profile["2fa_secret"] = secret
                try:
                    app_state.profile = profile
                except Exception:
                    pass
                save_profile_to_disk(profile)
                self.twofa_status = "Enabled"
                popup.dismiss()
            else:
                instruction.text = "Code invalid — try again"

        cancel.bind(on_release=_on_cancel)
        confirm.bind(on_release=_on_confirm)
        popup.open()

    def disable_2fa(self):
        profile = load_profile()
        if not profile.get("2fa_enabled"):
            return

        content = BoxLayout(orientation="vertical", padding=8, spacing=8)
        content.add_widget(Label(text="Enter current 2FA code to disable"))
        from kivy.uix.textinput import TextInput

        code_input = TextInput(multiline=False, size_hint_y=None, height=dp(40))
        content.add_widget(code_input)
        btn_box = BoxLayout(size_hint_y=None, height=dp(44), spacing=8)
        confirm = Button(text="Confirm")
        cancel = Button(text="Cancel")
        btn_box.add_widget(cancel)
        btn_box.add_widget(confirm)
        content.add_widget(btn_box)
        popup = Popup(
            title="Disable 2FA",
            content=content,
            size_hint=(None, None),
            size=(420, 220),
        )

        def _on_cancel(*_):
            popup.dismiss()

        def _on_confirm(*_):
            code = code_input.text.strip()
            secret = profile.get("2fa_secret")
            if secret and tf.verify_code(secret, code):
                profile["2fa_enabled"] = False
                profile.pop("2fa_secret", None)
                try:
                    app_state.profile = profile
                except Exception:
                    pass
                save_profile_to_disk(profile)
                self.twofa_status = "Disabled"
                popup.dismiss()
            else:
                content.children[1].text = "Invalid code"

        cancel.bind(on_release=_on_cancel)
        confirm.bind(on_release=_on_confirm)
        popup.open()
