# import time
import argparse
import time
import datetime
from timeit import default_timer as timer

from core.controller import Controller
from core.stream_analyzer import Stream_Analyzer
from utils.storage import connect_db, write_to_db

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', type=int, default=None, dest='device',
                        help='pyaudio (portaudio) device index')
    parser.add_argument('--height', type=int, default=450, dest='height',
                        help='height, in pixels, of the visualizer window')
    parser.add_argument('--n_frequency_bins', type=int, default=400, dest='frequency_bins',
                        help='The FFT features are grouped in bins')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--window_ratio', default='24/9', dest='window_ratio',
                        help='float ratio of the visualizer window. e.g. 24/9')
    parser.add_argument('--sleep_between_frames', dest='sleep_between_frames', action='store_true',
                        help='when true process sleeps between frames to reduce CPU usage (recommended for low update rates)')
    return parser.parse_args()

def convert_window_ratio(window_ratio):
    if '/' in window_ratio:
        dividend, divisor = window_ratio.split('/')
        try:
            float_ratio = float(dividend) / float(divisor)
        except:
            raise ValueError('window_ratio should be in the format: float/float')
        return float_ratio
    raise ValueError('window_ratio should be in the format: float/float')

def update_database(audioclip):
    db = connect_db('jamify', 'stef', 'Pass123')
    write_to_db(db, audioclip)
    db.client.close()

def run_FFT_analyzer():
    args = parse_args()
    window_ratio = convert_window_ratio(args.window_ratio)

    controller = Controller()
    controller.start_record()
    ear = Stream_Analyzer(
                    device = args.device,        # Pyaudio (portaudio) device index, defaults to first mic input
                    rate   = None,               # Audio samplerate, None uses the default source settings
                    FFT_window_size_ms  = 60,    # Window size used for the FFT transform
                    updates_per_second  = 1000,  # How often to read the audio stream for new data
                    smoothing_length_ms = 50,    # Apply some temporal smoothing to reduce noisy features
                    n_frequency_bins = args.frequency_bins, # The FFT features are grouped in bins
                    visualize = 1,               # Visualize the FFT features with PyGame
                    verbose   = args.verbose,    # Print running statistics (latency, fps, ...)
                    height    = args.height,     # Height, in pixels, of the visualizer window,
                    window_ratio = window_ratio,  # Float ratio of the visualizer window. e.g. 24/9
                    controller = controller  # Float ratio of the visualizer window. e.g. 24/9
                    )

    fps = 60  #How often to update the FFT features + display
    last_update = time.time()

    recording = False
    new_tick = False

    while True:
        updated = False
        if round(last_update) != new_tick:
            new_tick = round(last_update)
            updated = True

        if controller.last_noise is None:
            if updated:
                print('-- no noise --')
        else:
            if not recording:
                controller.start_record(record=True)
                recording = True

        if (time.time() - last_update) > (1./fps):
            last_update = time.time()
            raw_fftx, raw_fft, binned_fftx, binned_fft = ear.get_audio_features()
        elif args.sleep_between_frames:
            time.sleep(((1./fps)-(time.time()-last_update)) * 0.99)

        if updated:
            if controller.last_noise:
                now = datetime.datetime.now()
                if ((now - controller.last_noise).total_seconds() > 5):
                    controller.reset(save_file=True)
                    audioclip = controller.save_to_file()
                    update_database(audioclip)
                    time.sleep(1)
                    print('done')
                    break
                else:
                    if (now - controller.last_noise).total_seconds() > 1:
                        print(round(6 - (now - controller.last_noise).total_seconds()))
                    else:
                        print(" Playing Music ")

if __name__ == '__main__':
    while True:
        run_FFT_analyzer()
        time.sleep(1)
