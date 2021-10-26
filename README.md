# Overview
VocaLights is the in-house program that takes voice input and registers commands to adjust lighting in various ways. <strong>Requires smart light bulbs in order to function as intended.</strong><br>

***Tested and validated with LifX and Philips Hue model light bulbs.***

# Usage
You may choose to run the main script in the background and go on through the day. So long as a microphone is within distance, simply speak the desired command and the lights will turn on and off, dim and brighten, change colors, and set the mood for the space of your choice.<br></br>
<strong><u>Main Commands</u>: \[Brackets = Required] (Parens = Optional)</strong> 
* Turn off/on (light name or all "lights")
* Dim (light name or all "lights") (to # percent)
* Raise (light name or all "lights) (to # percent)
* Change color (of light name or "lights") to \[RED,ORANGE,YELLOW,GREEN,CYAN,BLUE,PURPLE,PINK,WHITE,GOLD]

To stop the program from running, speak "exit voice" and the program will end.

# Setup and Configuration
The application can be configured and used in 3 steps.<br>

First, import the package and initialize the Activation object. The pause_activation parameter is how long in seconds the program will pause for before registering what was spoken.
```python
import VocaLights

voice = VocaLights.Activation(pause_activation=0.5)
```

Then configure each set of lights by using the configure_lights method.<br>

Minimalist example for one bulb:
```python
voice.configure_lights(VocaLights.LX_BRAND, ip_addresses="192.xxx.x.xxx")
```

Full example for multiple lights:
```python
voice.configure_lights(VocaLights.LX_BRAND, 
                       ip_addresses=("192.xxx.x.xxx", "192.yyy.y.yyy"), 
                       light_names=("main light", "desk light"),
                       mac_addresses=("D0:12:34:56:78:90", "D0:98:76:54:32:10"),  # LifX require mac addresses as well
                       default_colors=("gold", "blue"), 
                       default_brightness=(65000, 37500), 
                       max_brightness=(65500, 45000), 
                       min_brightness=(12500, 10000),
                       brightness_rate=(3000, 3500), 
                       color_rate=(3200, 2500), 
                       flash_rate=(1, 1.2), 
                       colorama_rate=(3, 3),
                       disco_rate=(0.1, 0.2), 
                       flicker_rate=(0.01, 0.05))
 
 voice.configure_lights(VocaLights.PHUE_BRAND, 
                       ip_addresses="192.xxx.x.xxx",  # PhilipsHue uses a bridge which groups together lights
                       light_names=("table light", "bathroom light"),
                       light_ids=(1, 2),  # These bulbs come with unique ids beginning with 1
                       default_colors=("gold", "blue"), 
                       default_brightness=(254, 200),  
                       max_brightness=(254, 254),  # PhilipsHue has a range that goes up to 254
                       min_brightness=(100, 75),
                       flash_rate=(1, 1), 
                       colorama_rate=(3, 4),
                       disco_rate=(0.1, 0.2), 
                       flicker_rate=(0.01, 0.05))
```

Finally, call the run() method and speak a command. The voice_response parameter can be set to True to activate the voice assistant that will take input from the request sent and returned from the LightAPI object and convey it back in the computers voice.
```python
voice.run()  # Standard process
# voice.run(voice_response=True)  # Enable voice assistant to convey completed requests 
```
