from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from app_state import app_state
from kivy.logger import Logger


class BackupImportScreen(Screen):
    info_text = StringProperty("")
    path_field = ObjectProperty(None)

    def on_pre_enter(self, *args):
        self.info_text = ""
        if self.path_field:
            # default filename
            self.path_field.text = "vault_backup.psafe"

    def do_import(self):
        vault = getattr(app_state, "vault", None)
        if not vault:
            self._show_popup("No vault", "Vault not loaded.")
            return

        filepath = (self.path_field.text or "").strip() if self.path_field else ""
        if not filepath:
            self._show_popup("Path required", "Enter backup filepath.")
            return

        # Ask for master password to decrypt backup
        self._ask_password_and_import(filepath)

    def _ask_password_and_import(self, filepath: str):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Label
        content.add_widget(Label(
            text="Enter master password:",
            size_hint_y=None, height=30
        ))

        # TextInput for password
        pw_input = TextInput(
            password=True, multiline=False,
            hint_text="Master password",
            size_hint_y=None, height=40
        )
        content.add_widget(pw_input)

        # Buttons layout
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        ok = Button(text="Import")
        cancel = Button(text="Cancel")
        btn_layout.add_widget(ok)
        btn_layout.add_widget(cancel)
        content.add_widget(btn_layout)

        popup = Popup(
            title="Import Backup",
            content=content,
            size_hint=(None, None),
            size=(420, 260),
            auto_dismiss=False
        )
        cancel.bind(on_release=popup.dismiss)

        def _do(_: None):
            popup.dismiss()
            try:
                app_state.vault.import_encrypted_backup(
                    filepath, pw_input.text or "", replace_existing=True
                )
                self._show_popup("Import complete", "Backup imported successfully.")
            except Exception as e:
                Logger.exception("Import failed")
                self._show_popup("Import failed", f"Failed to import backup: {e}")

        ok.bind(on_release=_do)
        popup.open()

    def _show_popup(self, title: str, message: str):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)

        content.add_widget(Label(text=message, size_hint_y=None, height=40))

        btn = Button(text="OK", size_hint_y=None, height=50)
        content.add_widget(btn)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(None, None),
            size=(420, 220),
            auto_dismiss=False
        )
        btn.bind(on_release=popup.dismiss)
        popup.open()

    def goto_home(self):
        if "HOME" in self.manager.screen_names:
            self.manager.current = "HOME"