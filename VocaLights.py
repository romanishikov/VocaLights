import VoiceCommands as VC  # Module for retrieving voice input and giving output
import lifxlan as lx
import phue
import time
import sys
import re

from threading import Thread

LIFX_BRAND = "lifx"
PHUE_BRAND = "phue"

PARAMS = {
    LIFX_BRAND: ["light_names", "mac_addresses", "ip_addresses", "default_colors", "default_brightness",
                 "max_brightness", "min_brightness", "brightness_rate", "color_rate", "flash_rate",
                 "colorama_rate", "disco_rate", "flicker_rate"],
    PHUE_BRAND: ["light_names", "light_ids", "ip_addresses", "default_colors", "default_brightness",
                 "max_brightness", "min_brightness", "flash_rate",
                 "colorama_rate", "disco_rate", "flicker_rate"]
    }

DEFAULTS = {
    LIFX_BRAND: {
        "light_names": "light 1",
        "default_colors": "GOLD",
        "default_brightness": 32500,
        "max_brightness": 65000,
        "min_brightness": 32500,
        "brightness_rate": 3000,
        "color_rate": 3000,
        "flash_rate": 3,
        "colorama_rate": 3,
        "disco_rate": 0.1,
        "flicker_rate": 0.03,
        },
    PHUE_BRAND: {
        "light_names": "light 1",
        "light_ids": [1],
        "default_colors": "GOLD",
        "default_brightness": 254,
        "max_brightness": 254,
        "min_brightness": 5,
        "flash_rate": 1,
        "colorama_rate": 3,
        "disco_rate": 0.1,
        "flicker_rate": 0.03,
        }
    }

SPEECH_RESPONSES = {
    "turn on": "turning on",
    "turn off": "turning off",
    "change color": "changing color",
    "dim": "dimming",
    "raise": "raising",
    "colorama on": "turning colorama on",
    "colorama off": "turning colorama off",
    "disco on": "activating disco",
    "disco off": "stopping disco",
    "flicker on": "activating flicker",
    "flicker off": "stopping flicker",
    "flash on": "activating flash",
    "flash off": "stopping flash",
    }


