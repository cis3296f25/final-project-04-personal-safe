# ui/screens/clear_vault_screen.py
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.logger import Logger
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from app_state import app_state


class ClearVaultScreen(Screen):
    info_text = StringProperty("")

    def confirm_clear(self):
        """Show confirmation popup before clearing vault"""
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(Label(text="Are you sure? This will delete all vault entries!"))

        buttons = BoxLayout(size_hint_y=None, height=40, spacing=10)
        yes_btn = Button(text="Yes", background_color=(1,0,0,1))
        no_btn = Button(text="No")

        buttons.add_widget(yes_btn)
        buttons.add_widget(no_btn)
        content.add_widget(buttons)

        popup = Popup(
            title="Confirm Clear Vault",
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False,
        )

        yes_btn.bind(on_release=lambda *a: self._do_clear(popup))
        no_btn.bind(on_release=popup.dismiss)
        popup.open()

    def _do_clear(self, popup: Popup):
        """Actually clear the vault"""
        try:
            if app_state.vault:
                app_state.vault.clear()
                self.info_text = "Vault cleared!"
                # Update HomeScreen status if available
                try:
                    home = App.get_running_app().sm.get_screen("HOME")
                    home.status = "Vault cleared!"
                    home.refresh_entries()
                except Exception:
                    pass
        except Exception as e:
            Logger.exception("Failed to clear vault")
            self.info_text = f"Error: {e}"
        finally:
            popup.dismiss()

    def go_home(self):
        if "HOME" in self.manager.screen_names:
            self.manager.current = "HOME"