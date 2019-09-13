# coding: utf-8

from algomusic import *

def drums1():
    # Простая барабанная партия
    v1 = Kick_voice()
    v2 = Snare_voice()
    out = []

    for i in range(8):
        out += v1.play(0, sec(1/8)) + v1.play(0, sec(1/8)) + v2.play(0, sec(1/4))

    write_wav("drums1.wav", out)

# Перевод смещения ноты от С-4, с учетом гаммы и транспонирования, в герцы
def note2freq(offs, scale, trans=0):
    note = scale[offs % len(scale)] + 12 * (offs // len(scale))
    return midi2freq(60 + note + trans)

def get_note(): # Случайная нота из пентатоники
    n = random.randint(0, 11)
    return note2freq(n, MIN_PENTA_SCALE)

def wind_chime():
    v1 = Voice(Sin(), Env())
    d1 = Delay(sec(0.5))
    out = []

    for i in range(100):
        vol = random.randint(3, 10) * 0.1 # Громкость варьируется
        out += d1.play(v1.play(get_note(), sec(0.3), sec(0.3), amp=vol), 0.3, 0.85)

    write_wav("wind_chime.wav", out)

class Muse:
    def __init__(self, interval, theme):
        self.interval_sliders = interval
        self.theme_sliders = theme
        self.rows = [0, 1] + [0] * 38
        self.scale = parse_track("c-3 d-3 e-3 f-3 g-3 a-3 b-3 c-4 c-4 d-4 e-4 f-4 g-4 a-4 b-4 c-5")
        self.clock = 1

    def get_freq(self):
        values = [self.rows[i] for i in self.interval_sliders]
        return self.scale[sum([x * 2**i for i, x in enumerate(values)])]

    def update_lfsr(self):
        xor = sum([self.rows[i] for i in self.theme_sliders]) % 2
        self.rows = self.rows[:9] + [xor ^ 1] + self.rows[9:-1]

    def pulse(self):
        self.clock += 1
        self.rows[2] = self.clock & 1
        self.rows[3] ^= int(self.clock % 2 == 0)
        self.rows[4] ^= int(self.clock % 4 == 0)
        self.rows[5] ^= int(self.clock % 8 == 0)
        self.rows[6] ^= int(self.clock % 16 == 0)
        self.rows[7] ^= int(self.clock % 6 == 0)
        self.rows[8] ^= int(self.clock % 12 == 0)
        if self.rows[2] == 0:
            self.update_lfsr()

def muse():
    #m = Muse([15, 16, 13, 0], [0, 12, 31, 0])
    #m = Muse([18, 16, 15, 0], [1, 5, 9, 10])
    #m = Muse([14, 17, 14, 2], [39, 5, 0, 6])
    m = Muse([3, 9, 39, 6], [0, 0, 9, 39])
    #m = Muse([9, 10, 5, 6], [0, 0, 39, 5])

    tempo = sec(0.1)
    v1 = Voice(Sin(), Env())
    d1 = Delay(sec(0.5))
    freq = None
    out = []

    for i in range(200):
        new_freq = m.get_freq() * 4
        if new_freq == freq:
            new_freq = None
        else:
            freq = new_freq
        out += d1.play(v1.play(new_freq, sec(0.3), tempo), 0.4)
        m.pulse()

    write_wav("muse.wav", out)

def musinum():
    step = 65 # Шаг задает номер "композиции"
    num = 0
    tempo = sec(0.12)
    v1 = Voice(LFSR(4, [3, 0]), Env(0.01))
    d1 = Delay(sec(0.1))
    f1 = LP1()
    f2 = LP1()
    out = []

    for i in range(200): # Алгоритм MusiNum в действии
        freq = note2freq(bin(num).count("1"), MAJ_SCALE, 24)
        p = v1.play(freq, tempo, tempo, amp=1 if i % 4 == 0 else 0.7)
        out += d1.play(f1.play(f2.play(p, 0.4), 0.4), 0.35, 0.7)
        num += step

    write_wav("musinum.wav", out)

def similar(data, rule, times): # Порождение мелодии из исходных данных по правилу rules, times итераций
    for i in range(times):
        new = []
        for x in data:
            new += [x + offs for offs in rule] # замена очередной ноты по правилу
        data = new
    return data

def fractal():
    # Фрактальный генератор мелодий
    #rule = [0, 1, -1, 0]
    #rule = [-2, 7, -7, 2]
    rule = [0, 2, 4, -7]

    notes = similar([0], rule, 4)
    v1 = Voice(FMSquare(), Env(0.01))
    d1 = Delay(sec(0.1))
    tempo = sec(0.12)
    out = []

    for n in notes:
        freq = note2freq(n, MIN_SCALE, 12)
        out += d1.play(v1.play(freq, tempo, tempo), 0.25, 0.8)

    write_wav("fractal.wav", out)

def drums2():
    # # Вероятностные барабаны
    kick_break = [
        10, 0.4, None, None, 0.7, None, 0.8, None, None, None, None, None, 0.9, None, None, None,
        0.9, None, None, None, 0.9, None, 0.9, None, None, None, 0.9, None, 0.6, None, None, None
    ]
    snare_break = [
        None, None, None, None, None, None, None, None, 0.8, None, 0.7, None, None, None, 0.7, None,
        None, None, 0.7, None, None, None, None, None, 0.7, None, 0.7, None, None, None, None, None
    ]
    hat_break = [SR, None, SR, None] * 8

    tempo = sec(1/16)
    v1 = Kick_voice()
    v2 = Snare_voice()
    v3 = Voice(LFSR(12, [10, 9, 1, 2, 3, 11]), Env())
    d1 = Delay(sec(0.1))
    out = []
    busy = 0.8

    for j in range(16): # Барабанные вариации
        for i in range(len(kick_break)):
            is_kick = kick_break[i] is not None and random.random() < kick_break[i] * busy
            is_snare = snare_break[i] is not None and random.random() < snare_break[i] * busy
            is_hat = (hat_break[i] is not None) and (not is_kick and not is_snare)
            p1 = v1.play(kick_break[i] if is_kick else None, tempo)
            p2 = v2.play(snare_break[i] if is_snare else None, tempo)
            p3 = v3.play(hat_break[i] if is_hat else None, sec(0.02), tempo, amp=0.4)
            out += mix(p1, d1.play(p2, 0.1), p3)

    write_wav("drums2.wav", out)

# Порождение ритма в духе "Уральских напевов"
def make_bar(size, durations): # Заполнение такта длительностями из durations
    bar = []
    while sum(bar) < size:
        d = random.choice(durations)
        if sum(bar) + sum(d) <= size:
            bar += d
    return bar

def next_note(note, intervals, note_range): # Выбор очередной ноты, случайное блуждание
    while True:
        ivals, iprobs, idir = intervals
        direction = 2 * int(random.random() < idir) - 1
        new_note = note + random.choices(ivals, iprobs)[0] * direction
        if new_note in range(note_range):
            return new_note

def funk():
    # Алгоритмический фанк
    intervals = [
        [1, 2, 3, 4, 5, 6],
        [0.5, 0.4, 0.03, 0.03, 0.03, 0.01],
        0.6
    ]

    # Набор длительностей для построения такта
    durations = [[1/4], [1/2], [1/8, 1/8], [1/4 + 1/8, 1/8], [1/16, 1/16], [1/8 + 1/16, 1/16]]

    v1 = Voice(LFSR(4, [3, 0]), Env())
    out = []
    note = 0

    for i in range(32):
        part = []
        ab = make_bar(4/4, durations) + make_bar(4/4, durations)
        for dur in ab:
            note = next_note(note, intervals, 12)
            part += v1.play(note2freq(note, MAJ_BLUES_SCALE, 12), sec(dur) * 1.2, sec(dur) * 2)
        out += part * 2

    fs, drums = read_wav("drums2.wav")
    out = list(normalize(out, 0.15))
    drums = drums * (1 + len(out) // len(drums))
    write_wav("funk.wav", mix(drums[:len(out)], out))

# 7 ступеней, 49 риффов
def split_by(lst, n): return [lst[i: i + n] for i in range(0, len(lst), n)]

def riffology():
    riffs = [split_by(load_track("txt/riff%i.txt" % i), 9) for i in range(1, 8)]

    v1 = Voice(LFSR(4, [3, 0]), Env())
    d1 = Delay(sec(0.1))
    f1 = LP1()
    tempo = sec(1/8)
    out = []
    row = random.randint(0, len(riffs) - 1)

    for i in range(32):
        col = random.randint(0, len(riffs) - 1) # Выбор нового риффа
        riff = riffs[row][col]
        row = col # Выбор ступени
        dur = tempo if random.random() < 0.7 else tempo * 2
        for freq in riff[:-1]: # Последняя нота риффа заменяется первой нотой нового риффа
            out += d1.play(f1.play(v1.play(freq * 4, dur * 1.2, dur), 0.3), 0.3, 0.7)

    fs, drums = read_wav("drums1.wav")
    out = list(normalize(out, 0.5))
    drums = drums * (1 + len(out) // len(drums))
    write_wav("riffology.wav", mix(out, out, drums[:len(out)]))

def oneliner():
    # Однострочные алгоритмические композиции
    #def f(t): return t * (t >> 11) * t / 3
    #def f(t): return div(t, (t & (t >> 12)))
    #def f(t): return (div(t, ( t >> 16 | t >> 8)) & (( t >> 5 | t >> 11))) -1 | t * (( t >> 16 | t >> 8))
    #def f(t): return t * ((t >> 12 | t >> 8) & 63 & t >> 4)
    def f(t): return t >> 3 | t << 2 & t | int(t + 5e3) >> 4 | t - 14 >> 5
    #def f(t): return (t & t // 170 * 2) + t % 31 * 0.1
    #def f(t): return t << 1 >> 1 ^ t * 3 | t >> 5 | t >> 3
    #def f(t): return t * 9 & t >> 4 | t * 5 & t >> 7 | t * 3 & t // 1024

    def div(a, b): return 0 if b == 0 else a // b

    out = [int(f(t)) & 0xff for t in range(sec(5))]
    write_wav("oneliner.wav", out, 8000)

#drums1()
#wind_chime()
#muse()
#musinum()
fractal()
#drums2()
#funk()
#riffology()
#oneliner()
