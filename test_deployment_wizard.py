"""Test launcher for deployment wizard."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk
from tkinter import messagebox
from ui.deployment_wizard import DeploymentWizard

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.geometry("400x300")
    app.title("Test Deployment Wizard")

    def open_wizard():
        project_file = Path("output/ts3/ts3.ciraproject")
        if project_file.exists():
            wizard = DeploymentWizard(app, project_file)
        else:
            messagebox.showerror("Error", f"Project file not found:\n{project_file}")

    label = ctk.CTkLabel(
        app,
        text="CiRA Deployment Wizard Test",
        font=ctk.CTkFont(size=20, weight="bold")
    )
    label.pack(pady=40)

    btn = ctk.CTkButton(
        app,
        text="🚀 Open Deployment Wizard",
        command=open_wizard,
        width=250,
        height=50,
        font=ctk.CTkFont(size=14, weight="bold")
    )
    btn.pack(pady=20)

    info_label = ctk.CTkLabel(
        app,
        text="Project: ts3 (Gesture Classification)\n5 classes: idle, snake, updown, wave, shake",
        font=ctk.CTkFont(size=11),
        text_color="gray60"
    )
    info_label.pack(pady=10)

    app.mainloop()

if __name__ == "__main__":
    main()
