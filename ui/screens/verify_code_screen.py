from kivy.logger import Logger
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from app_state import app_state
from core.vault import Vault
from core import masterPassword as mp
from ui.screens.profile_screen import load_profile

class VerifyCodeScreen(Screen):
    def verify_code(self, code_input):
        """Called when user submits the code"""
        if code_input == getattr(app_state, 'reset_code', None):
            app_state.reset_code = None  # invalidate the code
            self._ask_reset_password()
        else:
            self._show_popup("Invalid Code", "The code you entered is incorrect.")

#THE VAULT DOESN'T OPEN WITHOUT A MASTER PASSWORD BEING INPUT
#BECAUSE THE MASTER PASSWORD IS NEEDED TO DECRYPT THE VAULT
#CHANGE THE CODE HERE ONCE RESET PASSWORD IS IMPLEMENTED
    def _ask_reset_password(self):
        """Popup asking user if they want to reset their password"""
        content = BoxLayout(orientation="vertical", padding=12, spacing=12)
        content.add_widget(Label(text="Code verified! Do you want to reset your master password?"))

        btn_layout = BoxLayout(size_hint_y=None, height="40dp", spacing=12)
        yes_btn = Button(text="Yes")
        no_btn = Button(text="No")
        btn_layout.add_widget(yes_btn)
        btn_layout.add_widget(no_btn)

        content.add_widget(btn_layout)
        popup = Popup(title="Reset Password?", content=content, size_hint=(None, None), size=(400, 200))

        yes_btn.bind(on_release=lambda *_: self._goto_reset_password(popup))
        no_btn.bind(on_release=lambda *_: self._login_vault(popup))

        popup.open()

    def _goto_reset_password(self, popup):
        popup.dismiss()
        self.manager.current = "RESET_PASSWORD"

#DELETE THIS METHOD ONCE RESET PASSWORD IS IMPLEMENTED
    def _login_vault(self, popup):
        popup.dismiss()
        try:
            #loadprofile
            app_state.profile = load_profile() or {}
            Logger.info(f"VerifyCodeScreen: Loaded profile -> {app_state.profile}")
            
            if not getattr(app_state, "vault", None) and getattr(app_state, "master_password", None):
                from core.vault import Vault
                app_state.vault = Vault(app_state.master_password)

            if self.manager and "HOME" in self.manager.screen_names:
                home = self.manager.get_screen("HOME")
                home.refresh_entries()

            self.manager.current = "HOME"
                
        except Exception as e:
            Logger.exception(f"VerifyCodeScreen: Login error: {e}")
            self.error_text = f"Error: {e}"

    def _show_popup(self, title, message):
        content = BoxLayout(orientation="vertical", padding=12, spacing=12)
        content.add_widget(Label(text=message))
        btn = Button(text="OK", size_hint_y=None, height="40dp")
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(None, None), size=(420, 220))
        btn.bind(on_release=popup.dismiss)
        popup.open()