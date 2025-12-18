import numpy as np
import matplotlib.pyplot as plt

FILENAME = "input_data.txt"
FILE_CLEAN = "input_clean.txt"
NUM_SAMPLES = 100
AMPLITUDE = 1000
OFFSET = 2048
NOISE_LEVEL = 200

t = np.linspace(0, 4 * np.pi, NUM_SAMPLES)

sin_wave = np.sin(t) * AMPLITUDE

square_wave = np.sign(np.sin(t)) * AMPLITUDE

signal = np.concatenate([sin_wave[:NUM_SAMPLES // 2], square_wave[NUM_SAMPLES // 2:]])

noise = np.random.normal(0, NOISE_LEVEL, NUM_SAMPLES)

noisy_signal = signal + noise + OFFSET;

noisy_signal = np.clip(noisy_signal, 0, 4095).astype(int)
signal_clean = np.clip(signal + OFFSET, 0, 4095).astype(int)


with open(FILENAME, 'w') as f:
    for val in noisy_signal:
        f.write(f"{val:X}\n")

with open(FILE_CLEAN, 'w') as f:
    for val in signal_clean:
        f.write(f"{val:X}\n")

plt.plot(noisy_signal)
plt.plot(signal_clean)
plt.title("Generated Input Signal")
plt.show()
