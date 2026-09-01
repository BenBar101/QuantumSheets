import numpy as np
from scipy.io import wavfile
import math

from .layout import circuit_to_moments
from .render import _SOLFEGE

# Frequencies for the treble clef staff (E4 to F5)
# Y offsets from mid_y (-2.0 to +2.0) map to these pitches:
PITCHES = {
    -2.0: 329.63, # E4
    -1.5: 349.23, # F4
    -1.0: 392.00, # G4
    -0.5: 440.00, # A4
     0.0: 493.88, # B4
     0.5: 523.25, # C5
     1.0: 587.33, # D5
     1.5: 659.25, # E5
     2.0: 698.46, # F5
}

def generate_audio(qc, filename="circuit_audio.wav", bpm=120):
    moments = circuit_to_moments(qc)
    
    sample_rate = 44100
    beat_duration = 60.0 / bpm
    
    # We will generate audio track per qubit to handle spans/sustains
    n_qubits = qc.num_qubits
    # Calculate total beats based on the maximum (start column + span) of any gate
    total_beats = 0
    for c, moment in enumerate(moments):
        for ev in moment:
            total_beats = max(total_beats, c + ev.span)
            
    total_samples = int(total_beats * beat_duration * sample_rate)
    
    # Audio buffer for the whole song
    audio_data = np.zeros(total_samples, dtype=np.float32)
    
    # ADSR Envelope parameters
    attack = 0.05
    release = 0.1
    
    for c, moment in enumerate(moments):
        for ev in moment:
            if ev.kind == "barrier" or ev.kind == "measure":
                continue
                
            # Find the y-offsets for this gate
            # For a gate, we draw notes on all its qubits (controls + targets)
            # Find the base name offset
            base_name = ev.name
            if ev.kind == "control":
                n_ctrl = len(ev.controls)
                base_name = ev.name[n_ctrl:]
                
            offset = _SOLFEGE.get(base_name, 0.0)
            freq = PITCHES.get(offset, 440.0)
            
            # Duration in samples
            dur_beats = ev.span
            dur_samples = int(dur_beats * beat_duration * sample_rate)
            start_sample = int(c * beat_duration * sample_rate)
            end_sample = min(start_sample + dur_samples, total_samples)
            actual_dur = end_sample - start_sample
            if actual_dur <= 0:
                continue
            
            t = np.linspace(0, actual_dur / sample_rate, actual_dur, False)
            
            # Apply ADSR envelope to avoid clicking
            env = np.ones_like(t)
            att_samples = int(attack * sample_rate)
            rel_samples = int(release * sample_rate)
            
            if att_samples > 0 and att_samples < actual_dur:
                env[:att_samples] = np.linspace(0, 1, att_samples)
            if rel_samples > 0 and rel_samples < actual_dur:
                env[-rel_samples:] = np.linspace(1, 0, rel_samples)
            
            # The gate appears on all its qubits. To make multi-qubit gates sound like 
            # beautiful chords, we map each participating qubit to a harmonious interval!
            # Intervals: 0 = unison, 1 = major 3rd (1.25x), 2 = perfect 5th (1.5x), 3 = octave (2.0x), 4 = major 10th (2.5x)
            intervals = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
            
            for i, q in enumerate(ev.qubits):
                interval = intervals[i % len(intervals)]
                freq_q = freq * interval
                
                # Re-synthesize for this specific frequency
                wave_q = np.sin(2 * np.pi * freq_q * t) * env
                
                # Mix it in! (divide volume by number of notes so chords aren't deafening)
                vol = 0.2 / len(ev.qubits)
                audio_data[start_sample:end_sample] += wave_q * vol

    # Normalize to 16-bit PCM
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val
    audio_data = (audio_data * 32767).astype(np.int16)
    
    wavfile.write(filename, sample_rate, audio_data)
    print(f"Audio saved to {filename}")
