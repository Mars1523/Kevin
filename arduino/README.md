This folder contains the code for driving led strips, specifically NeoPixel strips.

The `main.ino` can be opened and deployed to an ardunio (UNO) with Arduino IDE and connected
to the RIO by USB.

`tester.py` allows for *nix computers to control the led pattern for testing

The robot code can choose the light pattern with an instance of the `LEDManager` class.

The Arduino program allows for several different LED patterns and listens on the usb serial port for packets sent by the robot code.
