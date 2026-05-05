NeuroDrive-BCI: Real-Time Brain-Computer Interface for Assistive Mobility
A closed-loop, machine-learning-powered robotic wheelchair prototype that translates facial bio-signals into physical driving commands.

The Vision
Traditional motorized wheelchairs require precise hand dexterity, which limits autonomy for patients with severe motor impairments. Our engineering team set out to bypass the hands entirely.

NeuroDrive is a fully functional Brain-Computer Interface (BCI) pipeline. Instead of a joystick, the pilot uses natural facial movements—specifically jaw clenches and eye blinks—to drive and steer a 20kg physical motorized chassis.

How It Works: The "Two Island" Architecture
To ensure absolute patient safety and zero-latency processing, we split the hardware into two completely isolated systems that communicate invisibly over a localized Wi-Fi bridge.

Island 1: The AI Pilot Station (Data Acquisition & Inference)
The Sensors: Surface electrodes capture raw, noisy analog bio-signals (EMG/EOG) from the pilot's jaw and eyes at 100 Hz.

The DAQ: An Arduino UNO R4 acts as the high-speed data acquisition unit, streaming the electrical data via serial to the processing engine.

The ML Engine: A custom Python pipeline extracts 14 distinct statistical features (RMS, Variance, Zero-Crossing Rate, etc.) from overlapping 30-frame data windows.

The Brain: A trained Random Forest classifier instantly predicts the pilot's intent (Relaxed, Jaw Clench, Left Wink, Right Wink, Double Blink) in under 10 milliseconds.

Island 2: The Physical Chassis (Actuation & Power)
The Wireless Bridge: The laptop wirelessly beams the classified command to a Raspberry Pi Zero W mounted on the wheelchair using a private Access Point (AP) network, ensuring <10ms latency.

The Muscle: An L298N Motor Driver translates the 3.3V logic signals into high-current 12V power, driving dual high-torque DC metal gear motors.

The Power Matrix: A 12V Lead-Acid battery anchors the system's center of gravity. It is sustainably recharged by a custom-mounted 20W, 21.5V solar canopy passing through a PWM charge controller.

Key Engineering Failsafes
We didn't just build a toy; we engineered a robust mobility device. Real humans twitch, and real Wi-Fi drops. Here is how we handled it:

The 15-Frame Noise Rejection Filter: The AI requires a sustained signal to act (e.g., holding a jaw clench for 10 consecutive frames). Fast, accidental facial twitches are mathematically ignored by our logic gate.

Instant Hardware Braking: The "Double Blink" command overrides all movement with a 3-frame priority trigger.

The Hardware Kill-Switch: A high-current Emergency Stop button is wired directly between the 12V battery and the motor driver. Hitting it kills the motors instantly without crashing the isolated Raspberry Pi.

The Tech Stack
Software: Python (Pandas, Scikit-Learn, Pygame), C++ (Arduino IDE)

Algorithms: Random Forest Classification, SMOTE (Synthetic Minority Over-sampling Technique), Real-time Digital Signal Processing (DSP)

Hardware: Arduino UNO R4, Raspberry Pi Zero W, L298N Motor Driver, 12V DC Gear Motors, PWM Solar Controller

The Engineering Team
Developed as a final-year engineering capstone project by:

Pralhadraj Joshi

Swastik

Vikram