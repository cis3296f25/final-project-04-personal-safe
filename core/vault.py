from typing import Dict, List, Tuple
from . import storage
from core import backup as backup_mod  # adjust import path


class Vault:
    def __init__(self, master_password: str) -> None:
        # load_vault now requires a master password to derive the key
        self._master_password = master_password
        self._data: Dict[str, str] = storage.load_vault(master_password)

    def add(self, site: str, pwd: str) -> None:
        if not site or not pwd:
            return
        self._data[site] = pwd
        storage.save_vault(self._data, self._master_password)

    def items(self) -> List[Tuple[str, str]]:
        return list(self._data.items())

    def is_empty(self) -> bool:
        return not self._data

    def get_sites(self) -> List[str]:
        # Return list of site names
        return list(self._data.keys())

    def delete(self, site: str) -> bool:
        # Delete entry by site name
        # true if deleted, false if not found
        if site in self._data:
            del self._data[site]
            storage.save_vault(self._data, self._master_password)
            return True
        return False

    def get(self, site):
        return self._data.get(site)

    def export_encrypted_backup(self, filepath: str, master_password: str) -> None:
        """
        Export the entire vault (self._data) to an encrypted backup file.
        `master_password` must be provided (it is not read from disk here).
        """
        if self._data is None:
            raise ValueError("Vault has no data to export")
        if not master_password:
            raise ValueError("Master password required for export")
        
        # Convert items in vault to dict for JSON
        data_to_backup = {site: pwd for site, pwd in self.items()}
        
        # Choose what to export
        obj = {"entries": data_to_backup}
        backup_mod.save_encrypted_backup_file(obj, master_password, filepath)

    def import_encrypted_backup(self, filepath: str, master_password: str, replace_existing: bool = True) -> None:
        """
        Import an encrypted backup from `filepath`, decrypting with `master_password`.
        If replace_existing is True, the vault's internal data will be replaced by backup entries.
        Otherwise, backup entries will be merged (backup wins on key collisions).
        """
        if not master_password:
            raise ValueError("Master password required for import")
        data = backup_mod.load_encrypted_backup_file(filepath, master_password)
        if not isinstance(data, dict) or "entries" not in data:
            raise ValueError("Backup file missing entries")
        entries = data["entries"] or {}
        if not isinstance(entries, dict):
            raise ValueError("Backup entries malformed")

        if replace_existing:
            self._data = dict(entries)
        else:
            # merge, backup entries win
            self._data = {**(self._data or {}), **entries}

        storage.save_vault(self._data, self._master_password)