import customtkinter
from tkinter import PhotoImage, Label, messagebox
from PIL import Image
import minecraft_launcher_lib
import subprocess
import pickle
import json
import uuid
import os
import shutil
import threading
import random
import configparser
import hashlib
import ctypes
import time
from pypresence import Presence

"""
Rich Presence setup
"""
presence = Presence("1495473776043757819")

def discord_presence_worker(): #Function setting up the link with the discord API
        presence.connect()
        
        presence.update(
            state="Idle",
            large_text="Astro Launcher 2",
            small_image="block"
        )
        while True:
            time.sleep(15)

def update_discord_presence(state): #Function used to update the activity of the user
    presence.update(state=state)
    
thread = threading.Thread(target=discord_presence_worker, daemon=True)
thread.start()

"""
Class defining a profile
"""
class Profile:
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.profile_directory = "instances/" + self.name
        self.username = "Steve"
        self.ram = "2"
        
    def launch_sequence(self):
        self.found = False
        for element in minecraft_launcher_lib.utils.get_installed_versions(self.profile_directory):
            if element["id"] == self.version:
                self.found = True
                self.launch()
        if self.found == False:
            minecraft_launcher_lib.install.install_minecraft_version(self.version, self.profile_directory)
            self.launch()

    def launch(self):
        self.options = {
            "username": self.username,
            "uuid": str(uuid.UUID(bytes=hashlib.md5(bytes(f"OfflinePlayer:{self.username}", "utf-8")).digest()[:16])),
            "token": "",
            "jvmArguments": [f"-Xmx{self.ram}G", f"-Xms{self.ram}G"]}
        command = minecraft_launcher_lib.command.get_minecraft_command(self.version, self.profile_directory, self.options)
        
        process = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
        
        app.root.withdraw()
        update_discord_presence("Playing Minecraft")
        
        wait_thread = threading.Thread(target=self.wait_minecraft_close, args=(process,), daemon=True)
        wait_thread.start()
    
    def wait_minecraft_close(self, process):
        process.wait()
        time.sleep(1)
        app.root.deiconify()
        app.main_page()
        update_discord_presence("Idle")


