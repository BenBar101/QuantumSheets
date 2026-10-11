import logging
import numpy as np
import wave
import math

from .layout import circuit_to_moments
from .mapping import _SOLFEGE

_log = logging.getLogger(__name__)

# Cache for synthesised piano notes keyed by (freq, duration, sample_rate)
_NOTE_CACHE: dict = {}

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

def _unroll_moments(moments):
    def unroll_segment(start_idx, end_idx):
        unrolled = []
        c = start_idx
        while c < end_idx:
            moment = moments[c]
            repeat_start = next((ev for ev in moment if ev.kind == "repeat_start"), None)
            if repeat_start:
                try:
                    iters = int(repeat_start.label)
                except ValueError:
                    iters = 2
                    
                # Find matching repeat_end
                c_end = c + 1
                depth = 1
                while c_end < end_idx:
                    end_moment = moments[c_end]
                    if any(ev.kind == "repeat_start" and ev.qubits == repeat_start.qubits for ev in end_moment):
                        depth += 1
                    if any(ev.kind == "repeat_end" and ev.qubits == repeat_start.qubits for ev in end_moment):
                        depth -= 1
                        if depth == 0:
                            break
                    c_end += 1
                
                body_unrolled = unroll_segment(c + 1, c_end)
                for _ in range(iters):
                    unrolled.extend(body_unrolled)
                c = c_end + 1
            else:
                unrolled.append(moment)
                c += 1
        return unrolled
    return unroll_segment(0, len(moments))

def _event_to_notes(ev, base_dur_sec):
    """
    Map an event to a list of notes with frequencies and durations.
    - Control notes are drawn as black notes on B4 (Si) and play shorter than target notes.
    - Target notes are drawn as whole notes and play for the full resonant duration.
    - Single-qubit gates are drawn as black notes with standard articulation.
    """
    notes = []
    ratio_intervals = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]

    if ev.kind == "control":
        n_ctrl = len(ev.controls)
        base_name = ev.name[n_ctrl:] if ev.name[n_ctrl:] else ev.name
        target_off = _SOLFEGE.get(base_name, 0.0)
        target_freq = PITCHES.get(target_off, 392.00)

        # Control notes: black notes on B4 (Si), shorter than target notes
        ctrl_dur_sec = base_dur_sec * 0.45
        for _ in ev.controls:
            notes.append({
                "freq": 493.88,
                "dur_sec": ctrl_dur_sec,
            })

        # Target notes: whole notes, full resonant duration
        target_dur_sec = base_dur_sec * 0.95
        for i, _ in enumerate(ev.targets):
            rat = ratio_intervals[i % len(ratio_intervals)]
            notes.append({
                "freq": target_freq * rat,
                "dur_sec": target_dur_sec,
            })

    elif ev.kind == "single":
        off = _SOLFEGE.get(ev.name, 0.0)
        freq_p = PITCHES.get(off, 440.0)
        black_dur_sec = base_dur_sec * 0.85
        notes.append({
            "freq": freq_p,
            "dur_sec": black_dur_sec,
        })

    elif ev.kind == "swap":
        swap_dur_sec = base_dur_sec * 0.85
        base_freq = 493.88
        for i in range(len(ev.targets)):
            rat = ratio_intervals[i % len(ratio_intervals)]
            notes.append({
                "freq": base_freq * rat,
                "dur_sec": swap_dur_sec,
            })

    else:
        # Generic multi-qubit gate
        base_name = ev.name
        if base_name in ("rzz", "rxx", "ryy"):
            base_name = base_name[-1]
        off = _SOLFEGE.get(base_name, 0.0)
        base_freq = PITCHES.get(off, 440.0)
        chord_dur_sec = base_dur_sec * 0.85
        for i in range(len(ev.qubits)):
            rat = ratio_intervals[i % len(ratio_intervals)]
            notes.append({
                "freq": base_freq * rat,
                "dur_sec": chord_dur_sec,
            })

    return notes

