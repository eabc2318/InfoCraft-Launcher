import customtkinter
from tkinter import PhotoImage, Label, messagebox
from PIL import Image
import minecraft_launcher_lib
import subprocess
import uuid
import os
import threading
import configparser
import hashlib
import ctypes
import time

"""
Class defining a profile
"""
class Profile:
    def __init__(self, name, version): #Initialize a profile with default launch settings
        self.name = name
        self.version = version
        self.profile_directory = "instances/" + self.name
        self.username = "Steve"
        self.ram = "2"
        
    def launch_sequence(self): #Install missing version if needed, then launch
        self.found = False
        for element in minecraft_launcher_lib.utils.get_installed_versions(self.profile_directory):
            if element["id"] == self.version:
                self.found = True
                self.launch()
        if self.found == False:
            minecraft_launcher_lib.install.install_minecraft_version(self.version, self.profile_directory)
            self.launch()

    def launch(self): #Build launch command and start Minecraft process
        try:
            self.options = {
                "username": self.username,
                "uuid": str(uuid.UUID(bytes=hashlib.md5(bytes(f"OfflinePlayer:{self.username}", "utf-8")).digest()[:16])),
                "token": "",
                "jvmArguments": [f"-Xmx{self.ram}G", f"-Xms{self.ram}G"],
                "executablePath": "javaw",
                "server": "infocraft89.aternos.me",
                "port": "13619"}
            command = minecraft_launcher_lib.command.get_minecraft_command(self.version, self.profile_directory, self.options)
            
            process = subprocess.Popen(command)
            
            app.root.withdraw()
            
            wait_thread = threading.Thread(target=self.wait_minecraft_close, args=(process,), daemon=True)
            wait_thread.start()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while launching the game: {str(e)}")
            app.root.deiconify()
            app.main_page()

    def wait_minecraft_close(self, process): #Restore launcher UI when game closes
        process.wait()
        time.sleep(1)
        app.root.deiconify()
        app.main_page()

