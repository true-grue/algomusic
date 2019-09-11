# coding: utf-8

import math
import random
import struct
import wave

SR = 48000

def read_wav(filename):
    with wave.open(filename, "r") as f:
        samples = []
        for i in range(f.getnframes()):
            x = struct.unpack("<h", f.readframes(1))
            samples.append(x[0])
        return f.getframerate(), list(normalize(samples))

def normalize(samples, level=1):
    max_val = max((abs(x) for x in samples))
    samples = (level * x / max_val for x in samples)
    return samples

def write_wav(filename, samples, sr=SR):
    with wave.open(filename, "w") as f:
        f.setparams((1, 2, sr, len(samples), "NONE", ""))
        f.writeframes(b"".join([struct.pack("<h",
                      int(x * 32767)) for x in normalize(samples)]))

class Square: # Простой генератор прямоугольной формы волны
    def __init__(self):
        self.phase = 0 # Фаза изменяется в пределах [0, 1)
       
    def next(self, freq, width=0.5): # width задает ширину импульса
        y = 2 * int(self.phase < width) - 1
        self.phase = (self.phase + freq / SR) % 1 # SR обозначает частоту дискретизации
        return y

def sec(n): return int(n * SR) # Перевод секунд в кол-во сэмплов

class Saw: # Простой генератор пилообразного сигнала
    def __init__(self):
        self.phase = 0
       
    def next(self, freq):
        y = 2 * self.phase - 1
        self.phase = (self.phase + freq / SR) % 1
        return y

class Env: # Простой генератор огибающей (амплитудной, частотной)
    def __init__(self, attack_time=sec(0.0001)): # Время атаки
        self.reset()
        self.attack_time = attack_time
        self.amp = 0

    def reset(self):
        self.time = 0

    def next(self, decay_time): # Время затухания
        if self.time < self.attack_time:
            self.amp = min(self.amp + 1 / self.attack_time, 1)
        else:
            self.amp = max(self.amp - 1 / decay_time, 0)            
        self.time += 1
        return self.amp

class Sin: # Генератор синусоидального сигнала
    def __init__(self):
        self.phase = 0
       
    def next(self, freq, pm=0): # pm задает фазовую модуляцию
        y = math.sin(self.phase + pm)
        self.phase = (self.phase + 2 * math.pi * freq / SR) % (2 * math.pi)
        return y

class FMSaw: # Синтез пилообразного синала с помощью FM и обратной связи
    def __init__(self):
        self.op = Sin()
        self.fb = 0
       
    def next(self, freq, cutoff=1.8):
        self.fb = self.op.next(freq, self.fb * cutoff)
        return self.fb

class FMSaw: # Генератор пилообразного сигнала путем FM-синтеза
    def __init__(self):
        self.op = Sin()
        self.fb = 0
       
    def next(self, freq, cutoff=1.8): # cutoff работает подобно частоте среза в фильтрах
        self.fb = self.op.next(freq, self.fb * cutoff)
        return self.fb

class FMSquare: # "FM-прямоугольник", используется трюк с разностью 2 пилообразных сигналов
    def __init__(self):
        self.op1 = Sin()
        self.op2 = Sin()
        self.op2.phase = math.pi
        self.fb1 = 0
        self.fb2 = 0
       
    def next(self, freq, cutoff=1.5, width=0):
        self.fb1 = self.op1.next(freq, self.fb1 * cutoff)
        self.fb2 = self.op2.next(freq, self.fb2 * cutoff + width)
        return self.fb1 - self.fb2

class Voice: # Голос или инструмент, параметризуется осциллятором и огибающей
    def __init__(self, osc, env):
        self.osc = osc
        self.env = env
        self.reset(0, 0)

    def reset(self, freq, amp): # None обозначает продолжание звучания
        if freq is not None:
            self.env.reset()
            self.freq = freq
            self.amp = amp
    
    # on_time - время нажатой "клавиши", play_time - общее время звучания голоса
    def play(self, freq, on_time, play_time, amp=1):
        samples = []
        self.reset(freq, amp)
        for i in range(play_time):
            vol = self.amp * self.env.next(on_time)
            samples.append(vol * self.osc.next(self.freq))
        return samples

def midi2freq(m): # Перевод MIDI-значения [0-127] в герцы
    return 440 * 2 ** ((m - 69) / 12)

class SID_voice: # Имитация звучания SID
    def __init__(self):
        self.osc = FMSquare()
        self.lfo = Sin()
        self.env = Env()
        self.reset(0, 0)
        
    reset = Voice.reset
        
    def play(self, freq, on_time, play_time, amp=1, pwm_freq=0.3, pwm_amp=3):
        lst = []
        self.reset(freq, amp)
        for i in range(play_time):
            pwm = self.lfo.next(pwm_freq) * pwm_amp
            vol = self.amp * self.env.next(on_time)
            lst.append(vol * self.osc.next(self.freq, width=pwm))
        return lst