def _synthesize_piano_note(freq, duration, sample_rate=44100):
    """
    Synthesize an acoustic piano note at `freq` Hz for `duration` seconds.
    Features:
    - Multiple harmonics with natural acoustic roll-off
    - Phase dispersion across harmonics to eliminate synthetic electronic phasing
    - Inharmonicity (string stiffness dispersion)
    - Three-string unison chorus / detuning
    - Fast hammer attack with transient thump
    - Frequency-dependent dual exponential decay
    - Pure NumPy soundboard acoustic comb reflections
    - Smooth damper release
    """
    cache_key = (round(freq, 2), round(duration, 4), sample_rate)
    if cache_key in _NOTE_CACHE:
        return _NOTE_CACHE[cache_key].copy()

    n_samples = int(duration * sample_rate)
    if n_samples <= 0:
        return np.zeros(0, dtype=np.float32)

    t = np.linspace(0, duration, n_samples, endpoint=False)

    # 1. Harmonic weights with natural roll-off
    harmonic_weights = [1.0, 0.65, 0.40, 0.25, 0.15, 0.10, 0.05, 0.02]
    B = 0.00018  # Inharmonicity factor

    # Unison detuning shifts (in Hz) for the multi-string acoustic piano chorus
    detunes = [-0.35, 0.0, +0.35]
    detune_weights = [0.3, 0.4, 0.3]

    base_decay = 1.8 * (freq / 440.0) ** 0.4
    wave = np.zeros(n_samples, dtype=np.float32)

    for h_idx, w in enumerate(harmonic_weights):
        k = h_idx + 1
        f_k = k * freq * np.sqrt(1.0 + B * (k ** 2))
        if f_k >= sample_rate / 2.0:
            break

        decay_rate = base_decay * (1.0 + 0.7 * (k ** 1.3))
        env_h = 0.65 * np.exp(-decay_rate * t) + 0.35 * np.exp(-decay_rate * 0.35 * t)
        phi_k = np.sin(k * 2.39996) * np.pi

        h_wave = np.zeros(n_samples, dtype=np.float32)
        for d_hz, dw in zip(detunes, detune_weights):
            h_wave += dw * np.sin(2 * np.pi * (f_k + d_hz * (k ** 0.5)) * t + phi_k)

        wave += w * env_h * h_wave

    # 2. Fast attack hammer strike curve
    attack_samples = int(0.004 * sample_rate)
    if attack_samples > 0 and attack_samples < n_samples:
        att_curve = 1.0 - np.exp(-t[:attack_samples] / 0.0015)
        wave[:attack_samples] *= att_curve

    # 3. Subtle hammer strike thump
    thump_samples = min(int(0.025 * sample_rate), n_samples)
    if thump_samples > 0:
        t_thump = t[:thump_samples]
        thump = 0.18 * np.sin(2 * np.pi * (freq * 0.5) * t_thump) * np.exp(-t_thump / 0.006)
        wave[:thump_samples] += thump

    # 4. Soundboard body resonance (feedback comb filter — the in-place
    #    accumulation deliberately creates IIR-style ringing that mimics
    #    sympathetic string and soundboard resonance)
    delays = [int(0.029 * sample_rate), int(0.037 * sample_rate)]
    gains = [0.22, 0.18]
    for d, g in zip(delays, gains):
        if n_samples > d:
            refl = np.copy(wave)
            for offset in range(d, n_samples, d):
                chunk_len = min(d, n_samples - offset)
                refl[offset:offset + chunk_len] += g * refl[offset - d:offset - d + chunk_len]
            wave += 0.25 * refl

    # 5. Damper release at the end
    rel_samples = int(0.05 * sample_rate)
    if rel_samples > 0 and rel_samples < n_samples:
        rel_curve = np.linspace(1.0, 0.0, rel_samples) ** 2
        wave[-rel_samples:] *= rel_curve

    _NOTE_CACHE[cache_key] = wave
    return wave.copy()

def generate_audio(qc, filename: str = "circuit_audio.wav", bpm: int = 120, unroll_subcircuits: bool = True, moments=None) -> None:
    """Synthesize audio for a quantum circuit to a 16-bit PCM .wav file.
    Note durations accurately match visual note types (control notes are shorter than target notes).

    Parameters
    ----------
    qc : QuantumCircuit
        The circuit to sonify.
    filename : str
        Output WAV file path.
    bpm : int
        Beats per minute.
    unroll_subcircuits : bool
        Whether to unroll custom sub-circuits.
    moments : list, optional
        Pre-computed moments from ``circuit_to_moments``. If *None*,
        moments are computed from *qc*.
    """
    if moments is None:
        raw_moments = circuit_to_moments(qc, unroll_subcircuits=unroll_subcircuits)
    else:
        raw_moments = moments
    moments = _unroll_moments(raw_moments)
    
    sample_rate = 44100
    beat_duration = 60.0 / bpm
    
    total_beats = 0
    for c, moment in enumerate(moments):
        for ev in moment:
            total_beats = max(total_beats, c + ev.span)
            
    total_samples = int((total_beats + 0.6) * beat_duration * sample_rate)
    audio_data = np.zeros(total_samples, dtype=np.float32)
    
    for c, moment in enumerate(moments):
        for ev in moment:
            if ev.kind in ("barrier", "measure", "repeat_start", "repeat_end", "bracket_start", "bracket_end"):
                continue

            start_sample = int(c * beat_duration * sample_rate)
            base_dur_sec = ev.span * beat_duration
            notes_info = _event_to_notes(ev, base_dur_sec)

            for n_info in notes_info:
                freq = n_info["freq"]
                dur_sec = n_info["dur_sec"]
                wave_note = _synthesize_piano_note(freq, dur_sec, sample_rate)
                
                # Mix in the note
                vol = 0.35 / max(1, len(ev.qubits))
                end_idx = min(start_sample + len(wave_note), total_samples)
                audio_data[start_sample:end_idx] += wave_note[:end_idx - start_sample] * vol

    # Normalize to 16-bit PCM
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val
    audio_data = (audio_data * 32767 * 0.95).astype(np.int16)
    
    with wave.open(str(filename), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())

    _log.info("Audio saved to %s", filename)