"""
Class defining the launcher itself : GUI and the interaction between this GUI and the BackEnd
"""
class Launcher:
    def __init__(self): #Initialize launcher window, assets, state, and widgets
        
        self.root = customtkinter.CTk()
        self.root.geometry("1000x550")
        self.root.title("InfoCraft Launcher")
        self.root.resizable(False, False)
        self.root.iconbitmap("assets/icon.ico")
        self.root.configure(fg_color="#1C1C1C")
        

        self.bg_img = PhotoImage(file="assets/background.png")
        self.bg = Label(self.root, image=self.bg_img)      

        self.play = Image.open("assets/play.png")
        self.creeper = Image.open("assets/off_login_logo.png")
        self.block = Image.open("assets/block_logo.png")
        self.settings_icon = Image.open("assets/settings.png")
        
        self.username = None
        
        self.setup_widgets()
        
    def setup_widgets(self): #Filling widgets proprieties
        self.play_button = customtkinter.CTkButton(self.root, command=self.start_game,
                                                    fg_color="#36007A",
                                                    bg_color="#1C1C1C",
                                                    hover_color="#2A005C",
                                                    text="JOUER ",
                                                    width=200,
                                                    height=50,
                                                    corner_radius=20,
                                                    image=customtkinter.CTkImage(self.play, size=(30, 30)),
                                                    compound="right",
                                                    font=("Arial", 25, "bold"))
                                                    
        self.settings_button = customtkinter.CTkButton(self.root, command=self.settings_page,
                                                    fg_color="#36007A",
                                                    bg_color="#1C1C1C",
                                                    hover_color="#2A005C",
                                                    text="",
                                                    width=50,
                                                    height=50,
                                                    corner_radius=20,
                                                    image=customtkinter.CTkImage(self.settings_icon, size=(30, 30)))

        self.loading_bar = customtkinter.CTkProgressBar(self.root,
                                                            mode="indeterminate",
                                                            width=900,
                                                            height=20,
                                                            corner_radius=100,
                                                            fg_color="#474747",
                                                            bg_color="#1C1C1C",
                                                            progress_color="#36007A")
        
        self.loading_label = customtkinter.CTkLabel(self.root, 
                                                           text="Téléchargement des fichiers du jeu ...",
                                                           font=("Arial", 15, "bold"))

        self.back_button = customtkinter.CTkButton(self.root,
                                                        command=self.main_page,
                                                        fg_color="#972626",
                                                        bg_color="#1C1C1C",
                                                        hover_color="#751F1F",
                                                        text="ANNULER",
                                                        width=200,
                                                        height=50,
                                                        corner_radius=20,
                                                        font=("Arial", 25, "bold"))
        
        self.block = customtkinter.CTkImage(light_image=self.block,
                                        dark_image=self.block,
                                        size=(200, 200))
        self.block = customtkinter.CTkLabel(self.root, image=self.block, text="")


        self.connection_label = customtkinter.CTkLabel(self.root, 
                                                           text="Bienvenue !",
                                                           font=("Arial", 50, "bold"))
        
        self.creeper = customtkinter.CTkImage(light_image=self.creeper,
                                        dark_image=self.creeper,
                                        size=(200, 200))
        self.creeper = customtkinter.CTkLabel(self.root, image=self.creeper, text="")
        
        self.username_entry = customtkinter.CTkEntry(self.root,
                                                                height=50,
                                                                placeholder_text="*nom d'utilisateur",
                                                                placeholder_text_color="gray",
                                                                bg_color="#1C1C1C",
                                                                fg_color="white",
                                                                border_color="white",
                                                                text_color="black",
                                                                corner_radius=15,
                                                                width=500)
        
        self.off_login_button = customtkinter.CTkButton(self.root,
                                                            fg_color="#36007A",
                                                            bg_color="#1C1C1C",
                                                            hover_color="#2A005C",
                                                            command=self.off_login,
                                                            text="Se Connecter",
                                                            width=500,
                                                            height=50,
                                                            corner_radius=20)
                                                        
        self.settings_label_title = customtkinter.CTkLabel(self.root, 
                                                           text="Paramètres",
                                                           font=("Arial", 50, "bold"))
        
        self.ram_slider = customtkinter.CTkSlider(self.root, 
                                                  from_=1, to=self.get_system_ram()-1, 
                                                  number_of_steps=int(self.get_system_ram()-1), 
                                                  width=500,
                                                  command=self.update_ram_label,
                                                  button_color="#36007A",
                                                  button_hover_color="#2A005C",
                                                  progress_color="#36007A")
                                                  
        self.ram_value_label = customtkinter.CTkLabel(self.root, 
                                                      text="RAM Allouée: 2 GB",
                                                      font=("Arial", 25, "bold"))
                                                      
        self.save_settings_button = customtkinter.CTkButton(self.root,
                                                                command=self.save_settings,
                                                                fg_color="#36007A",
                                                                bg_color="#1C1C1C",
                                                                hover_color="#2A005C",
                                                                text="SAUVEGARDER",
                                                                width=200,
                                                                height=50,
                                                                corner_radius=20,
                                                                font=("Arial", 25, "bold"))
        
    def clear_ui(self): #Clearing the widgets in the window
        self.play_button.place_forget()
        self.settings_button.place_forget()
        self.loading_bar.place_forget()
        self.back_button.place_forget()
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
        self.settings_button.place(relx=0.05, rely=0.855)
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
        self.save_settings_button.place(relx=0.49, rely=0.855)

    def update_ram_label(self, value): #Update the ram text
        self.ram_value_label.configure(text=f"RAM Allouée: {int(float(value))} GB")
        
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
        
    def display(self): #Displaying the window on the offline login page
        self.off_login_page()
        self.root.mainloop()

    def verify_str(self, string_to_verify): #Verify if a string is valid for a profile name (not empty and only contains allowed characters)
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        if string_to_verify == "": return False
        for element in string_to_verify:
            if element not in allowed_chars:
                return False
        if string_to_verify == "none":
            return False

        return True
        
    def off_login(self): #Offline authentification
        self.username = self.username_entry.get()
        if len(self.username) < 1 or " " in self.username or not self.verify_str(self.username):
            messagebox.showerror("Error", "Invalid Username.")
        else:
            self.save_last_username()
            self.main_page()
            
    def set_username(self): #Set latest username in the entry
        saved_username = config['GUI']['last_used_nickname']
        if saved_username != "Steve":
            self.username_entry.insert(0, saved_username)
            
    def save_last_username(self): #Save the last used username
        try:
            config.set('GUI', 'last_used_nickname', self.username_entry.get())
            with open("config.ini", 'w') as configfile:
                config.write(configfile)
        except Exception as e:
            messagebox.showerror("Error", f"Unable to save username:\n{str(e)}")

    
    def start_game(self): #Start the game files download and launch
        self.loading_page()
        selected_profile = Profile("Default", "1.14.4")
        selected_profile.username = self.username
        selected_profile.ram = str(self.get_saved_ram())
        thread = threading.Thread(target=selected_profile.launch_sequence, daemon=True)
        thread.start()
        

"""
Entry Point
"""
if __name__ == "__main__":
    config = configparser.ConfigParser()
    if not os.path.exists("config.ini"):
        config['GUI'] = {
            'last_used_nickname': 'Steve',
            'ram_allocation': '2'
        }
        with open("config.ini", 'w') as configfile:
            config.write(configfile)
    else:
        config.read('config.ini')

    if not os.path.exists("instances"):
        os.mkdir("instances")
        os.mkdir("instances/Default")
    
    app = Launcher()
    app.display()


"""
Compilation Instructions:
CMD : pyinstaller --noconfirm --onefile --windowed --icon="assets/icon.ico" --add-data="assets;assets" --collect-all customtkinter main.py
"""