class Lights(object):

    """
    A configuration class that logs light objects and stores them for later use.
    Required to pass the brand parameter which corresponds to the type of light (e.g. lifx, phue).
    All other parameters with the exceptions of ip_addresses and/or mac_addresses (see below)
    will be given default values as outlined in the global variables above. The user can specify
    any parameter values they like as long as they are the appropriate datatype.

    The parameters are as follows:

    - ip_addresses: Corresponds to the ip address associated with a
                    a) light bulb (LifX) and/or
                    b) bridge (PhilipsHue)
                    At minimum an IP address is required to set up the current brands (lifx also requires mac address).
        * Subtype String. Must be either a list/tuple or single string (e.g. '198.221.1.111')

    - light_names: The name(s) of the light(s) the user will refer to (e.g. 'bathroom light').
        * Subtype String .Must be either a list/tuple or single string (comma separation is not registered)

    - light_ids: Unique to PhilipsHue. This refers to the ID number of the light when it was setup (e.g. 1, 2, 3, etc.)
        * Subtype Integer. Must be a small integer or a list/tuple of small integer(s)

    - mac_addresses: Unique to LifX. To connect to a light bulb both mac address and ip address must be specified.
        * Subtype String. Must be either a list/tuple or single string (e.g. 'D0:12:34:56:78:90')

    - default_color: Specifies the color of the light when the program is first run.
                     Colors available are: red, orange, yellow, blue, green, cyan, purple, pink, white, and gold.
                     This parameter is not case sensitive as all values are converted to lowercase upon config.
        * Subtype String. Must be either a list/tuple or single string (one value default all lights to that color)

    - default_brightness: Specifies how bright a light will be on runtime.
                          Lifx uses a different range than PhilipsHue. Max brightness for LifX is 65535
                          while max brightness for PhilipsHue is 254. 0 is the lowest for both.
        * Subtype Integer. Must be either a list/tuple or single integer

    - max_brightness: Specifies the upper brightness range when executing commands such as 'raise lights' or 'flash'.
        * Subtype Integer. Must be either a list/tuple or single integer

    - min_brightness: Specified the lower brightness range when executing commands such as 'dim lights' or 'flash'
        * Subtype Integer. Must be either a list/tuple or single integer

    - brightness_rate: Unique for LifX. Specifies how fast a light is raised or dim (in ms).
        * Subtype Integer. Must be either a list/tuple or single integer

    - color_rate: Unique for LifX. Specifies how fast a light's color will change (in ms).
        * Subtype Integer. Must be either a list/tuple or single integer

    - flash_rate: Specifies the speed that the light(s) will flash in and out (in s, specific to the flash command)
        * Subtype Integer. Must be either a list/tuple or single integer

    - colorama_rate: Specifies the speed that the light(s) smoothly transition into new colors (in s).
        * Subtype Integer. Must be either a list/tuple or single integer

    - disco_rate: Similar to colorama except without smooth transition and at a faster rate (in s).
        * Subtype Integer. Must be either a list/tuple or single integer (decimal)

    - flicker_rate: Similar to flash except without smooth transition and at a faster rate (in s).
        * Subtype Integer. Must be either a list/tuple or single integer (decimal)
    """

    def __init__(self):
        self.light_objects = []

    def configure_lights(self, brand, ip_addresses, light_names=None, light_ids=None, mac_addresses=None,
                         default_colors=None, default_brightness=None, max_brightness=None, min_brightness=None,
                         brightness_rate=None, color_rate=None, flash_rate=None, colorama_rate=None,
                         disco_rate=None, flicker_rate=None):

        if len([light_names]) != len([ip_addresses]):
            print("WARNING: Number of lights and addresses do not match which may affect processing speed of requests.")

        settings = {
            "ip_addresses": ip_addresses,
            "light_names": light_names,
            "light_ids": light_ids,
            "mac_addresses": mac_addresses,
            "default_colors": default_colors,
            "default_brightness": default_brightness,
            "max_brightness": max_brightness,
            "min_brightness": min_brightness,
            "brightness_rate": brightness_rate,
            "color_rate": color_rate,
            "flash_rate": flash_rate,
            "colorama_rate": colorama_rate,
            "disco_rate": disco_rate,
            "flicker_rate": flicker_rate
        }

        for key in list(settings.keys()):
            if key not in PARAMS[brand]:
                del settings[key]
                continue
            if None in [settings[key]]:  # Get the default setting if none specified
                settings[key] = DEFAULTS[brand][key]
            if not isinstance(settings[key], (tuple, list)):  # Convert
                settings[key] = [settings[key]]
            if len(settings[key]) != len(settings["light_names"]):
                settings[key] = settings[key] * len(settings["light_names"])

        params = list(settings.values())

        if brand == "lifx":
            try:
                if None in settings["mac_addresses"]:
                    raise Exception("Insufficient parameters passed for 'mac_addresses'. "
                                    "Make sure MAC addresses are included for all lights.")

                lifx = self.LifX(*params)
                self.light_objects.append(lifx)
            except Exception as Ex:
                print("Connection to LifX could not be established: " + str(Ex))
        if brand == "phue":
            try:
                if None in settings["light_ids"]:
                    raise Exception("Insufficient parameters passed for 'light_ids'. "
                                    "Make sure each light has it's associated id assigned.")

                philips = self.PhilipsHue(*params)
                self.light_objects.append(philips)
            except Exception as Ex:
                print("Connection to phue could not be established: " + str(Ex))

    class LightAPI:

        """
        Works with all the Light subclasses in order to execute them
        at once based on the command passed.

        The class takes in the subclasses (e.g. LifX, PhilipsHue) configured
        by the user and stores them in a dictionary where they can be run
        together once all other requests have been completed.
        """

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

        def __init__(self, ip_addresses, light_names, mac_addresses, default_colors, default_brightness,
                     max_brightness, min_brightness, brightness_rate, color_rate,
                     flash_rate, colorama_rate, disco_rate, flicker_rate):

            self.LX_LIGHT_NAMES = light_names

            # Color values according to lifxlan.Light module specifications
            self.LX_COLORS = {"red": [65535, 65535, 65535, 3500], "orange": [6500, 65535, 65535, 3500],
                              "yellow": [9000, 65535, 65535, 3500], "green": [16173, 65535, 65535, 3500],
                              "cyan": [29814, 65535, 65535, 3500], "blue": [43634, 65535, 65535, 3500],
                              "purple": [50486, 65535, 65535, 3500], "pink": [58275, 65535, 47142, 3500],
                              "white": [58275, 0, 65535, 5500], "gold": [58275, 0, 65535, 2500]}

            # Light commands along with their respective methods and arguments
            self.LX_COMMANDS = {
                "turn on": {"set_power": "on"},  # Turn power on
                "turn off": {"set_power": "off"},  # Turn power off
                "change color": {"set_color": self.LX_COLORS},  # Change color of bulb
                "dim": {"set_brightness": "dynaInt" + str(min_brightness[0]), "rate": brightness_rate[0]},
                # Lower the brightness
                "raise": {"set_brightness": "dynaInt" + str(max_brightness[0]), "rate": brightness_rate[0]},
                # Raise brightness
                "colorama on": {"set_color": [True, "colorama", colorama_rate[0], self.LX_COLORS, color_rate[0]]},
                # Casual color
                "colorama off": {"set_color": [False, "colorama"]},
                "disco on": {"set_color": [True, "disco", disco_rate[0], self.LX_COLORS, disco_rate[0]]},
                # Intense color array
                "disco off": {"set_color": [False, "disco"]},
                "flash on": {"set_brightness": [True, "flash", flash_rate[0],
                                                {"in": max_brightness[0], "out": min_brightness[0]},
                                                brightness_rate[0]]},
                "flash off": {"set_brightness": [False, "flash"]},
                "flicker on": {"set_power": [True, "flicker", flicker_rate[0], {"on": "on", "off": "off"}, 0]},
                "flicker off": {"set_power": [False, "flicker"]},
            }

            self.lights = {}  # Stores lx.Light objects
            self.lightThreads = {}  # For purposes of multi-threading functions
            self.threadVars = {}  # Dynamic True/False values to trigger threaded function

            for i, name in enumerate(light_names):
                self.lights[name] = lx.Light(mac_addresses[i], ip_addresses[i])  # Set the Light objects
                self.lights[name].set_color(getattr(lx, default_colors[i]))  # Set the default color
                self.lights[name].set_brightness(default_brightness[i])  # Set the default brightness

        def process_command(self, words):
            args = []
            light_name = None
            for name in self.LX_LIGHT_NAMES:
                if name in words:
                    light_name = name
                    break

            # If no light name was specified, default to all lights
            if light_name:
                lx_names = [light_name]
            else:
                lx_names = self.LX_LIGHT_NAMES

            args.append(lx_names)

            try:
                # Go through each command and see if it matches the spoken words
                for cmd, value in self.LX_COMMANDS.items():
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
                                                                         args=(args, self.LX_COMMANDS[cmd]),
                                                                         daemon=True)
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

                        return {"SUCCESS": {cmd: lx_names}}

                return {"INFO": "Voice command '" + str(words) + "' does not exist."}
            except Exception as Ex:
                return {"ERROR": str(Ex)}

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

        def get_light_names(self):
            return self.LX_LIGHT_NAMES

    class PhilipsHue:
        def __init__(self, ip_addresses, light_names, light_ids, default_colors,
                     default_brightness, max_brightness, min_brightness,
                     flash_rate, colorama_rate, disco_rate, flicker_rate):

            self.PHUE_LIGHT_NAMES = light_names
            self.PHUE_LIGHT_IDS = {}

            self.bridge = phue.Bridge(ip_addresses[0])
            self.lights = {}
            self.lightThreads = {}
            self.threadVars = {}

            self.PHUE_COLORS = {"red": [1, 0], "orange": [0.55, 0.4], "yellow": [0.45, 0.47],
                                "green": [0, 1], "cyan": [0.196, 0.252], "blue": [0, 0],
                                "purple": [0.285, 0.202], "pink": [0.36, 0.23],
                                "white": [0.31, 0.316], "gold": [0.4, 0.35]}

            self.PHUE_COMMANDS = {
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

            self.PHUE_KEYWORDS = {
                "change color": self.PHUE_COLORS,
                "turn on": True,
                "colorama on": [True, "colorama", colorama_rate[0], self.PHUE_COLORS],
                "disco on": [True, "disco", disco_rate[0], self.PHUE_COLORS],
                "flicker on": [True, "flicker", flicker_rate[0], {"on": True, "off": False}],
                "flash on": [True, "flash", flash_rate[0], {"in": max_brightness[0], "out": min_brightness[0]}],
                "turn off": False,
                "colorama off": [False, "colorama"],
                "disco off": [False, "disco"],
                "flicker off": [False, "flicker"],
                "flash off": [False, "flash"],
                "dim": "dynaInt" + str(min_brightness[0]),
                "raise": "dynaInt" + str(max_brightness[0]),
            }

            # Set the defaults
            for i, name in enumerate(light_names):
                self.PHUE_LIGHT_IDS[name] = light_ids[i]
                isOn = self.bridge.get_light(light_ids[i])["state"]["on"]
                if not isOn:
                    self.bridge.set_light(light_ids[i], "on", True)  # Can only alter when on
                    self.bridge.set_light(light_ids[i], "xy", self.PHUE_COLORS[default_colors[i].lower()])
                    self.bridge.set_light(light_ids[i], "on", False)
                else:
                    self.bridge.set_light(light_ids[i], "xy", self.PHUE_COLORS[default_colors[i].lower()])
                    self.bridge.set_light(light_ids[i], "bri", default_brightness[i])

        def process_command(self, words):
            args = []
            light_id = None
            for name in self.PHUE_LIGHT_NAMES:
                if name in words:
                    light_id = self.PHUE_LIGHT_IDS[name]
                    break

            if light_id:
                ids = [light_id]
            else:  # If no light name was specified, default to all lights
                ids = list(self.PHUE_LIGHT_IDS.values())

            args.append(ids)

            try:
                # Go through each command and see if it matches the spoken words
                for cmd, value in self.PHUE_COMMANDS.items():
                    if cmd in words:
                        args.append(value)
                        if isinstance(self.PHUE_KEYWORDS[cmd], dict):  # For color related functions
                            for spec in words.split():
                                if spec in self.PHUE_KEYWORDS[cmd].keys():
                                    args.append(self.PHUE_KEYWORDS[cmd][spec])
                                    break
                        elif isinstance(self.PHUE_KEYWORDS[cmd], list):  # For looped functions
                            for lid in ids:  # If no light name specified default to all
                                if self.PHUE_KEYWORDS[cmd][0]:
                                    self.threadVars[self.PHUE_KEYWORDS[cmd][1]] = True
                                    self.lightThreads[lid] = Thread(target=getattr(self, self.PHUE_KEYWORDS[cmd][1]),
                                                                    args=(args, self.PHUE_KEYWORDS[cmd]), daemon=True)
                                    self.lightThreads[lid].start()
                                else:
                                    self.threadVars[self.PHUE_KEYWORDS[cmd][1]] = False
                        elif "dynaInt" in str(self.PHUE_KEYWORDS[cmd]):  # For brightness adjustment
                            try:
                                args.append(int(int(re.findall(r'\d+', words)[-1]) * 2.54))
                            except IndexError:  # Without specifying percent, dynamically dim or raise the lights
                                args.append(int(re.findall(r'\d+', self.PHUE_KEYWORDS[cmd])[-1]))
                        else:
                            args.append(self.PHUE_KEYWORDS[cmd])  # For main switch

                        if len(args) >= 3:
                            self.execute_command(args)

                        return {"SUCCESS": {cmd: ids}}

                return {"INFO": "Voice command '" + str(words) + "' does not exist."}
            except Exception as Ex:
                return {"ERROR": str(Ex)}

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
                    for i, light in enumerate(args[0]):  # Unique for phue, check status to make sure error is captured
                        result_status = list(result[i][0].keys())[0]
                        if result_status == "error":  # Exit thread for the light(s) that are non-responsive to requests
                            print(f"Light {i + 1} error: " + str(result[i][0][result_status]["description"]))
                            return
                    time.sleep(elements[2])
                    if not self.threadVars[elements[1]]:
                        break

        def get_light_names(self):
            return self.PHUE_LIGHT_NAMES


class Activation(Lights):

    """
    Using the Lights object and its subclasses we initialize our program and
    set up speech recognition and speech response.

    Before running the main function, ensure all light objects have been configured
    using the configure_lights method inherited from the Lights object. When setup is complete
    then the run() function below can be used. The voice_response parameter can be set to True
    in order to receive a response back from the machine on the status of a completed request.
    """

    def __init__(self, pause_threshold=0.5):
        super().__init__()
        self.vIn = VC.CommandInputs(pause_threshold)
        self.vOut = VC.CommandOutputs()

    def run(self, voice_response=False):
        if len(self.light_objects) == 0:
            raise Exception("ERROR: No lights have been configured for usage. To set up lights "
                            "use configure_lights and pass it the type of light (e.g. lifx, phue), "
                            "the light names, and any additional customizable parameters listed. ")

        light_api = self.LightAPI(self.light_objects)
        while True:
            words = self.vIn.get_voice_input()

            if "exit voice" in words:
                sys.exit(0)
            elif words == "Audio not understood":
                continue

            response = light_api.run_commands(words)
            if voice_response:
                self._voice_response(response)

    def _voice_response(self, response):
        speech_responses = set()  # Get unique speech responses
        quantity = 0  # Count how many lights were affected
        for result in response:
            if list(result)[0] == "SUCCESS":
                command = list(result["SUCCESS"])[0]
                quantity += len(list(result["SUCCESS"].values())[0])  # Count successful light calls
                noun = "lights" if quantity > 1 else list(result["SUCCESS"].values())[0][0]  # Get light name
                speech_responses.add(SPEECH_RESPONSES[command] + " " + noun)
            elif list(result)[0] == "INFO":
                speech_responses.add(result["INFO"])

        for res in speech_responses:
            self.vOut.speak(res)
