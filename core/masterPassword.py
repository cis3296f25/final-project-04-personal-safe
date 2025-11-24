import json
import os
import ssl
import app_state
import bcrypt
import tkinter as tk
import base64
import time
import smtplib
import secrets
from email.message import EmailMessage
from tkinter import simpledialog, messagebox
from typing import Tuple

masterHashFile = os.path.join(os.path.expanduser("~"), ".vaultMaster.hash")
recoveryFile = os.path.join(os.path.expanduser("~"), ".vaultRecovery.json")

def createMasterPassword(password: str):
    "Create and store master password"
    password = password.strip()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    with open(masterHashFile, "wb") as f:
        f.write(hashed)
    print("Master password created")

def verifyMasterPassword(password: str) -> bool:
    "Check master password"
    password = password.strip()
    with open(masterHashFile, "rb") as f:
        storedHash = f.read()
    return bcrypt.checkpw(password.encode(), storedHash)

#Recovery Helper Functions
def loadRecovery() -> dict:
    if os.path.exists(recoveryFile):
        with open(recoveryFile, "r", encoding="utf-8") as f:
            return json.load(f)

def saveRecovery(obj: dict) -> None:
    tmp = recoveryFile + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    os.replace(tmp, recoveryFile)
    try:
        os.chmod(recoveryFile, 0o600)
    except Exception:
        pass

def setRecoveryEmail(email: str):
    obj = loadRecovery()
    if obj is None:
        obj = {}  #create new dict if nothing exists
    obj["email"] = email.strip()
    saveRecovery(obj)
    '''
    obj = loadRecovery()
    obj["email"] = email.strip()
    obj["token_hash_b64"] = None
    obj["token_expiry"] = None
    obj["attempts_left"] = 3
    saveRecovery(obj)'''

def storeTokenHash(token: str, ttl_seconds: int = 3600) -> None:
    token_bytes = token.encode()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(token_bytes, salt)
    b64 = base64.b64encode(hashed).decode()
    obj = loadRecovery()
    obj['token_hash_b64'] = b64
    obj['token_expiry'] = int(time.time()) + ttl_seconds
    obj['attempts_left'] = 3
    saveRecovery(obj)

def clearToken() -> None:
    obj = loadRecovery()
    obj.pop('token_hash_b64', None)
    obj.pop('token_expiry', None)
    obj['attempts_left'] = 3
    saveRecovery(obj)

def getMasterPassword(parent=None):
    "First time set up or Login verification"
    createdRoot = False
    if parent is None:
        parent = tk.Tk()
        createdRoot = True
    
    if email:
        setRecoveryEmail(email)
        #Update profile file and app_state
        from ui.screens.profile_screen import save_profile_to_disk
        from app_state import app_state
        profile = {"email": email, "display_name": ""}
        app_state.profile = profile
        save_profile_to_disk(profile)

    try:
        if not os.path.exists(masterHashFile):
            while True:
                pw = simpledialog.askstring("Create Master Password", "Enter a new master password:", show="*", parent=parent)
                if pw is None:
                    return None
                confirm = simpledialog.askstring("Confirm Password", "Confirm your master password:", show="*", parent=parent)

                if confirm is None:
                    if messagebox.askyesno("Cancel setup?", "cancel", parent=parent):
                        return None
                    else:
                        continue
                
                if pw != confirm:
                    messagebox.showerror("Mismatch", "Passwords do not match", parent=parent)
                    continue
                if pw.strip() == "":
                    messagebox.showerror("Invalid", "Password cannot have white space", parent=parent)
                    continue

                createMasterPassword(pw)
                messagebox.showinfo("Success", "Master password created", parent=parent)
                
                email = simpledialog.askstring("Recovery Email (optional)", "Enter recovery email (optional):", parent=parent)
                if email:
                    setRecoveryEmail(email)
                    messagebox.showinfo("Recovery", f"Recovery email {email} saved.", parent=parent)
            
                
                return pw
            
        else:
            attemptsLeft = 3
            while attemptsLeft > 0:
                pw = simpledialog.askstring("Master password", f"Enter password - attempts left {attemptsLeft}", show="*", parent=parent)
                if pw is None:
                    return None
                if verifyMasterPassword(pw):
                    return pw
                attemptsLeft -= 1
                continue
                
            messagebox.showerror("Access Denied", "incorrect password", parent=parent)
            return None

    finally:
        if createdRoot:
            parent.destroy()