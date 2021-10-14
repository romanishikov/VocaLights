import VoiceCommands as vc  # Module for retrieving voice input and giving output
import CommandLights as CL  # Module for using words to controls lights
import sys


def main():
    light_objects = []
    vIn = vc.CommandInputs()
    vOut = vc.CommandOutputs()
    try:
        lifx = CL.LifX()  # Use this if using LifX smart lights
        light_objects.append(lifx)
    except Exception as Ex:
        print("Connection to LifX could not be established: " + str(Ex))
    try:
        phue = CL.PhilipsHue()  # Use this if using Philips Hue smart lights
        light_objects.append(phue)
    except Exception as Ex:
        print("Connection to PhilipsHue could not be established: " + str(Ex))

    light_api = CL.LightAPI(light_objects)

    while True:
        words = vIn.get_voice_input()
        if words == "Audio not understood":
            continue
        if "exit voice" in words:
            light_api.reset_lights()
            sys.exit(0)

        response = light_api.run_commands(words)
        if response:
            print(response)


if __name__ == "__main__":
    main()
