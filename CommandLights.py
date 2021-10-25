import lifxlan as lx
import phue
import time
import re

from threading import Thread

#########################################################
#                VocaLights Command module              #
#########################################################
# Leverages the following packages:                     #
# lifxlan - Developed by Meghan Clark                   #
#           * http://github.com/mclarkk/lifxlan         #
# phue - Developed by Nathanaël Lécaudé                 #
#           * https://github.com/studioimaginaire/phue  #
#########################################################
# IMPORTANT: In order to use the functions developed    #
#            above and below the proper smart lights    #
#            must be available and setup. Currently     #
#            supports LifX and Philips Hue smart lights.#
#                                                       #
# USAGE: The global variables below can be updated and  #
#        customized to ones liking. The program will    #
#        take voice input from the user and processes   #
#        each request. Lights can be specified by name. #
#        If the name of the light(s) are omitted then   #
#        the program will default to all lights listed. #
#########################################################

#########################################################################
#                              LIFX SETTINGS                            #
#########################################################################

# Default values for lights upon startup
LX_DEFAULT_COLOR = {"main light": "GOLD", "backlight": "GOLD"}
LX_DEFAULT_BRIGHTNESS = 32500

# Adjust these values to how bright/dim a light should get (divide by 650 to get percentage)
LX_MAX_BRIGHTNESS = 65000
LX_MIN_BRIGHTNESS = 16250

# Transition rates in milliseconds
LX_BRIGHTNESS_RATE = 3000  # Rate at which the brightness changes
LX_COLOR_RATE = 3000  # Rate at which the color changes

# Function rates in seconds
LX_FLASH_RATE = 3
LX_COLORAMA_RATE = 3
LX_DISCO_RATE = 0.1
LX_FLICKER_RATE = 0.03

# Color values according to lifxlan.Light module specifications
LX_COLORS = {"red": [65535, 65535, 65535, 3500], "orange": [6500, 65535, 65535, 3500],
             "yellow": [9000, 65535, 65535, 3500], "green": [16173, 65535, 65535, 3500],
             "cyan": [29814, 65535, 65535, 3500], "blue": [43634, 65535, 65535, 3500],
             "purple": [50486, 65535, 65535, 3500], "pink": [58275, 65535, 47142, 3500],
             "white": [58275, 0, 65535, 5500], "gold": [58275, 0, 65535, 2500]}

# Light connection specifications
LX_LIGHT_NAMES = ["main light", "backlight"]  # Add, remove, and rename light names based on how they're referred to
LX_LIGHT_MACAD = {"main light": "D0:12:34:56:78:90", "backlight": "D0:98:76:54:32:10"}  # MAC address for each light
LX_LIGHT_IPADD = {"main light": "xxx.xxx.x.xxx", "backlight": "xxx.xxx.x.xxx"}  # IP address for each light

# Default setting of LifX lights
LX_LIGHT_BRIGHTNESS = {"main light": LX_MAX_BRIGHTNESS, "backlight": LX_MAX_BRIGHTNESS}  # Default brightness level
LX_LIGHT_BRIGHTRATE = {"main light": LX_BRIGHTNESS_RATE, "backlight": LX_BRIGHTNESS_RATE}  # Default brightness rate
LX_LIGHT_COLORRATE = {"main light": LX_COLOR_RATE, "backlight": LX_COLOR_RATE}  # Default brightness rate of lights

