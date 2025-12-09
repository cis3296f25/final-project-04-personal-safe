# ui/screens/reset_password_screen.py
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup

from core import masterPassword as mp
from core.vault import Vault
from app_state import app_state

class ResetPasswordScreen(Screen):
    #def reset_password(self, new_password, confirm_password):

    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=20, spacing=14)

        layout.add_widget(Label(text="Enter Current Master Password"))
        self.old_pw = TextInput(password=True, multiline=False)
        layout.add_widget(self.old_pw)

        layout.add_widget(Label(text="Enter New Password"))
        self.new_pw = TextInput(password=True, multiline=False)
        layout.add_widget(self.new_pw)

        layout.add_widget(Label(text="Confirm New Password"))
        self.confirm_pw = TextInput(password=True, multiline=False)
        layout.add_widget(self.confirm_pw)

        btn = Button(text="Reset Password", size_hint_y=None, height="48dp")
        btn.bind(on_release=self._reset_password)
        layout.add_widget(btn)

        self.add_widget(layout)

    def _reset_password(self, *_):
        old_pw = self.old_pw.text.strip()
        new_pw = self.new_pw.text.strip()
        confirm_pw = self.confirm_pw.text.strip()

        if not old_pw:
            self._show_popup("Error", "Current password is required.")
            return

        if not new_pw:
            self._show_popup("Error", "New password cannot be empty.")
            return

        if new_pw != confirm_pw:
            self._show_popup("Error", "Passwords do not match.")
            return

        if new_pw == old_pw:
            self._show_popup("Error", "New password must differ from the old password.")
            return

        try:
            vault = Vault(old_pw)
            vault.change_master_password(new_pw)

            app_state.master_password = new_pw
            app_state.vault = Vault(new_pw)

            self._show_popup("Success", "Master password has been reset.")
            self.manager.current = "HOME"

        except Exception as e:
            self._show_popup("Error", str(e))


    def _show_popup(self, title, message):
        content = BoxLayout(orientation="vertical", padding=12, spacing=12)
        content.add_widget(Label(text=message))
        btn = Button(text="OK", size_hint_y=None, height="40dp")
        content.add_widget(btn)
        popup = Popup(title=title, content=content, size_hint=(None, None), size=(420, 220))
        btn.bind(on_release=popup.dismiss)
        popup.open()