# Чтение простого текстового формата, в духе музыкальных трекеров
# Пример: "D-3 ... C-3 ... === ... E-3 ..."
TRACK_NAMES = dict(zip("c- c# d- d# e- f- f# g- g# a- a# b-".split(),
                   range(12)))

def name2freq(name, trans): # Имя ноты в духе "С-4" или "d#5"
    n, o = name[:2].lower(), int(name[2])
    return midi2freq(TRACK_NAMES[n] + 12 * (o + 1) + trans)

# Перевод текста в список значений частота или None (удержание ноты)
def parse_track(text, trans=0):
    return [name2freq(x, trans) if x[0].isalpha() else
            None for x in text.split()]

def load_track(filename, trans=0): # Загрузить и разобрать текст
    with open(filename) as f:
        return parse_track(f.read(), trans)

def mix(*tracks): return [sum(x) for x in zip(*tracks)] # Микширование нескольких голосов

class Delay: # Эффект дилэй ("эхо")
    def __init__(self, size):
        self.line = [0] * size # Линия задержки размером size
        self.idx = 0

    def play(self, samples, level, fb=0.5): # level - уровень эхо-сигнала, fb - уровень обратной связи
        lst = []
        for x in samples:
            old = self.line[self.idx] # Самое старое значение из линии задержки
            lst.append(x + old * level) # Выдача результата
            self.line[self.idx] = old * fb + x # Обновленное значение в линии задержки
            self.idx = (self.idx + 1) % len(self.line)
        return lst

class LP1: # Простейший рекурсивный НЧ-фильтр
    def __init__(self):
        self.y = 0

    def play(self, samples, cutoff): # Частота среза cutoff
        lst = []
        for x in samples:
            self.y += cutoff * (x - self.y) # y' = y + k * (x - y)
            lst.append(self.y)
        return lst

class LFSR: # Генератор шума на основе регистра сдвига с линейной обратной связью
    def __init__(self, bits, taps):
        self.bits = bits # Разрядность регистра
        self.taps = taps # Индексы для вычисления очередного бита
        self.state = 1 # Состояние регистра
        self.phase = 0
    
    def next(self, freq):
        y = self.state & 1
        self.phase += 2 * freq / SR
        if self.phase > 1:
            self.phase -= 1
            # Xor значений по индексам бит taps
            x = 0
            for b in (self.state >> i for i in self.taps):
                x ^= b
            self.state = (self.state >> 1) | ((~x & 1) << (self.bits - 1))
        return 2 * y - 1

class Kick_voice: # Синтез бас-барабана
    def __init__(self):
        self.osc = FMSquare()
        self.env = Env()
        self.pitch_env = Env() # Частотная огибающая
        self.amp = 0
        
    def reset(self, freq, amp):
        if freq is not None:
            self.env.reset()
            self.pitch_env.reset()
            self.amp = amp
        
    def play(self, freq, play_time, amp=1):
        lst = []
        self.reset(freq, amp)
        for i in range(play_time):
            vol = self.amp * self.env.next(sec(0.1))
            lst.append(vol * self.osc.next(180 * self.pitch_env.next(sec(0.1))))
        return lst

class Snare_voice: # Синтез малого барабана
    def __init__(self):
        self.bass = FMSquare() # Басовая составляющая тембра
        self.osc = LFSR(12, [7, 9, 1, 2, 3, 11])
        self.env = Env()
        self.pitch_env = Env()
        self.amp = 0
        
    def reset(self, freq, amp):
        if freq is not None:
            self.env.reset()
            self.pitch_env.reset()
            self.amp = amp
        
    def play(self, freq, play_time, amp=1):
        lst = []
        self.reset(freq, amp)
        for i in range(play_time):
            vol = self.amp * self.env.next(sec(0.1))
            m = 0.5 * self.osc.next(16000 * self.pitch_env.next(sec(0.3)))
            m += self.bass.next(320 * self.pitch_env.next(sec(0.3)))
            lst.append(vol * m)
        return lst

MAJ_SCALE = [0, 2, 4, 5, 7, 9, 11] # Мажор
MIN_SCALE = [0, 2, 3, 5, 7, 8, 10] # Минор
MAJ_PENTA_SCALE = [0, 2, 4, 7, 9] # Мажорная пентатоника
MIN_PENTA_SCALE = [0, 3, 5, 7, 10] # Минорная пентатоника
MAJ_BLUES_SCALE = [0, 2, 3, 4, 7, 9] # Мажорная блюзовая гамма
MIN_BLUES_SCALE = [0, 3, 5, 6, 7, 10] # Минорная блюзовая гамма

# Перевод смещения ноты от С-4, с учетом гаммы и транспонирования, в герцы
def note2freq(offs, scale, trans=0):
    note = scale[offs % len(scale)] + 12 * (offs // len(scale))
    return midi2freq(60 + note + trans)
