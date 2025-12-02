from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.logger import Logger
from app_state import app_state


class DeletePasswordScreen(Screen):
    site_spinner = ObjectProperty(None)
    info_text = StringProperty("")
    sites = ListProperty([])

    def on_pre_enter(self, *args):
        self.refresh_sites()
        self.info_text = ""

    def refresh_sites(self):
        if app_state.vault:
            self.sites = app_state.vault.get_sites()
        else:
            self.sites = []
        if self.site_spinner and self.sites:
            self.site_spinner.values = self.sites
            self.site_spinner.text = self.sites[0] if self.sites else ""

    def do_delete(self):
        if not (app_state.vault and self.site_spinner):
            self.info_text = "No vault"
            return
        site = self.site_spinner.text
        if not site:
            self.info_text = "Select site"
            return
        try:
            if app_state.vault.delete(site):
                self.info_text = "Deleted"
                self.refresh_sites()
                try:
                    from kivy.app import App

                    App.get_running_app().show_status("Deleted")
                except Exception:
                    pass
            else:
                self.info_text = "Not found"
        except Exception as e:
            Logger.exception("Delete failed")
            self.info_text = f"Error: {e}"

    def go_home(self):
        if "HOME" in self.manager.screen_names:
            self.manager.current = "HOME"