# Light commands along with their respective methods and arguments
LX_COMMANDS = {
    "turn on": {"set_power": "on"},  # Turn power on
    "turn off": {"set_power": "off"},  # Turn power off
    "change color": {"set_color": LX_COLORS},  # Change color of bulb
    "dim": {"set_brightness": "dynaInt" + str(LX_MIN_BRIGHTNESS), "rate": LX_BRIGHTNESS_RATE},  # Lower the brightness
    "raise": {"set_brightness": "dynaInt" + str(LX_MAX_BRIGHTNESS), "rate": LX_BRIGHTNESS_RATE},  # Raise brightness
    "colorama on": {"set_color": [True, "colorama", LX_COLORAMA_RATE, LX_COLORS, LX_COLOR_RATE]},  # Casual color array
    "colorama off": {"set_color": [False, "colorama"]},
    "disco on": {"set_color": [True, "disco", LX_DISCO_RATE, LX_COLORS, LX_DISCO_RATE]},  # Intense color array
    "disco off": {"set_color": [False, "disco"]},
    "flash on": {"set_brightness": [True, "flash", LX_FLASH_RATE, {"in": LX_MAX_BRIGHTNESS, "out": LX_MIN_BRIGHTNESS}, LX_BRIGHTNESS_RATE]},
    "flash off": {"set_brightness": [False, "flash"]},
    "flicker on": {"set_power": [True, "flicker", LX_FLICKER_RATE, {"on": "on", "off": "off"}, 0]},
    "flicker off": {"set_power": [False, "flicker"]},
    }

#########################################################################
#                          PHILIPS HUE SETTINGS                         #
#########################################################################

PHUE_DEFAULT_COLOR = {"table light": [0.4, 0.35], "bath light": [0.4, 0.35]}
PHUE_DEFAULT_BRIGHTNESS = 254  # Default color for LifX bulbs

PHUE_MAX_BRIGHTNESS = 254  # Adjust these values to how bright a light should get (divide by 2.54 to get percentage)
PHUE_MIN_BRIGHTNESS = 5  # Adjust this to how dim a light should get

PHUE_BRIDGE_IPADD = "xxx.xxx.x.xxx"  # IP address of the bridge
PHUE_LIGHT_NAMES = ["table light", "bath light"]
PHUE_LIGHT_IDS = {"table light": 1, "bath light": 2}  # ID's for each lights

PHUE_COLORS = {"red": [1, 0], "orange": [0.55, 0.4], "yellow": [0.45, 0.47],
               "green": [0, 1], "cyan": [0.196, 0.252], "blue": [0, 0],
               "purple": [0.285, 0.202], "pink": [0.36, 0.23],
               "white": [0.31, 0.316], "gold": [0.4, 0.35]}

PHUE_FLASH_RATE = 1
PHUE_COLORAMA_RATE = 3
PHUE_DISCO_RATE = 0.1
PHUE_FLICKER_RATE = 0.03

PHUE_COMMANDS = {
    "turn on": "on",  # Turn power on
    "turn off": "on",  # Turn power off
    "change color": "xy",  # Change color of bulb
    "dim": "bri",  # Lower the light brightness
    "raise": "bri",  # Raise the light brightness
    "colorama on": "xy",  # Casual array of colors
    "colorama off": "xy",
    "disco on": "xy",  # Intense array of colors
    "disco off": "xy",
    "flicker on": "on",  # Malfunctioning paradigm
    "flicker off": "off",
    "flash on": "bri",  # Smooth signal
    "flash off": "bri",
    }

PHUE_KEYWORDS = {
    "change color": PHUE_COLORS,
    "turn on": True,
    "colorama on": [True, "colorama", PHUE_COLORAMA_RATE, PHUE_COLORS],
    "disco on": [True, "disco", PHUE_DISCO_RATE, PHUE_COLORS],
    "flicker on": [True, "flicker", PHUE_FLICKER_RATE, {"on": True, "off": False}],
    "flash on": [True, "flash", PHUE_FLASH_RATE, {"in": PHUE_MAX_BRIGHTNESS, "out": PHUE_MIN_BRIGHTNESS}],
    "turn off": False,
    "colorama off": [False, "colorama"],
    "disco off": [False, "disco"],
    "flicker off": [False, "flicker"],
    "flash off": [False, "flash"],
    "dim": "dynaInt" + str(PHUE_MIN_BRIGHTNESS),
    "raise": "dynaInt" + str(PHUE_MAX_BRIGHTNESS),
}


