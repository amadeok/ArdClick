#include <Keyboard.h>
#include <AbsMouse.h>
#include "utils.h"
#include <avr/wdt.h>

void softwareReset() {
  wdt_enable(WDTO_15MS);  // Enable watchdog with a 15ms timeout
  while (1)
    ;  // Wait for watchdog to trigger reset
}

enum serialStatusEnum { settingX,
                        settingY,
                        ready };
int serialStatus = settingX;

enum boardModeEnum { standard,      //blinks to indicate remainer time before trigger
                     mouseKeyboard  //only lisent for serial commands for fast mouse / keyboard operations
};

unsigned int intervalMins = 5 * 60;
unsigned long long waitMs = 0;   //intervalMins * 60 * 1000;
unsigned long long debugMs = 0;  //*1000 MULTIPLIED ON SETUP()
unsigned long blinkRemTimeIntervalMs = 5 * 1000;
bool bPrintInfo = 0;
bool bBeepRemainerTime = 0;
bool bPressEnter = false;
int16_t boardMode = mouseKeyboard;
unsigned long long start = millis();
unsigned long long start2 = start;
unsigned long long startPress = start;
bool queueReset = false;
int bPanic = 0;
const int PIN_BEEP_REM = 3;
char buffer[120];



void setup() {
  pinMode(PIN_BEEP_REM, INPUT_PULLUP);

  blink(2, 30, 30, 1200);

  pinMode(PC_POWER_PIN, OUTPUT);
  digitalWrite(PC_POWER_PIN, HIGH);
  waitMs = intervalMins * 60;
  waitMs *= 1000;
  debugMs *= 1000;


  if (using_pro_micro) {
    pinMode(proMicroLED_pin, OUTPUT);  // Set RX LED as an output
    LED_PIN = proMicroLED_pin;
  }
  if (1)
    for (int n = 0; n < 2; n++) {
      blink(1, 100, 30, 700);
      blink(1, 100, 30, 1000);
    }
  delay(200);

  Serial.begin(115200);
  Serial.setTimeout(1);

  for (int n_counter = 0; n_counter < 3; n_counter++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }

  AbsMouse.init(1920, 1080);  //4320, 1650);
  Keyboard.begin();
  delay(500);
}

bool beepOrNot() {
  return bBeepRemainerTime || !digitalRead(PIN_BEEP_REM);
}
void triggerBeep() {
  for (int n = 0; n < 2; n++) {
    blink(1, 300, 200, 500);
    blink(1, 300, 200, 700);
    blink(1, 300, 200, 1000);
    blink(1, 300, 200, 1000);
    blink(1, 300, 200, 700);
    blink(1, 300, 200, 500);
  }
}

void printInfo(unsigned long targetMs, unsigned long remMs, unsigned long hours, unsigned long minutes, unsigned long tensOfMinutes) {
  Serial.print(targetMs);
  Serial.print("tms ");

  Serial.print(remMs / 1000 / 60);
  Serial.print("m ");
  Serial.print((remMs % 60000) / 1000);

  Serial.print("s | ");
  Serial.print(hours);
  Serial.print("h ");

  Serial.print(minutes);
  Serial.print("m | ");
  Serial.print(tensOfMinutes);
  Serial.print(" tens mins ");
  Serial.println("");
}

