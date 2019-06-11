#include "FastLED.h"

const int led_pin = 6;
const int num_pixels = 30;
byte mode = 0;

CRGB leds[num_pixels];

enum Alliance {
    Red,
    Blue,
};

class LEDPattern {
   public:
    virtual ~LEDPattern() {}
    virtual void periodic() = 0;
};

class Off : public LEDPattern {
   public:
    virtual void periodic(){};
};

class Stacking : public LEDPattern {
   private:
    int last = 0;

   public:
    virtual void periodic() {
        for (auto i = 0; i < num_pixels - last + 1; i++) {
            leds[i] = CRGB::Red;
            leds[i - 1] = CRGB::Black;
            FastLED.show();
            FastLED.delay(10);
        }
        last = (last + 1) % num_pixels;
    };
};

class IdleFader : public LEDPattern {
   private:
    CRGB color;
    int position = 0;
    bool forward = true;
    void fadeall() {
        for (int i = 0; i < num_pixels; i++) {
            leds[i].nscale8(240);
        }
    }

   public:
    IdleFader(Alliance alliance) {
        if (alliance == Alliance::Red) {
            color = CRGB::Red;
        } else {
            color = CRGB::Blue;
        }
    }
    virtual void periodic() {
        leds[position] = color;
        fadeall();
        FastLED.show();
        FastLED.delay(30);
        if (forward) {
            position++;
        } else {
            position--;
        }
        if (position == num_pixels || position == 0) {
            forward = !forward;
        }
    };
};

class Bounce1 : public LEDPattern {
   private:
    int step_size = 7;
    int step_delay = 50;

   public:
    virtual void periodic() {
        for (int c = 0; c < step_size; c++) {
            for (int i = 0; i < num_pixels - step_size; i += step_size) {
                leds[i + c] = CRGB::Red;
            }
            FastLED.show();
            FastLED.delay(step_delay);
            for (int i = 0; i < num_pixels - step_size; i += step_size) {
                leds[i + c] = CRGB::Black;
            }
        }
        for (int c = step_size; c > 0; c--) {
            for (int i = 0; i < num_pixels - step_size; i += step_size) {
                leds[i + c] = CRGB::Red;
            }
            FastLED.show();
            FastLED.delay(step_delay);
            for (int i = 0; i < num_pixels - step_size; i += step_size) {
                leds[i + c] = CRGB::Black;
            }
        }
    }
};

class Warning : public LEDPattern {
   private:
    bool dimming = true;
    int value = 255;

   public:
    virtual void periodic() {
        for (int i = 0; i < num_pixels; i++) {
            leds[i] = CHSV(HUE_RED, 255, value);
        }
        FastLED.show();

        if (value < 90) {
            dimming = false;
        }
        if (value == 255) {
            dimming = true;
        }
        if (dimming) {
            value -= 3;
        } else {
            value += 3;
        }
    };
};

class Chase : public LEDPattern {
   public:
    int step_size;
    int step_delay;
    Chase(int step_size = 3, int step_delay = 50)
        : step_size(step_size), step_delay(step_delay) {}
    virtual void periodic() {
        for (int c = 0; c < step_size; c++) {
            for (int i = 0; i < num_pixels; i += step_size) {
                leds[i + c] = CRGB::Red;
                leds[i + c + 1] = CRGB(255, 25, 0);
            }
            FastLED.show();
            FastLED.delay(step_delay);
            for (int i = 0; i < num_pixels; i += step_size) {
                leds[i + c] = CRGB::Black;
                leds[i + c + 1] = CRGB::Black;
            }
        }
    }
};

class Rainbow : public LEDPattern {
   private:
    uint16_t i = 0;
    uint16_t j = 0;

    CRGB Wheel(byte WheelPos) {
        WheelPos = 255 - WheelPos;
        if (WheelPos < 85) {
            return CRGB(255 - WheelPos * 3, 0, WheelPos * 3);
        }
        if (WheelPos < 170) {
            WheelPos -= 85;
            return CRGB(0, WheelPos * 3, 255 - WheelPos * 3);
        }
        WheelPos -= 170;
        return CRGB(WheelPos * 3, 255 - WheelPos * 3, 0);
    }

   public:
    virtual void periodic() {
        for (j = 0; j < 256 * 5; j++) {  // 5 cycles of all colors on wheel
            for (i = 0; i < num_pixels; i++) {
                leds[i] = Wheel(((i * 256 / num_pixels) + j) & 255);
            }
            FastLED.show();
            // delay(3);
        }
    };
};

class Rainbow2 : public LEDPattern {
   private:
    uint16_t i = 0;
    uint16_t j = 0;

    CRGB Wheel(byte WheelPos) {
        WheelPos = 255 - WheelPos;
        if (WheelPos < 85) {
            return CRGB(255 - WheelPos * 3, 0, WheelPos * 3);
        }
        if (WheelPos < 170) {
            WheelPos -= 85;
            return CRGB(0, WheelPos * 3, 255 - WheelPos * 3);
        }
        WheelPos -= 170;
        return CRGB(WheelPos * 3, 255 - WheelPos * 3, 0);
    }

   public:
    virtual void periodic() {
        for (j = 0; j < 256; j++) {
            for (i = 0; i < num_pixels; i++) {
                leds[i] = Wheel((i + j) & 255);
            }
            FastLED.show();
            FastLED.delay(2);
        }
    };
};

class Rainbow3 : public LEDPattern {
   private:
    uint8_t hue = 0;

   public:
    virtual void periodic() {
        for (int i = 0; i < num_pixels; i++) {
            leds[i] = CHSV(hue++, 255, 255);
        }
        FastLED.show();
        FastLED.delay(2);
    };
};

class Idle1 : public LEDPattern {
   private:
    int value = -128;

   public:
    virtual void periodic() {
        for (int i = 0; i < num_pixels; i++) {
            leds[i] =
                CRGB(i % 2 == 0 ? abs(value) : abs(128 - abs(value)), 0, 0);
        }
        value++;
        if (value == 128) {
            value = -128;
        }
        FastLED.show();
        FastLED.delay(10);
    };
};

Off off;
IdleFader redIdleFader(Alliance::Red);
IdleFader blueIdleFader(Alliance::Blue);
Stacking stacking;
Bounce1 bounce1;
Warning warning;
Chase lift(6, 70);
Rainbow rainbow1;
Rainbow2 rainbow2;
Idle1 idle1;

LEDPattern* pattern = &idle1;

void setup() {
    Serial.begin(9600);
    FastLED.addLeds<NEOPIXEL, led_pin>(leds, num_pixels);
    FastLED.setBrightness(16);
}

void loop() {
    if (Serial.available()) {
        mode = Serial.read();

        if (mode == 0) {
            pattern = &off;
        } else if (mode == 1) {
            pattern = &redIdleFader;
        } else if (mode == 2) {
            pattern = &blueIdleFader;
        } else if (mode == 3) {
            pattern = &stacking;
        } else if (mode == 4) {
            pattern = &warning;
        } else if (mode == 5) {
            pattern = &bounce1;
        } else if (mode == 6) {
            pattern = &lift;
        } else if (mode == 7) {
            pattern = &rainbow1;
        } else if (mode == 8) {
            pattern = &rainbow2;
        } else if (mode == 9) {
            pattern = &idle1;
        }
        for (int i = 0; i < num_pixels; i++) {
            leds[i] = CRGB::Black;
        }
        FastLED.show();
    }

    pattern->periodic();
}
