from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from pathlib import Path
from .theme import Theme


# Ensure KV for login/create is loaded if present
def _load_kv_if_exists():
    for kv in (
        "ui/kv/components.kv",
        "ui/kv/login_screen.kv",
        "ui/kv/login.kv",
        "ui/kv/create_master.kv",
        "ui/kv/home.kv",
        "ui/kv/dialogs.kv",
        "kivy_ui.kv",
        "ui/kv/profile.kv",
        "ui/kv/verify_code_screen.kv",
        "ui/kv/backup_export_screen.kv",
        "ui/kv/backup_import_Screen.kv",
        "ui/kv/clear_vault_screen.kv",
    ):
        p = Path(kv)
        if p.exists():
            Builder.load_file(str(p))


_load_kv_if_exists()

from ui.screens.login_screen import LoginScreen
from ui.screens.create_master_screen import CreateMasterScreen
from ui.screens.home_screen import HomeScreen
from ui.screens.add_password_screen import AddPasswordScreen
from ui.screens.edit_password_screen import EditPasswordScreen
from ui.screens.delete_password_screen import DeletePasswordScreen
from ui.screens.profile_screen import ProfileScreen
from ui.screens.verify_code_screen import VerifyCodeScreen
from ui.screens.reset_password_screen import ResetPasswordScreen
from ui.screens.backup_export_screen import BackupExportScreen
from ui.screens.backup_import_screen import BackupImportScreen
from ui.screens.clear_vault_screen import ClearVaultScreen
from core import masterPassword as mp

class PersonalSafeApp(App):
    title = "Personal Safe"

    def build(self):
        # Ensure vault is unset until user unlocks/creates
        self.vault = None
        self.theme = Theme()
        Window.minimum_width, Window.minimum_height = 480, 380
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(LoginScreen(name="LOGIN"))
        sm.add_widget(CreateMasterScreen(name="CREATE"))
        sm.add_widget(HomeScreen(name="HOME"))
        sm.add_widget(AddPasswordScreen(name="ADD"))
        sm.add_widget(EditPasswordScreen(name="EDIT"))
        sm.add_widget(DeletePasswordScreen(name="DELETE"))
        sm.add_widget(ProfileScreen(name="PROFILE"))
        sm.add_widget(VerifyCodeScreen(name="VERIFY_CODE"))
        sm.add_widget(ResetPasswordScreen(name="RESET_PASSWORD"))
        sm.add_widget(BackupExportScreen(name="BACKUP_EXPORT"))
        sm.add_widget(BackupImportScreen(name="BACKUP_IMPORT"))
        sm.add_widget(ClearVaultScreen(name="CLEAR_VAULT"))

        sm.app = self
        self.sm = sm
        # Route based on existence of master hash
        if Path(mp.masterHashFile).exists():
            sm.current = "LOGIN"
        else:
            sm.current = "CREATE"
        return sm