void loop() {

  // blink(3, 300, 100, 1000);
  unsigned long targetMs = (debugMs ? debugMs : waitMs);
  unsigned long long ct = millis();
  unsigned long elapsedMs = ct - start;
  unsigned long remMs = targetMs - elapsedMs;
  unsigned long hours = remMs / 3600000;              // 1 hour = 3600000 milliseconds
  unsigned long minutes = (remMs % 3600000) / 60000;  // 1 minute = 60000 milliseconds
  unsigned long tensOfMinutes = minutes / 10;
  if (boardMode == standard) {

    delay(100);

    if (bPrintInfo) {
      printInfo(targetMs, remMs, hours, minutes, tensOfMinutes);
    }

    if (elapsedMs > targetMs) {
      // Serial.println("trigger");
      //blink(6, 100, 300, 1200);
      triggerBeep();
      digitalWrite(PC_POWER_PIN, LOW);   // Turn on the LED
      delay(500);                        // Wait for a short duration
      digitalWrite(PC_POWER_PIN, HIGH);  // Turn off the LED
      start = millis();
      bPressEnter = true;
    }


    unsigned long elapsedMs2 = ct - start2;
    unsigned long remMs2 = blinkRemTimeIntervalMs - elapsedMs2;
    if (1)
      if (elapsedMs2 > blinkRemTimeIntervalMs) {
        // Serial.println("trigger");
        bool beep = beepOrNot();

        if (hours || tensOfMinutes) {
          blink(hours, 500, 300, beep ? 500 : 0);
          delay(1000);
          blink(tensOfMinutes, 150, 150, beep ? 700 : 0);
        } else if (minutes >= 2)
          blink(4, 75, 75, beep ? 900 : 0);
        else
          blink(20, 75, 75, beep ? 1000 : 0);

        start2 = millis();
      }

    if (bPressEnter && elapsedMs < 600000) {  // less than 10 minutes
      unsigned long elapsedMsPress = ct - startPress;
      unsigned long remMsPress = (10 * 1000) - elapsedMsPress;
      if (elapsedMsPress > (10 * 1000)) {
        //Serial.println("trigger");
        Keyboard.press(KEY_KP_ENTER);
        delay(300);
        Keyboard.release(KEY_KP_ENTER);
        startPress = millis();
      }
    }
  }
  String s;
  // if (Serial.availableForWrite() < 1)
  //   blink(10, 250, 50, 500);
  if (queueReset) {
    // blink(3, 250, 50, 1300);
    softwareReset();
    queueReset = false;
  }

  if (Serial.available()) {
    switch (serialStatus) {

      case settingX:
        x = serial_read_2bytes();
        serialStatus = settingY;
        break;
      case settingY:
        y = serial_read_2bytes();
        serialStatus = ready;
        break;
    }
  }
  if (serialStatus == ready) {

    key = y;
    switch (x) {
      case 30000:
        press_key(y);
        break;
      case 30001:
        s = serial_read_string(y);
        Keyboard.print(s);
        break;
      case 30002:
        write_pass();
        break;
      case 30003:
        write_string2();
        break;
      case 30004:
        x = serial_read_2bytes();
        y = serial_read_2bytes();
        AbsMouse.move(x, y);
        break;
      case 30005:

        x = serial_read_2bytes();
        y = serial_read_2bytes();
        AbsMouse.init(x, y);
        bPressEnter = false;
        for (int n_counter = 0; n_counter < 10; n_counter++) {
          digitalWrite(LED_PIN, HIGH);
          if (n_counter % 2 == 0)
            delay(50);
          else
            delay(10);
          digitalWrite(LED_PIN, LOW);
          delay(50);
        }

        break;
      case 30006:
        blink(2, 10, 10, 1100);

        delay(10);
        queueReset = true;

        // digitalWrite(resetPin, LOW); //reset can be done opening and closing serial with baud 1200
        delay(10);
        break;
      case 30007:  // right click
        x = serial_read_2bytes();
        y = serial_read_2bytes();
        move_click_right(x, y);
        break;
      case 30009:  // left click
        x = serial_read_2bytes();
        y = serial_read_2bytes();
        move_click(x, y);
        break;
      case 30008:  //change delay
        delay_between = y;
        break;
      case 40010:
        intervalMins = serial_read_2bytes();
        waitMs = intervalMins * 60;
        waitMs *= 1000;
        start = millis();
        break;
      case 40011:
        // blink(4, 100, 200, 700);
        bBeepRemainerTime = serial_read_2bytes();
        break;
      case 40009:
        boardMode = serial_read_2bytes();
        if (bBeepRemainerTime)
          blink(boardMode + 1, 500, 300, 600);
        break;
      case 40012:
        {
          y = serial_read_2bytes();
          unsigned long intervalMins_ = intervalMins;
          unsigned long ct_ = millis() / 1000;
          unsigned long *ptrArray[] = {
            &intervalMins_,
            &targetMs,
            &elapsedMs,
            &remMs,
            &hours,
            &minutes,
            &tensOfMinutes,
            &ct_
          };
          //blink(13, 150, 50, 0);
          int s = 4;  // sizeof(ptrArray[0])
          for (int n = 0; n < sizeof(ptrArray); n++)
            memcpy(buffer + s * n, ptrArray[n], s);
          // for (int n = 0; n < 1; n++){
          //   unsigned char cc = buffer[n];
          Serial.write(buffer, 120);
          // }

          break;
          // case 40009: cannot go in here lol
          //   // boardMode = serial_read_2bytes();
          //   // if (bBeepRemainerTime)
          //   //   blink(boardMode + 1, 500, 300, 600);
          //   break;
        }
      case 40013:
        //press left click
        x = serial_read_2bytes();
        y = serial_read_2bytes();
        move_click_2(x, y, false, true);
        break;
      case 40014:
        //release left click
        x = serial_read_2bytes();
        y = serial_read_2bytes();
        move_click_2(x, y, false, false);
        break;
      case 40015:
        //press right click
        x = serial_read_2bytes();
        y = serial_read_2bytes();
        move_click_2(x, y, true, true);
        break;
      case 40016:
        //release right click
        x = serial_read_2bytes();
        y = serial_read_2bytes();
        move_click_2(x, y, true, false);
        break;
      case 40017:
        y = serial_read_2bytes();
        press_key_only(y);
        break;
      case 40018:
        y = serial_read_2bytes();
        release_key_only(y);
        break;
      case 40019:  // panic, beep repeteadly
        // Serial.println("panic");
        bPanic = 1;
        // while (bPanic) {
        //   blink(3, 50, 50, 1300);
        //   delay(20);
        //   blink(3, 10, 50, 2000);
        //   delay(10);
        // }
        break;
      case 40020:
        // Serial.println("unpanic");
        bPanic = 0;
        break;

      default:
        //  blink(4);
        blink(1, 250, 250, 1600);
        blink(1, 250, 250, 1400);
        blink(1, 250, 250, 1200);
        move_click(x, y);
        break;
    }
    serialStatus = settingX;
  }
  if (bPanic == 1){
    for (int i = 0; i < 1; i++){
          blink(3, 50, 50, 1300);
          delay(20);

    }
    bPanic++;
  }else if (bPanic == 2){
      blink(3, 10, 50, 2000);
      delay(10);
      bPanic = 1;
  }
}