"""
Class defining the launcher itself : GUI and the interaction between this GUI and the BackEnd
"""
class Launcher:
    def __init__(self):
        
        #Window proprieties
        self.root = customtkinter.CTk()
        self.root.geometry("1000x550")
        self.root.title("Astro Launcher 2")
        self.root.resizable(False, False)
        self.root.iconbitmap("assets/icon.ico")
        self.root.configure(fg_color="#1C1C1C")
        
        #Background selection
        self.bg_number = random.randint(0, 2)
        if self.bg_number == 0: self.bg_img = PhotoImage(file="assets/background1.png")
        elif self.bg_number == 1: self.bg_img = PhotoImage(file="assets/background2.png")
        elif self.bg_number == 2: self.bg_img = PhotoImage(file="assets/background3.png")  
        self.bg = Label(self.root, image=self.bg_img)      

        #Assets importation
        self.play = Image.open("assets/play.png")
        self.creeper = Image.open("assets/off_login_logo.png")
        self.block = Image.open("assets/block_logo.png")
        
        #Launcher variables
        self.profile_list = self.load_profiles_list()
        self.profile_list_by_name = []
        self.get_profile_list_by_name()
        self.username = None
        
        #GUI Variables
        self.setup_widgets()
        
    def setup_widgets(self): #Filling widgets proprieties
        self.play_button = customtkinter.CTkButton(self.root, command=self.start_game,
                                                    fg_color="#47316F",
                                                    bg_color="#1C1C1C",
                                                    hover_color="#342451",
                                                    text="PLAY ",
                                                    width=200,
                                                    height=50,
                                                    corner_radius=20,
                                                    image=customtkinter.CTkImage(self.play, size=(30, 30)),
                                                    compound="right",
                                                    font=("Arial", 25, "bold"))
                                                    
        self.settings_button = customtkinter.CTkButton(self.root, command=self.settings_page,
                                                    fg_color="#47316F",
                                                    bg_color="#1C1C1C",
                                                    hover_color="#342451",
                                                    text="⚙",
                                                    width=50,
                                                    height=50,
                                                    corner_radius=20,
                                                    font=("Arial", 30, "bold"))

        self.add_profile_button = customtkinter.CTkButton(self.root,
                                                            command=self.create_profile_page,
                                                            fg_color="#47316F",
                                                            bg_color="#1C1C1C",
                                                            hover_color="#342451",
                                                            text="+",
                                                            width=46,
                                                            height=28,
                                                            corner_radius=100)

        self.profiles_combobox_variable = customtkinter.StringVar()
        self.profiles_combobox = customtkinter.CTkComboBox(self.root,
                                                            variable=self.profiles_combobox_variable,
                                                            values=self.profile_list_by_name,
                                                            bg_color="#1C1C1C", 
                                                            fg_color="#47316F", 
                                                            button_color="#47316F", 
                                                            border_color="#47316F", 
                                                            text_color="white", 
                                                            state="readonly", 
                                                            corner_radius=15, 
                                                            width=150)

        self.edit_profile_button = customtkinter.CTkButton(self.root,
                                                                text="EDIT PROFILE",
                                                                height=26,
                                                                command=self.edit_profile_page,
                                                                fg_color="#47316F",
                                                                bg_color="#1C1C1C",
                                                                hover_color="#342451",
                                                                corner_radius=15,
                                                                width=200)

        self.loading_bar = customtkinter.CTkProgressBar(self.root,
                                                            mode="indeterminate",
                                                            width=900,
                                                            height=20,
                                                            corner_radius=100,
                                                            fg_color="#474747",
                                                            bg_color="#1C1C1C",
                                                            progress_color="#47316F")
        
        self.loading_label = customtkinter.CTkLabel(self.root, 
                                                           text="Downloading game files ...",
                                                           font=("Arial", 15, "bold"))

        self.back_button = customtkinter.CTkButton(self.root,
                                                        command=self.main_page,
                                                        fg_color="#972626",
                                                        bg_color="#1C1C1C",
                                                        hover_color="#751F1F",
                                                        text="CANCEL",
                                                        width=200,
                                                        height=50,
                                                        corner_radius=20,
                                                        font=("Arial", 25, "bold"))
        
        self.create_profile_button = customtkinter.CTkButton(self.root,
                                                                command=self.create_profile,
                                                                fg_color="#348D5C",
                                                                bg_color="#1C1C1C",
                                                                hover_color="#24512F",
                                                                text="CREATE",
                                                                width=200,
                                                                height=50,
                                                                corner_radius=20,
                                                                font=("Arial", 25, "bold"))
        
        self.save_edited_profile_button = customtkinter.CTkButton(self.root,
                                                                command=self.edit_profile,
                                                                fg_color="#348D5C",
                                                                bg_color="#1C1C1C",
                                                                hover_color="#24512F",
                                                                text="SAVE",
                                                                width=200,
                                                                height=50,
                                                                corner_radius=20,
                                                                font=("Arial", 25, "bold"))
        
        self.delete_profile_button = customtkinter.CTkButton(self.root,
                                                            fg_color="#47316F",
                                                            bg_color="#1C1C1C",
                                                            hover_color="#342451",
                                                            command=self.delete_profile,
                                                            text="DELETE PROFILE",
                                                            width=500,
                                                            height=50,
                                                            corner_radius=20)
        
        self.profile_name_entry = customtkinter.CTkEntry(self.root,
                                                                height=50,
                                                                placeholder_text="*profile name",
                                                                placeholder_text_color="gray",
                                                                bg_color="#1C1C1C",
                                                                fg_color="white",
                                                                border_color="white",
                                                                text_color="black",
                                                                corner_radius=15,
                                                                width=500)
        
        self.profile_edition_label = customtkinter.CTkLabel(self.root, 
                                                           text="Profile Editor",
                                                           font=("Arial", 50, "bold"))
        
        self.profile_creation_label = customtkinter.CTkLabel(self.root, 
                                                           text="New Profile",
                                                           font=("Arial", 50, "bold"))
        
        self.block = customtkinter.CTkImage(light_image=self.block,
                                        dark_image=self.block,
                                        size=(200, 200))
        self.block = customtkinter.CTkLabel(self.root, image=self.block, text="")
        
        self.versions_combobox_variable = customtkinter.StringVar()
        self.versions_combobox = customtkinter.CTkComboBox(self.root,
                                                            variable=self.versions_combobox_variable,
                                                            bg_color="#1C1C1C", 
                                                            fg_color="#47316F", 
                                                            button_color="#47316F", 
                                                            border_color="#47316F", 
                                                            text_color="white", 
                                                            state="readonly", 
                                                            height=50,
                                                            corner_radius=15,
                                                            width=500)
            
        self.profile_dir_button = customtkinter.CTkButton(self.root,
                                                            fg_color="#47316F",
                                                            bg_color="#1C1C1C",
                                                            hover_color="#342451",
                                                            command=self.open_directory,
                                                            text="OPEN DIRECTORY",
                                                            width=500,
                                                            height=50,
                                                            corner_radius=20)

        self.connection_label = customtkinter.CTkLabel(self.root, 
                                                           text="Welcome !",
                                                           font=("Arial", 50, "bold"))
        
        self.creeper = customtkinter.CTkImage(light_image=self.creeper,
                                        dark_image=self.creeper,
                                        size=(200, 200))
        self.creeper = customtkinter.CTkLabel(self.root, image=self.creeper, text="")
        
        self.username_entry = customtkinter.CTkEntry(self.root,
                                                                height=50,
                                                                placeholder_text="*username",
                                                                placeholder_text_color="gray",
                                                                bg_color="#1C1C1C",
                                                                fg_color="white",
                                                                border_color="white",
                                                                text_color="black",
                                                                corner_radius=15,
                                                                width=500)
        
        self.off_login_button = customtkinter.CTkButton(self.root,
                                                            fg_color="#47316F",
                                                            bg_color="#1C1C1C",
                                                            hover_color="#342451",
                                                            command=self.off_login,
                                                            text="LOGIN",
                                                            width=500,
                                                            height=50,
                                                            corner_radius=20)
                                                        
        self.settings_label_title = customtkinter.CTkLabel(self.root, 
                                                           text="Settings",
                                                           font=("Arial", 50, "bold"))
        
        self.ram_slider = customtkinter.CTkSlider(self.root, 
                                                  from_=1, to=self.get_system_ram()-1, 
                                                  number_of_steps=int(self.get_system_ram()-1), 
                                                  width=500,
                                                  command=self.update_ram_label,
                                                  button_color="#47316F",
                                                  button_hover_color="#342451",
                                                  progress_color="#47316F")
                                                  
        self.ram_value_label = customtkinter.CTkLabel(self.root, 
                                                      text="Allocated RAM: 2 GB",
                                                      font=("Arial", 25, "bold"))
                                                      
        self.save_settings_button = customtkinter.CTkButton(self.root,
                                                                command=self.save_settings,
                                                                fg_color="#348D5C",
                                                                bg_color="#1C1C1C",
                                                                hover_color="#24512F",
                                                                text="SAVE",
                                                                width=200,
                                                                height=50,
                                                                corner_radius=20,
                                                                font=("Arial", 25, "bold"))
        
                        
    def clear_ui(self): #Clearing the widgets in the window
        self.gui_update()
        self.play_button.place_forget()
        self.settings_button.place_forget()
        self.add_profile_button.place_forget()
        self.profiles_combobox.place_forget()
        self.edit_profile_button.place_forget()
        self.loading_bar.place_forget()
        self.back_button.place_forget()
        self.create_profile_button.place_forget()
        self.save_edited_profile_button.place_forget()
        self.delete_profile_button.place_forget()
        self.profile_dir_button.place_forget()
        self.profile_name_entry.place_forget()
        self.profile_edition_label.place_forget()
        self.versions_combobox.place_forget()
        self.profile_creation_label.place_forget()
        self.username_entry.place_forget()
        self.connection_label.place_forget()
        self.off_login_button.place_forget()
        self.creeper.place_forget()
        self.block.place_forget()
        self.loading_label.place_forget()
        self.settings_label_title.place_forget()
        self.ram_slider.place_forget()
        self.ram_value_label.place_forget()
        self.save_settings_button.place_forget()

    def get_system_ram(self): # Returns system RAM in GB
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_ram_gb = round(stat.ullTotalPhys / (1024 ** 3))
        if total_ram_gb < 2:
            total_ram_gb = 2
        return total_ram_gb

    def loading_page(self): #Displaying loading page widgets in the window
        self.clear_ui()
        self.bg.pack()
        self.loading_bar.place(relx=0.05, rely=0.882)
        self.loading_label.place(relx=0.05, rely=0.92)
        self.loading_bar.start()
        
    def off_login_page(self): #Displaying offline login page widgets in the window
        self.clear_ui()
        self.bg.pack_forget()
        self.connection_label.place(relx=0.5, rely=0.1, anchor="center")
        self.creeper.place(relx=0.5, rely=0.37, anchor="center")
        self.username_entry.place(relx=0.5, rely=0.68, anchor="center")
        self.off_login_button.place(relx=0.5, rely=0.80, anchor="center")
        self.set_username()
        
    def main_page(self): #Displaying main page widgets in the window
        self.clear_ui()
        self.bg.pack()
        self.profiles_combobox_variable.set(self.get_last_used_profile())
        self.profiles_combobox.place(relx=0.05, rely=0.836)
        self.add_profile_button.place(relx=0.204, rely=0.836)
        self.edit_profile_button.place(relx=0.05, rely=0.91)
        self.settings_button.place(relx=0.66, rely=0.855)
        self.play_button.place(relx=0.75, rely=0.855)
        
    def settings_page(self): #Displaying settings page widgets in the window
        self.clear_ui()
        self.bg.pack_forget()
        self.settings_label_title.place(relx=0.5, rely=0.1, anchor="center")
        
        saved_ram = self.get_saved_ram()
        self.ram_slider.set(saved_ram)
        self.update_ram_label(saved_ram)
        
        self.ram_value_label.place(relx=0.5, rely=0.4, anchor="center")
        self.ram_slider.place(relx=0.5, rely=0.5, anchor="center")
        
        self.back_button.place(relx=0.75, rely=0.855)
        self.save_settings_button.place(relx=0.525, rely=0.855)

    def update_ram_label(self, value): #Update the ram text
        self.ram_value_label.configure(text=f"Allocated RAM: {int(float(value))} GB")
        
    def save_settings(self): #Save the settings and return to main page
        if 'GUI' not in config:
            config['GUI'] = {}
        config.set('GUI', 'ram_allocation', str(int(self.ram_slider.get())))
        with open("config.ini", 'w') as configfile:
            config.write(configfile)
        self.main_page()
        
    def get_saved_ram(self): #Returns the saved RAM allocation
        if 'GUI' in config and 'ram_allocation' in config['GUI']:
            return int(config['GUI']['ram_allocation'])
        return 2
        
    def edit_profile_page(self): #Displaying profile edition page widgets in the window
        if self.profiles_combobox_variable.get() == "none" :
            return
        self.clear_ui()
        self.bg.pack_forget()
        self.back_button.place(relx=0.75, rely=0.855)
        self.save_edited_profile_button.place(relx=0.525, rely=0.855)
        self.delete_profile_button.place(relx=0.5, rely=0.72, anchor="center")
        self.profile_dir_button.place(relx=0.5, rely=0.60, anchor="center")
        self.profile_name_entry.place(relx=0.5, rely=0.36, anchor="center")
        self.profile_edition_label.place(relx=0.5, rely=0.1, anchor="center")
        self.versions_combobox.place(relx=0.5, rely=0.48, anchor="center")
        
        self.profile = self.get_profile_from_name(self.profiles_combobox.get())
        self.available_versions = self.get_available_versions(self.profile)
        self.versions_combobox.configure(values=self.available_versions)
        self.versions_combobox.set(self.profile.version)
        self.profile_name_entry.insert(0, self.profile.name)
        self.save_last_used_profile()
        
    def create_profile_page(self): #Displaying profile creation page widgets in the window
        self.clear_ui()
        self.bg.pack_forget()
        self.profile_name_entry.place(relx=0.5, rely=0.58, anchor="center")
        self.back_button.place(relx=0.75, rely=0.855)
        self.create_profile_button.place(relx=0.525, rely=0.855)
        self.profile_creation_label.place(relx=0.5, rely=0.1, anchor="center")
        self.block.place(relx=0.5, rely=0.33, anchor="center")
        self.versions_combobox.place(relx=0.5, rely=0.70, anchor="center")     

        installable_versions = self.get_versions()
        self.versions_combobox.configure(values=installable_versions)
        latest_released_version = installable_versions[0]
        self.versions_combobox.set(latest_released_version)
        self.save_last_used_profile()
    
    def gui_update(self): #Filling profiles combobox and clearing profile name entry
        self.profiles_combobox.configure(values=self.get_profile_list_by_name())
        self.profile_name_entry.delete(0, customtkinter.END)
        
    def display(self): #Displaying the window on the offline login page
        self.off_login_page()
        self.root.mainloop()
        
    def get_versions(self): #Returns all the versions of the game
        versions_list = []
        for version in minecraft_launcher_lib.utils.get_version_list():
            if version["type"] == "release": versions_list.append(version["id"])
        return versions_list
            
    def get_available_versions(self, profile): #Returns all the versions of the game and the ones installed
        available_versions_list = []
        for version in minecraft_launcher_lib.utils.get_available_versions(profile.profile_directory):
            if version["type"] == "release": available_versions_list.append(version["id"])
        return available_versions_list
    
    def verify_str(self, string_to_verify): #Verify if a string is valid for a profile name (not empty and only contains allowed characters)
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        if string_to_verify == "": return False
        for element in string_to_verify:
            if element not in allowed_chars:
                return False
        return True
    
    def create_dummy_launcher_config(self, profile_directory): #Create a dummy launcher_profiles.json to avoid errors when launching the game for the first time
        data = {
            "profiles": {
                "Default": {
                    "name": "Default",
                    "type": "custom",
                    "created": "2024-01-01T00:00:00.000Z",
                    "lastUsed": "2024-01-01T00:00:00.000Z",
                    "icon": "Grass",
                    "lastVersionId": "1.20.1"
                }
            },
            "settings": {
                "crashAssistance": True,
                "enableAdvanced": True
            },
            "launcherVersion": {
                "format": 21,
                "name": "2.x",
                "profilesFormat": 3
            }
        }
        os.makedirs(profile_directory, exist_ok=True)
        path = os.path.join(profile_directory, "launcher_profiles.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def create_profile(self): #Create a profile
        if not self.verify_str(self.profile_name_entry.get()) or self.profile_name_entry.get() in self.profile_list_by_name:
            messagebox.showerror("Error", "Invalid Name.")
            return 1
        os.mkdir(f"instances/{self.profile_name_entry.get()}")
        self.create_dummy_launcher_config(f"instances/{self.profile_name_entry.get()}")
        self.profile_list.append(Profile(self.profile_name_entry.get(), self.versions_combobox.get()))
        self.save_profiles()
        self.profiles_combobox_variable.set(self.profile_name_entry.get())
        self.save_last_used_profile()
        self.main_page()

    def edit_profile(self): #Edit a profile
        old_name = self.profiles_combobox.get()
        new_name = self.profile_name_entry.get()
        new_version = self.versions_combobox.get()

        if  (new_name != old_name and new_name in self.profile_list_by_name) or not self.verify_str(new_name):
            messagebox.showerror("Error", "Invalid Name.")
            return 1

        target_index = -1
        for i, p in enumerate(self.profile_list):
            if p.name == old_name:
                target_index = i
                break

        if target_index != -1:
            old_profile = self.profile_list[target_index]
            old_dir = old_profile.profile_directory
            new_dir = os.path.join("instances", new_name)
            os.rename(old_dir, new_dir)
            self.profile_list[target_index] = Profile(new_name, new_version)
            
            self.save_profiles()
            self.profiles_combobox_variable.set(new_name)
            self.save_last_used_profile()
            self.main_page()
            

    def delete_profile(self): #Delete a profile
        profile_name = self.profiles_combobox.get()
        if not messagebox.askyesno("Profile Removal", f"Are you sure you want to delete '{profile_name}' and all its data?"):
            return 1

        target_index = -1
        for i, p in enumerate(self.profile_list):
            if p.name == profile_name:
                target_index = i
                break

        if target_index != -1:
            profile_to_delete = self.profile_list[target_index]
            shutil.rmtree(profile_to_delete.profile_directory)
            self.profile_list.pop(target_index)

        self.save_profiles()
        self.gui_update()
        if len(self.profile_list_by_name) < 1:
            self.profiles_combobox_variable.set("none")
        else:
            self.profiles_combobox_variable.set(self.profile_list_by_name[0])
        self.save_last_used_profile()
        self.main_page()
        messagebox.showinfo("Profile Removal", f"Profile '{profile_name}' has been deleted.")
        
    def open_directory(self): #Opens the profile's directory
        profile_name = self.profiles_combobox.get()
        profile = self.get_profile_from_name(profile_name)
        path = os.path.abspath(profile.profile_directory)
        os.startfile(path)
        
    def save_profiles(self): #Save a profile
        with open("profiles.dat", "wb") as f:
            pickle.dump(self.profile_list, f)
        
    def off_login(self): #Offline authentification
        self.username = self.username_entry.get()
        if len(self.username) < 1 or " " in self.username:
            messagebox.showerror("Error", "Invalid Username.")
        else:
            self.save_last_username()
            self.main_page()
            
    def set_username(self): #Set latest username in the entry
        saved_username = config['GUI']['last_used_nickname']
        if saved_username != "Steve":
            self.username_entry.insert(0, saved_username)
            
    def save_last_username(self): #Save the last used username
        config.set('GUI', 'last_used_nickname', self.username_entry.get())
        with open("config.ini", 'w') as configfile:
            config.write(configfile)
            
    def get_last_used_profile(self): #Returns the last used profile
        saved_profile = config['GUI']['last_used_profile']
        return saved_profile
            
    def save_last_used_profile(self): #Save the last used profile
        config.set('GUI', 'last_used_profile', self.profiles_combobox_variable.get())
        with open("config.ini", 'w') as configfile:
            config.write(configfile)
            
    
    def load_profiles_list(self): #Load the stored profiles list
        filename = "profiles.dat"
        if not os.path.exists(filename) or os.path.getsize(filename) == 0:
            return []
        with open(filename, "rb") as f:
            return pickle.load(f)
        
    def get_profile_list_by_name(self): #Returns a list with all the profiles's names
        self.profile_list_by_name = []
        for element in self.profile_list:
            self.profile_list_by_name.append(element.name)
        return self.profile_list_by_name
        
    def get_profile_from_name(self, name): #Returns a profile from its name
        for i in range(len(self.profile_list_by_name)):
            if name == self.profile_list[i].name:
                return self.profile_list[i]
    
    def start_game(self): #Start the game files download and launch
        
        selected_profile_name = self.profiles_combobox_variable.get()
        if self.profiles_combobox.get() == "none":
            messagebox.showerror("Error", "Create a profile first !")
            return
        self.loading_page()
        selected_profile = self.get_profile_from_name(selected_profile_name)
        selected_profile.username = self.username
        selected_profile.ram = str(self.get_saved_ram())
        self.save_last_used_profile()
        thread = threading.Thread(target=selected_profile.launch_sequence, daemon=True)
        thread.start()  
        

"""
Entry Point
"""
if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')

    if not os.path.exists("instances"):
        os.mkdir("instances")
    
    app = Launcher()
    app.display()