class LightAPI:
    def __init__(self, light_objects):
        self.light_names = {}
        self.light_objects = light_objects
        for obj in self.light_objects:
            self.light_names[obj] = obj.get_light_names()

    def run_commands(self, words):
        words = words.lower()  # Consistency across commands
        requested_lights = []
        # Look for any light mentioned by name
        for obj in self.light_objects:
            for name in self.light_names[obj]:
                if name in words:
                    requested_lights.append(obj)

        if len(requested_lights) == 0:  # If not light specified, default to all lights
            requested_lights = self.light_objects

        responses = []
        for obj in requested_lights:
            response = obj.process_command(words)
            responses.append(response)

        return responses


class LifX:
    def __init__(self):
        self.lights = {}  # Stores lx.Light objects
        self.lightThreads = {}  # For purposes of multi-threading functions
        self.threadVars = {}  # Dynamic True/False values to trigger threaded function
        for name in LX_LIGHT_NAMES:
            self.lights[name] = lx.Light(LX_LIGHT_MACAD[name], LX_LIGHT_IPADD[name])  # Set the Light objects
            self.lights[name].set_color(getattr(lx, LX_DEFAULT_COLOR[name]))  # Set the default color
            self.lights[name].set_brightness(LX_DEFAULT_BRIGHTNESS)  # Set the default brightness

    def process_command(self, words):
        args = []
        light_name = None
        for name in LX_LIGHT_NAMES:
            if name in words:
                light_name = name
                break
        
        # If no light name was specified, default to all lights
        if light_name:
            lx_names = [light_name]
        else:
            lx_names = LX_LIGHT_NAMES

        args.append(lx_names)

        try:
            # Go through each command and see if it matches the spoken words
            for cmd, value in LX_COMMANDS.items():
                if cmd in words:
                    for method, specs in value.items():
                        args.append(method)
                        if isinstance(specs, dict):  # Specific to color adjustment
                            for spec in words.split():
                                if spec in specs.keys():
                                    args.append([specs[spec]])
                                    break
                        elif isinstance(specs, list):  # Specific to continuous functions
                            for name in lx_names:  # If no light name specified default to all
                                if specs[0]:
                                    self.threadVars[specs[1]] = True
                                    self.lightThreads[name] = Thread(target=getattr(self, specs[1]),
                                                                     args=(args, LX_COMMANDS[cmd]), daemon=True)
                                    self.lightThreads[name].start()
                                else:
                                    self.threadVars[specs[1]] = False
                        elif "dynaInt" in specs:  # Specific to brightness adjustment
                            try:
                                args.append([int(int(re.findall(r'\d+', words)[-1]) * 650), value["rate"]])
                            except IndexError:  # Without specifying percent, dynamically dim or raise the lights
                                args.append([int(re.findall(r'\d+', specs)[-1]), value["rate"]])
                        else:
                            args.append([specs])  # Power on/off

                        if len(args) >= 3:
                            self.execute_command(args)

                    return cmd

            return "Voice command '" + str(words) + "' does not exist."
        except Exception as Ex:
            return "Error: " + str(Ex)

    def execute_command(self, args):
        for name in args[0]:
            getattr(self.lights[name], args[1])(*args[2])

    def colorama(self, args, elements):
        self.run_thread(args, elements)

    def disco(self, args, elements):
        self.run_thread(args, elements)

    def flash(self, args, elements):
        self.run_thread(args, elements)

    def flicker(self, args, elements):
        self.run_thread(args, elements)

    def run_thread(self, args, elements):
        while self.threadVars[elements[args[1]][1]]:
            for key, val in elements[args[1]][3].items():
                self.execute_command(args + [[val] + [elements[args[1]][4]]])
                time.sleep(elements[args[1]][2])
                if not self.threadVars[elements[args[1]][1]]:
                    break

    @staticmethod
    def get_light_names():
        return LX_LIGHT_NAMES


