import datetime
import os
import pyaudio
import wave
import struct
import matplotlib.pyplot as plt
import numpy as np
import time
from collections import deque
from statistics import mean
from pathlib import Path
from core.audioclip import Audioclip

from utils.silencer import noalsaerr
from utils.data import numpy_data_buffer



class Controller():
    FORMAT = pyaudio.paInt16 
    CHANNELS = 1
    RATE = 44100
    CHUNK = 512
    RECORD_SECONDS = 15
    WAVE_OUTPUT_FILENAME = "recordedFile.wav"
    update_window_n_frames = 1024 #Don't remove this, needed for device testing!
    device_index = 5
    with noalsaerr():
        audio = pyaudio.PyAudio()
    stream = None
    fig, ax = plt.subplots()
    recording = False
    verbose = False
    data_buffer = None
    new_data = False
    last_noise = None
    Recordframes = []

    def __init__(self):
        self.updates_per_second = self.RATE / self.update_window_n_frames
        if self.verbose:
            self.data_capture_delays = deque(maxlen=20)
            self.num_data_captures = 0
        self.open_stream()

        
    def start_record(self, data_windows_to_buffer=None, record=False):
        self.data_windows_to_buffer = data_windows_to_buffer

        if data_windows_to_buffer is None:
            self.data_windows_to_buffer = int(self.updates_per_second / 2) #By default, buffer 0.5 second of audio
        else:
            self.data_windows_to_buffer = data_windows_to_buffer

        self.data_buffer = numpy_data_buffer(self.data_windows_to_buffer, self.update_window_n_frames)

        if record:
            self.recording = True
            print("\n--🎙  -- Started recording live audio stream...\n")
        else:
            self.recording = False
            print("\n--🎙  -- Started listening for noise --\n")
        self.stream_start_time = time.time()
        self.stream.start_stream()


    def non_blocking_stream_read(self, in_data, frame_count, time_info, status):
        if self.verbose:
            start = time.time()

        if self.data_buffer is not None:
            if self.recording:
                self.Recordframes.append(in_data);
            self.data_buffer.append_data(np.frombuffer(in_data, dtype=np.int16))
            self.new_data = True
            latest_data_window = self.data_buffer.get_most_recent(5)

            avg_noise = abs(mean(latest_data_window))
            if avg_noise > 80:
                self.last_noise = datetime.datetime.now()

        if self.verbose:
            self.num_data_captures += 1
            self.data_capture_delays.append(time.time() - start)

        return in_data, pyaudio.paContinue

    def stop_record(self):
        self.recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
    

    def is_playing_audio(self):
        audio_detected = False
        for record_frame in self.Recordframes:
            data_int = struct.unpack(str(2 * 512) + 'B', record_frame)
            if ([i for i in data_int if i not in set([0, 1, 2, 3, 253, 254, 255])]):
                audio_detected = True
        return audio_detected
    

    def reset(self, save_file=False):
        if save_file:
            print("\n--🎙  -- Live recording finished...\n")
        else:
            print("\n--🎙  -- Noise Detected ...\n")
            self.recording = False
            self.data_buffer = None
            self.new_data = False
            self.Recordframes = []
        self.last_noise = None

        self.audio.close(self.stream)
        time.sleep(3)
        self.open_stream()
        
    def open_stream(self):
        self.stream = self.audio.open(
            format = pyaudio.paInt16,
            channels = 1,
            rate = self.RATE,
            input=True,
        input_device_index = 8,
            frames_per_buffer = self.update_window_n_frames,
            stream_callback=self.non_blocking_stream_read)
    

    def save_to_file(self):
        now = datetime.datetime.now()
        date_path = now.strftime("%Y-%m-%d")
        hour_path = now.strftime("%H")
        os.makedirs('/home/stef/audioclips/' + date_path, exist_ok=True)
        os.makedirs('/home/stef/audioclips/' + date_path + '/' + hour_path, exist_ok=True)
        filename = f'{now.strftime("%Y%m%d-%H%M%S")}.wav'
        filepath = '/home/stef/audioclips/' + date_path + '/' + hour_path + '/' + filename

        waveFile = wave.open(filepath, 'wb')
        waveFile.setnchannels(self.CHANNELS)
        # frames = waveFile.getnframes()
        # rate = waveFile.getframerate()
        waveFile.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        waveFile.setframerate(self.RATE)
        waveFile.writeframes(b''.join(self.Recordframes))
        frames = waveFile.getnframes()
        duration = frames / float(self.RATE)
        waveFile.close()
        print(f"\n--🎙  -- File written: {filepath}...\n")
        size = Path(filepath).stat().st_size
        audioclip = Audioclip(filename=filename, path=f'{date_path}/{hour_path}', startTime=datetime.datetime.now().isoformat(), size=size, duration=duration)
        return audioclip