from gpiozero import LED, PWMLED, MotionSensor, DistanceSensor
import time

# GPIO Pins (BCM Mode)
IR_MORNING = 17
IR_NIGHT = 27
IR_EXTRA = 22
LED_MORNING_PIN = 2
LED_NIGHT_PIN = 3
TRIG = 23
ECHO = 24
TRIG2 = 6     # Second ultrasonic sensor
ECHO2 = 13
TEMP_ALERT_PIN = 5  # Will be unused now, but LED still connected if needed

# Components
pir_morning = MotionSensor(IR_MORNING)
pir_night = MotionSensor(IR_NIGHT)
pir_extra = MotionSensor(IR_EXTRA)

led_morning = PWMLED(LED_MORNING_PIN)
led_night = PWMLED(LED_NIGHT_PIN)
led_temp_alert = LED(TEMP_ALERT_PIN)  # Unused now, but left for compatibility

ultrasonic = DistanceSensor(echo=ECHO, trigger=TRIG, max_distance=2.0)
ultrasonic_zone = DistanceSensor(echo=ECHO2, trigger=TRIG2, max_distance=2.0)

# Constants
MORNING_DURATION = 120
DIM_DELAY = 5
OFF_DELAY = 10
NIGHT_WARN_DELAY = 15
DISTANCE_THRESHOLD = 0.5  # 0.5 meters = 50 cm

# Helper Functions
def blink(led, times):
    for _ in range(times):
        led.value = 1
        time.sleep(0.2)
        led.value = 0
        time.sleep(0.2)

# Morning Phase
def morning_phase():
    print("[INFO] MORNING PHASE started.")
    blink(led_morning, 2)
    light_on = False
    dimmed = False
    last_motion = time.time()
    start_time = time.time()

    while time.time() - start_time < MORNING_DURATION:
        motion = pir_morning.motion_detected or pir_extra.motion_detected
        distance = ultrasonic.distance
        distance_zone = ultrasonic_zone.distance
        print(f"[Ultrasonic] Distance: {distance * 100:.2f} cm")
        print(f"[Zone Monitor] Distance: {distance_zone * 100:.2f} cm")

        if distance_zone < DISTANCE_THRESHOLD:
            print("[ALERT] Movement detected in restricted zone (morning phase)!")
            blink(led_night, 2)

        if motion or distance < DISTANCE_THRESHOLD:
            last_motion = time.time()
            if not light_on:
                led_morning.value = 1
                light_on = True
                dimmed = False
                print("[INFO] Morning: Presence detected. Light ON.")
            elif dimmed:
                led_morning.value = 1
                dimmed = False
                print("[INFO] Morning: Activity detected. Restoring brightness.")

        if light_on:
            idle = time.time() - last_motion
            if idle > DIM_DELAY and not dimmed:
                led_morning.value = 0.4
                dimmed = True
                print("[INFO] Morning: Idle. Light DIMMED.")
            if idle > OFF_DELAY:
                led_morning.off()
                light_on = False
                dimmed = False
                print("[INFO] Morning: Idle too long. Light OFF.")

        time.sleep(1)

# Night Phase
def night_phase():
    print("[INFO] NIGHT PHASE started.")
    while True:
        motion = pir_night.motion_detected or pir_extra.motion_detected
        distance = ultrasonic.distance
        distance_zone = ultrasonic_zone.distance
        print(f"[Ultrasonic] Distance: {distance * 100:.2f} cm")
        print(f"[Zone Monitor] Distance: {distance_zone * 100:.2f} cm")

        if distance_zone < DISTANCE_THRESHOLD:
            print("[ALERT] Movement detected in restricted zone (night phase)!")
            blink(led_night, 2)

        if motion or distance < DISTANCE_THRESHOLD:
            print("[INFO] Night: Intrusion detected. Blinking warning.")
            blink(led_night, 3)
            time.sleep(NIGHT_WARN_DELAY)
            if pir_night.motion_detected:
                led_night.off()
                print("[INFO] Night: Motion persists. Light OFF.")
        time.sleep(1)

# Main Program
try:
    morning_phase()
    night_phase()

except KeyboardInterrupt:
    print("[INFO] Exiting program.")
    led_morning.off()
    led_night.off()
    led_temp_alert.off()
