import VoiceCommands as VC  # Module for retrieving voice input and giving output
import CommandLights as CL  # Module for using words to controls lights
import sys

ALL_BRANDS = ["lifx", "phue"]


class ActivateVoice:
    def __init__(self, pause_threshold=0.5):
        self.vIn = VC.CommandInputs(pause_threshold)
        self.vOut = VC.CommandOutputs()

    def run(self, brands=None, light_names=None):
        light_objects = []

        # If no brands were specified, default to using both
        if brands is None:
            brands = ALL_BRANDS
        if isinstance(light_names, list):
            light_names = " ".join(light_names)

        if "lifx" in brands:
            try:
                lifx = CL.LifX()  # Use this if using LifX smart lights
                light_objects.append(lifx)
            except Exception as Ex:
                print("Connection to LifX could not be established: " + str(Ex))
        if "phue" in list(brands):
            try:
                phue = CL.PhilipsHue()  # Use this if using Philips Hue smart lights
                light_objects.append(phue)
            except Exception as Ex:
                print("Connection to PhilipsHue could not be established: " + str(Ex))

        light_api = CL.LightAPI(light_objects)

        while True:
            words = self.vIn.get_voice_input()

            if "exit voice" in words:
                sys.exit(0)
            elif words == "Audio not understood":
                continue

            if light_names:
                words = f"{light_names} {words}"

            response = light_api.run_commands(words)
            if response:
                print(set(response))
