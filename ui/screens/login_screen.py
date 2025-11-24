import code
import email
import profile
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from core.vault import Vault
from core import masterPassword as mp
from app_state import app_state
import os
import json
import re
import random
import smtplib
from email.message import EmailMessage
import threading
from dotenv import load_dotenv
from ui.screens.profile_screen import load_profile

load_dotenv()

def generate_reset_code(length=6):
    """Return a random numeric code as a string."""
    code = "".join(str(random.randint(0, 9)) for _ in range(length))
    app_state.reset_code = code  # store it temporarily in app_state
    return code


def send_reset_email(to_email, code):
    msg = EmailMessage()
    msg["Subject"] = "Your Password Reset Code"
    msg["From"] = "pswrdsafe@outlook.com"
    msg["To"] = to_email
    msg.set_content(f"Your password reset code is: {code}")

    api_key = os.getenv("SMTP_APIKEY")

    with smtplib.SMTP("smtp.sendgrid.net", 587) as smtp:
        smtp.starttls()
        smtp.login(
            "apikey",
            api_key,
        )
        smtp.send_message(msg)
        print("Email sent successfully!")


class LoginScreen(Screen):
    error_text = StringProperty("")  # Bound to error label
    pwd_field = ObjectProperty(None)  # Bound to password TextInput

    def on_pre_enter(self, *args):
        # Reset UI state
        self.error_text = ""
        if self.pwd_field:
            self.pwd_field.text = ""
        Logger.info("LoginScreen: ready")

    def do_login(self):
        pwd = (self.pwd_field.text or "").strip() if self.pwd_field else ""
        if not pwd:
            self.error_text = "Enter master password"
            return
        try:
            # If master hash doesn't exist, create it with provided password
            if not mp.os.path.exists(mp.masterHashFile):
                mp.createMasterPassword(pwd)
            else:
                if not mp.verifyMasterPassword(pwd):
                    self.error_text = "Incorrect password"
                    return

            # Initialize vault with current password
            app_state.vault = Vault(pwd)
            app_state.master_password = pwd
            Logger.info("Login: authenticated; vault initialized")
            #Load profile
            if not getattr(app_state, "profile", None):
                app_state.profile = load_profile()
            if self.manager and "HOME" in self.manager.screen_names:
                try:
                    home = self.manager.get_screen("HOME")
                    home.refresh_entries()
                except Exception:
                    Logger.exception("Failed to refresh Home screen after login")

            #If a home screen exists, navigate there; otherwise stay
            if "HOME" in self.manager.screen_names:
                self.manager.current = "HOME"
        except Exception as e:
            Logger.exception("Login error")
            self.error_text = f"Error: {e}"

    def on_submit(self):
        self.do_login()

    def _send_recovery_thread(self, email, smtp_config, popup):
        try:
            if smtp_config is None:
                import secrets

                token = secrets.token_urlsafe(32)
                mp.storeTokenHash(token, ttl_seconds=3600)
                Clock.schedule_once(
                    lambda dt: self._on_send_result(True, f"DEV TOKEN: {token}", popup),
                    0,
                )
                return

            ok, msg = mp.generate_and_send_recovery(
                smtp_config, email, ttl_seconds=3600
            )
            Clock.schedule_once(lambda dt: self._on_send_result(ok, msg, popup), 0)
        except Exception as e:
            Logger.exception("forgot_password: unexpected error")
            Clock.schedule_once(
                lambda dt: self._on_send_result(False, f"Internal error: {e}", popup), 0
            )

    def _on_send_result(self, ok: bool, msg: str, popup: Popup):
        popup.dismiss()
        self._forgot_sending = False
        if ok:
            if msg.startswith("DEV TOKEN:"):
                token = msg.split("DEV TOKEN: ", 1)[-1]
                self._show_popup(
                    "Dev token (testing only)", f"Use this token to reset: {token}"
                )
            else:
                self._show_popup(
                    "Recovery email sent",
                    f"A recovery email was sent to {msg if isinstance(msg, str) else 'your email'}.",
                )
        else:
            self._show_popup("Send failed", f"Failed to send recovery email: {msg}")

    def _show_popup(self, title: str, message: str):
        content = BoxLayout(orientation="vertical", padding=12, spacing=12)
        content.add_widget(Label(text=message))
        btn = Button(text="OK", size_hint_y=None, height="40dp")
        content.add_widget(btn)
        popup = Popup(
            title=title, content=content, size_hint=(None, None), size=(420, 220)
        )
        btn.bind(on_release=popup.dismiss)
        popup.open()

    def _load_profile_file(self) -> dict:
        """Try to load profile JSON from app user_data_dir then fallback to local file."""
        try:
            user_dir = App.get_running_app().user_data_dir
        except Exception:
            user_dir = None

        candidates = []
        if user_dir:
            candidates.append(os.path.join(user_dir, "user_profile.json"))
        candidates.append("user_profile.json")

        for p in candidates:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f) or {}
                except Exception:
                    Logger.exception(f"Failed to read profile file: {p}")
        return {}
    def _get_recovery_email(self) -> str:
        try:
            mp_obj = mp.loadRecovery()
            if mp_obj and "email" in mp_obj:
                return mp_obj["email"] or ""
        except Exception:
            Logger.exception("Failed to load recovery email from master password")
    
    #fallback to profile JSON
        profile = getattr(app_state, "profile", None) or self._load_profile_file()
        if isinstance(profile, dict):
            return profile.get("email", "") or ""
        return ""

    def forgot_password(self):
        Logger.info("LoginScreen: forgot_password called")

        profile = getattr(app_state, "profile", None) or self._load_profile_file()
        if not profile:
            profile = self._load_profile_file()
        email = self._get_recovery_email()
        if not email:
            self._show_popup(
                "No recovery email",
                "No recovery email configured. Go to Profile and set one.",
            )
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self._show_popup(
                "Invalid email",
                "The configured recovery email looks invalid. Please update it in Profile.",
            )
            return

        code = generate_reset_code()
        app_state.reset_code = code
        Logger.info("LoginScreen: generated reset code (stored in app_state)")

        def _thread_send():
            err = None
            try:
                send_reset_email(email, code)
                Logger.info("LoginScreen: reset email sent in background")
            except Exception as e:
                Logger.exception("Failed to send email in background")
                err = e
            # user notification on the main thread
            Clock.schedule_once(lambda dt: self._notify_send_result(err, email), 0)

        t = threading.Thread(target=_thread_send, daemon=True)
        t.start()

    def _notify_send_result(self, err, email):
        if err is None:
            self._show_popup(
                "Recovery email sent", f"A recovery email was sent to {email}."
            )
            if self.manager and "VERIFY_CODE" in self.manager.screen_names:
                Clock.schedule_once(
                    lambda dt: setattr(self.manager, "current", "VERIFY_CODE"), 0
                )

        else:
            self._show_popup("Send failed", f"Failed to send recovery email: {err}")
