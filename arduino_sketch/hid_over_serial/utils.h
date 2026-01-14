#include "Arduino.h"
int proMicroLED_pin = 17;
int LED_PIN = LED_PIN;
const int PC_POWER_PIN = A0;

#define SPEAKER_PIN A3 // Define the pin where the speaker is connected

// int resetPin = 2;
int Xres = 1920;
int Yres = 1080;
unsigned char b0 = 0;
unsigned char b1 = 0;
int x = 0;
int y = 0;
char key = 0;
String pass = "";
bool using_pro_micro = true;

int delay_between = 500;
int  delay_between_var = 10;

int get_delay_between(){ 
  return random( max(delay_between-delay_between_var, 0) , delay_between+delay_between_var);  
}

void blink(int times, int delay_1 = 250,int delay_2 = 250, int beep = 0) {
  for (int n = 0; n < times; n++) {
    if (beep)
        tone(SPEAKER_PIN, beep); // You can change the frequency here
    digitalWrite(LED_PIN, LOW);
    delay(delay_1);
      if (beep)
          noTone(SPEAKER_PIN);
    digitalWrite(LED_PIN, HIGH);
    delay(delay_2);
  }
}

void press_key(int key) {
  delay(get_delay_between());
  Keyboard.press(key);
  delay(get_delay_between());
  Keyboard.release(key);
}

void press_key_only(int key) {
  Keyboard.press(key);
}
void release_key_only(int key) {
  Keyboard.release(key);
}

void move_click(int x, int y) {

  AbsMouse.move(x, y);
  delay(get_delay_between());
  AbsMouse.press(MOUSE_LEFT);
  delay(get_delay_between());
  AbsMouse.release(MOUSE_LEFT);
  char c = 99;
  Serial.write(99);
}

void move_click_2(int x, int y, bool right, bool click) {
  AbsMouse.move(x, y);
  //delay(delay_between);
  if (click)
    AbsMouse.press(right ? MOUSE_RIGHT : MOUSE_LEFT);
  else
    AbsMouse.release(right ? MOUSE_RIGHT : MOUSE_LEFT);
  
}

void move_click_right(int x, int y) {
  AbsMouse.move(x, y);
  delay(get_delay_between());
  AbsMouse.press(MOUSE_RIGHT);
  delay(get_delay_between());
  AbsMouse.release(MOUSE_RIGHT);
  char c = 99;
  Serial.write(99);
}

int serial_read_2bytes() {
  while (!Serial.available())
    ;
  b0 = Serial.read();
  b1 = Serial.read();
  Serial.write(b0);
  Serial.write(b1);
  int combined = b0 | b1 << 8;
  return combined;
}


void serial_send_2bytes(int combined) {
  // int combined = b0 | b1 << 8;

  Serial.write(b0);
  Serial.write(b1);
}
String serial_read_string(int y) {
  while (!Serial.available())
    ;
  String s;
  s = Serial.readString();
  Serial.println(s);

  return s;
}

void write_string2() {
  while (!Serial.available())
    ;
  String s;
  s = Serial.readString();
  Serial.println(s);
  x = serial_read_2bytes();
  y = serial_read_2bytes();
  delay(get_delay_between());

  AbsMouse.move(x, y);
  for (int t = 0; t < 2; t++) {
    AbsMouse.press(MOUSE_LEFT);
    AbsMouse.release(MOUSE_LEFT);
  }
  Keyboard.print(s);
}


void write_pass() {
  x = serial_read_2bytes();
  y = serial_read_2bytes();
  delay(delay_between);
  AbsMouse.move(x, y);
  for (int t = 0; t < 2; t++) {
    AbsMouse.press(MOUSE_LEFT);
    AbsMouse.release(MOUSE_LEFT);
  }
  Keyboard.print(pass);
}