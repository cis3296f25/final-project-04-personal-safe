from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from app_state import app_state
from kivy.logger import Logger


class BackupExportScreen(Screen):
    info_text = StringProperty("")
    path_field = ObjectProperty(None)

    def on_pre_enter(self, *args):
        self.info_text = ""
        if self.path_field:
            # default filename in current directory
            self.path_field.text = "vault_backup.psafe"

    def do_export(self):
        vault = getattr(app_state, "vault", None)
        if not vault:
            self._show_popup("No Vault", "Vault is not loaded.")
            return

        # Prefer current master password if available
        master_pw = getattr(app_state, "master_password", "") or None
        filepath = (self.path_field.text or "").strip() if self.path_field else ""
        if not filepath:
            self._show_popup("Path Required", "Please enter a backup filepath.")
            return

        if not master_pw:
            # ask user for master password via popup
            self._ask_for_password_and_export(filepath)
            return

        try:
            vault.export_encrypted_backup(filepath, master_pw)
            self.info_text = "Export successful"
            self._show_popup("", f"Backup saved to:\n{filepath}")
        except Exception as e:
            Logger.exception("Export failed")
            self.info_text = f"Error: {e}"
            self._show_popup("Export Failed", f"Failed to export backup:\n{e}")

    def _ask_for_password_and_export(self, filepath: str):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)

        label = Label(
            text="Enter master password to encrypt backup:",
            size_hint_y=None,
            height=40
        )
        content.add_widget(label)

        pw_input = TextInput(
            password=True,
            multiline=False,
            hint_text="Master password",
            size_hint_y=None,
            height=40
        )
        content.add_widget(pw_input)

        # Buttons layout
        btn_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        ok_btn = Button(text="Export")
        cancel_btn = Button(text="Cancel")
        btn_layout.add_widget(ok_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(
            title="Export Backup",
            content=content,
            size_hint=(None, None),
            size=(420, 200),
            auto_dismiss=False
        )

        def do_export_pw(*_):
            popup.dismiss()
            try:
                app_state.vault.export_encrypted_backup(filepath, pw_input.text or "")
                self.info_text = "Export successful"
                self._show_popup("", f"Backup saved to:\n{filepath}")
            except Exception as e:
                Logger.exception("Export failed with password input")
                self.info_text = f"Error: {e}"
                self._show_popup("Export Failed", f"Failed:\n{e}")

        ok_btn.bind(on_release=do_export_pw)
        cancel_btn.bind(on_release=popup.dismiss)

        popup.open()

    def _show_popup(self, title: str, message: str):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)

        msg_label = Label(
            text=message,
            size_hint_y=None,
            height=60
        )
        content.add_widget(msg_label)

        ok_btn = Button(
            text="OK",
            size_hint_y=None,
            height=40
        )
        content.add_widget(ok_btn)

        popup = Popup(
            title=title,
            content=content,
            size_hint=(None, None),
            size=(420, 180),
            auto_dismiss=False
        )
        ok_btn.bind(on_release=popup.dismiss)
        popup.open()

    def goto_home(self):
        if "HOME" in self.manager.screen_names:
            self.manager.current = "HOME"