class PhilipsHue:
    def __init__(self):
        self.bridge = phue.Bridge(PHUE_BRIDGE_IPADD)
        self.lights = {}
        self.lightThreads = {}
        self.threadVars = {}
        # Set the defaults
        for name, lid in PHUE_LIGHT_IDS.items():
            isOn = self.bridge.get_light(lid)["state"]["on"]
            if not isOn:
                self.bridge.set_light(lid, "on", True)  # Can only alter when on
                self.bridge.set_light(lid, "xy", PHUE_DEFAULT_COLOR[name])
                self.bridge.set_light(lid, "on", False)
            else:
                self.bridge.set_light(lid, "xy", PHUE_DEFAULT_COLOR[name])
                self.bridge.set_light(lid, "bri", PHUE_DEFAULT_BRIGHTNESS)

    def process_command(self, words):
        args = []
        light_id = None
        for name in PHUE_LIGHT_NAMES:
            if name in words:
                light_id = PHUE_LIGHT_IDS[name]
                break

        if light_id:
            ids = [light_id]
        else:   # If no light name was specified, default to all lights
            ids = list(PHUE_LIGHT_IDS.values())

        args.append(ids)

        try:
            # Go through each command and see if it matches the spoken words
            for cmd, value in PHUE_COMMANDS.items():
                if cmd in words:
                    args.append(value)
                    if isinstance(PHUE_KEYWORDS[cmd], dict):  # For color related functions
                        for spec in words.split():
                            if spec in PHUE_KEYWORDS[cmd].keys():
                                args.append(PHUE_KEYWORDS[cmd][spec])
                                break
                    elif isinstance(PHUE_KEYWORDS[cmd], list):  # For looped functions
                        for lid in ids:  # If no light name specified default to all
                            if PHUE_KEYWORDS[cmd][0]:
                                self.threadVars[PHUE_KEYWORDS[cmd][1]] = True
                                self.lightThreads[lid] = Thread(target=getattr(self, PHUE_KEYWORDS[cmd][1]),
                                                                args=(args, PHUE_KEYWORDS[cmd]), daemon=True)
                                self.lightThreads[lid].start()
                            else:
                                self.threadVars[PHUE_KEYWORDS[cmd][1]] = False
                    elif "dynaInt" in str(PHUE_KEYWORDS[cmd]):  # For brightness adjustment
                        try:
                            args.append(int(int(re.findall(r'\d+', words)[-1]) * 2.54))
                        except IndexError:  # Without specifying percent, dynamically dim or raise the lights
                            args.append(int(re.findall(r'\d+', PHUE_KEYWORDS[cmd])[-1]))
                    else:
                        args.append(PHUE_KEYWORDS[cmd])  # For main switch

                    if len(args) >= 3:
                        self.execute_command(args)
                    return cmd

            return "Voice command '" + str(words) + "' does not exist."
        except Exception as Ex:
            return "PHUE ERROR: " + str(Ex)

    def execute_command(self, args):
        return self.bridge.set_light(*args)

    def colorama(self, args, elements):
        self.run_thread(args, elements)

    def disco(self, args, elements):
        self.run_thread(args, elements)

    def flash(self, args, elements):
        self.run_thread(args, elements)

    def flicker(self, args, elements):
        self.run_thread(args, elements)

    def run_thread(self, args, elements):
        while self.threadVars[elements[1]]:
            for key, val in elements[3].items():
                result = self.execute_command(args + [val])
                for i, light in enumerate(args[0]):  # Unique for phue, check statuses to make sure error is captured
                    result_status = list(result[i][0].keys())[0]
                    if result_status == "error":  # Exit thread for the light(s) that are non-responsive to requests
                        print(f"Light {i+1} error: " + str(result[i][0][result_status]["description"]))
                        return
                time.sleep(elements[2])
                if not self.threadVars[elements[1]]:
                    break

    @staticmethod
    def get_light_names():
        return PHUE_LIGHT_NAMES
