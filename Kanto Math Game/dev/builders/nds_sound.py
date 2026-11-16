"""DS music without a DS: a game file's sound data (SDAT) -> MIDI + SoundFont (SF2), for FluidSynth.

The DS plays its music live from sequences (SSEQ: notes, like MIDI) and instrument banks (SBNK)
that point at sample archives (SWAR). This turns each sequence into a standard MIDI file and its
bank into an SF2 SoundFont, so FluidSynth can render it to audio (dev/builders/build_music_library.py).
Written from the Nitro Composer format notes (the SDAT / SSEQ / SBNK / SWAR layouts, as documented
by the DS homebrew community; see kanto_handoff/music_tools/README.md). Pure standard library.

    python -I dev/builders/nds_sound.py list <game.nds>                 the sequences in it
    python -I dev/builders/nds_sound.py one <game.nds> <SEQ_NAME> <dir>  one song -> dir/<name>.mid + .sf2
"""
import math
import os
import random
import struct
import sys

STEP_MS = 2728 * 64 / 33513982 * 1000 * 1.0   # the DS sound engine updates envelopes every ~5.2 ms (one step)
AMPL_MIN = -92544                          # silence, in the engine's units (1/128 of 0.1 dB... see _db)


# ------------------------------------------------------------------------------------------- the ROM
def nitro_files(rom_path):
    """{path: (offset, size)} for every file in a .nds game file (its NitroFS)."""
    with open(rom_path, "rb") as f:
        head = f.read(0x200)
        fnt_off, fnt_size, fat_off, fat_size = struct.unpack_from("<4I", head, 0x40)
        f.seek(fnt_off)
        fnt = f.read(fnt_size)
        f.seek(fat_off)
        fat = f.read(fat_size)
    out = {}

    def walk(dir_id, path):
        sub, first, _ = struct.unpack_from("<IHH", fnt, (dir_id & 0xFFF) * 8)
        p, fid = sub, first
        while True:
            n = fnt[p]
            p += 1
            if n == 0:
                break
            name = fnt[p:p + (n & 0x7F)].decode("latin-1")
            p += n & 0x7F
            if n & 0x80:
                child = struct.unpack_from("<H", fnt, p)[0]
                p += 2
                walk(child, path + name + "/")
            else:
                start, end = struct.unpack_from("<II", fat, fid * 8)
                out[path + name] = (start, end - start)
                fid += 1
    walk(0xF000, "")
    return out


def read_part(path, off, size):
    with open(path, "rb") as f:
        f.seek(off)
        return f.read(size)


# ------------------------------------------------------------------------------------------- SDAT
class SDAT:
    def __init__(self, data):
        if data[:4] != b"SDAT":
            raise ValueError("not an SDAT")
        self.d = data
        symb, _ss, info, _is, fat, _fs = struct.unpack_from("<6I", data, 0x10)
        self.names = self._symbols(symb) if symb else {}
        self.info = info
        n = struct.unpack_from("<I", data, fat + 8)[0]
        self.fat = [struct.unpack_from("<II", data, fat + 12 + i * 16) for i in range(n)]
        self.seqs = self._records(0, lambda o: dict(zip(("file", "bank", "vol", "player"), (
            struct.unpack_from("<H", data, o)[0], struct.unpack_from("<H", data, o + 4)[0], data[o + 6], data[o + 9]))))
        self.banks = self._records(2, lambda o: {"file": struct.unpack_from("<H", data, o)[0],
                                                  "swar": list(struct.unpack_from("<4H", data, o + 4))})
        self.swars = self._records(3, lambda o: {"file": struct.unpack_from("<I", data, o)[0] & 0xFFFFFF})
        self._swar_cache = {}

    def _symbols(self, base):
        out = {}
        for kind, key in ((0, "seq"), (2, "bank"), (3, "wavearc")):
            rec = struct.unpack_from("<I", self.d, base + 8 + kind * 4)[0]
            if not rec:
                continue
            n = struct.unpack_from("<I", self.d, base + rec)[0]
            names = []
            for i in range(n):
                o = struct.unpack_from("<I", self.d, base + rec + 4 + i * 4)[0]
                if o:
                    end = self.d.index(b"\0", base + o)
                    names.append(self.d[base + o:end].decode("latin-1"))
                else:
                    names.append(None)
            out[key] = names
        return out

    def _records(self, kind, parse):
        rec = struct.unpack_from("<I", self.d, self.info + 8 + kind * 4)[0]
        n = struct.unpack_from("<I", self.d, self.info + rec)[0]
        out = []
        for i in range(n):
            o = struct.unpack_from("<I", self.d, self.info + rec + 4 + i * 4)[0]
            out.append(parse(self.info + o) if o else None)
        return out

    def file(self, fid):
        off, size = self.fat[fid]
        return self.d[off:off + size]

    def seq_name(self, i):
        names = self.names.get("seq") or []
        return (names[i] if i < len(names) else None) or f"SEQ_{i:03d}"

    def swar(self, idx):
        if idx not in self._swar_cache:
            self._swar_cache[idx] = parse_swar(self.file(self.swars[idx]["file"])) if self.swars[idx] else []
        return self._swar_cache[idx]


# ------------------------------------------------------------------------------------------- samples
IMA_STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88,
            97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658,
            724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660,
            4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818,
            18500, 20350, 22385, 24623, 27086, 29794, 32767]
IMA_INDEX = [-1, -1, -1, -1, 2, 4, 6, 8]


def decode_swav(d):
    """(16-bit samples as list, rate, loop start or None, loop end) from one SWAV body (12-byte header + data)."""
    kind, loops, rate, _time, loop_off, nonloop = struct.unpack_from("<BBHHHI", d, 0)
    body = d[12:12 + (loop_off + nonloop) * 4]
    if kind == 0:
        s = [(b - 256 if b > 127 else b) << 8 for b in body]
        ls = loop_off * 4
    elif kind == 1:
        s = list(struct.unpack_from(f"<{len(body) // 2}h", body))
        ls = loop_off * 2
    else:
        pred, idx = struct.unpack_from("<hH", body, 0)
        idx = min(idx & 0x7F, 88)
        s = []
        for b in body[4:]:
            for nib in (b & 0xF, b >> 4):
                step = IMA_STEP[idx]
                diff = step >> 3
                if nib & 1:
                    diff += step >> 2
                if nib & 2:
                    diff += step >> 1
                if nib & 4:
                    diff += step
                pred = max(-32768, min(32767, pred - diff if nib & 8 else pred + diff))
                idx = max(0, min(88, idx + IMA_INDEX[nib & 7]))
                s.append(pred)
        ls = (loop_off - 1) * 8 if loop_off else 0
    return s, rate, (ls if loops else None), len(s)


def parse_swar(d):
    if d[:4] != b"SWAR":
        return []
    n = struct.unpack_from("<I", d, 0x38)[0]
    offs = list(struct.unpack_from(f"<{n}I", d, 0x3C))
    ends = offs[1:] + [len(d)]
    out = []
    for a, b in zip(offs, ends):
        try:
            out.append(decode_swav(d[a:b]))
        except (struct.error, IndexError):
            out.append(None)
    return out


def psg_sample(duty):
    """One looped cycle of the DS's square wave (duty 0-6: (duty+1)/8 high), 32 samples, A4 at 14080 Hz."""
    high = (duty + 1) * 4 if duty < 7 else 0
    return [12000 if i < high else -12000 for i in range(32)] * 8, 14080, 0, 256


def noise_sample():
    rnd = random.Random(1)
    s = [rnd.choice((12000, -12000)) for _ in range(32768)]
    return s, 32768, 0, len(s)


# ------------------------------------------------------------------------------------------- envelopes
ATTACK_LUT = [0x00, 0x01, 0x05, 0x0E, 0x1A, 0x26, 0x33, 0x3F, 0x49, 0x54, 0x5C, 0x64, 0x6D, 0x74, 0x7B, 0x7F, 0x84,
              0x89, 0x8F]


def _attack_ms(a):
    lvl = ATTACK_LUT[0x7F - a] if a >= 0x6D else 0xFF - a
    ampl, steps = AMPL_MIN, 0
    while ampl < -128 * 10 and steps < 20000:     # (to within 1 dB of full)
        ampl = -((-ampl * lvl) >> 8)
        steps += 1
    return steps * STEP_MS


def _fall_rate(x):
    if x == 0x7F:
        return 0xFFFF
    if x == 0x7E:
        return 0x3C00
    if x < 0x32:
        return x * 2 + 1
    return 0x1E00 // (0x7E - x)


def _sustain_db(s):
    return -100.0 if s == 0 else max(-100.0, 40 * math.log10(s / 127))


def _timecents(ms):
    return -12000 if ms <= 1 else int(round(1200 * math.log2(ms / 1000)))


def envelope(attack, decay, sustain, release):
    """SF2 generator values (attack, decay, sustain attenuation cB, release) from the DS's ADSR bytes."""
    db_per_step = lambda rate: rate / 1280.0          # (engine units: 1/128 of 0.1 dB)
    full = 100.0                                      # SF2 times are for a 100% (100 dB) change
    dec_ms = full / db_per_step(_fall_rate(decay)) * STEP_MS
    rel_ms = full / db_per_step(_fall_rate(release)) * STEP_MS
    sus_cb = int(round(-_sustain_db(sustain) * 10))
    return _timecents(_attack_ms(attack)), _timecents(dec_ms), min(1440, max(0, sus_cb)), _timecents(rel_ms)


# ------------------------------------------------------------------------------------------- SBNK -> SF2
def parse_sbnk(d):
    """[instrument or None] where an instrument is a list of regions:
    (low key, high key, kind, swav, swar slot, root note, attack, decay, sustain, release, pan)."""
    n = struct.unpack_from("<I", d, 0x38)[0]
    out = []
    for i in range(n):
        kind, off = struct.unpack_from("<BH", d, 0x3C + i * 4)
        if kind == 0 or off >= len(d):
            out.append(None)
            continue
        if kind < 16:
            out.append([(0, 127, kind) + struct.unpack_from("<HHBBBBBB", d, off)])
        elif kind == 16:
            lo, hi = d[off], d[off + 1]
            regs, p = [], off + 2
            for key in range(lo, hi + 1):
                sub = struct.unpack_from("<H", d, p)[0] & 0xFF
                regs.append((key, key, sub) + struct.unpack_from("<HHBBBBBB", d, p + 2))
                p += 12
            out.append(regs)
        elif kind == 17:
            tops = [k for k in d[off:off + 8] if k]
            regs, p, lo = [], off + 8, 0
            for top in tops:
                sub = struct.unpack_from("<H", d, p)[0] & 0xFF
                regs.append((lo, top, sub) + struct.unpack_from("<HHBBBBBB", d, p + 2))
                p += 12
                lo = top + 1
            out.append(regs)
        else:
            out.append(None)
    return out


def _chunk(tag, data):
    return tag + struct.pack("<I", len(data)) + data + (b"\0" if len(data) % 2 else b"")


def build_sf2(sdat, bank_index, used_programs=None):
    """An SF2 (bytes) for one SDAT bank: preset p (bank p // 128) = SBNK instrument p."""
    bank = sdat.banks[bank_index]
    instruments = parse_sbnk(sdat.file(bank["file"]))
    samples, sample_ids = [], {}           # (pcm list, rate, loop start, loop end, name)

    def sample_for(kind, swav, slot):
        key = (kind, swav, slot) if kind == 1 else (kind, swav if kind == 2 else 0)
        if key in sample_ids:
            return sample_ids[key]
        if kind == 1:
            arc = bank["swar"][slot] if slot < 4 else 0xFFFF
            if arc == 0xFFFF or arc >= len(sdat.swars):
                return None
            wavs = sdat.swar(arc)
            if swav >= len(wavs) or wavs[swav] is None:
                return None
            s = wavs[swav]
        elif kind == 2:
            s = psg_sample(swav)
        elif kind == 3:
            s = noise_sample()
        else:
            return None
        if not s[0]:
            return None
        sample_ids[key] = len(samples)
        samples.append(s + (f"s{len(samples)}",))
        return sample_ids[key]

    inst_zones = []                        # per instrument: [(lo, hi, sample id, generators)]
    for p, inst in enumerate(instruments):
        zones = []
        if inst and (used_programs is None or p in used_programs):
            for lo, hi, kind, swav, slot, note, a, dcy, sus, rel, pan in inst:
                sid = sample_for(kind, swav, slot)
                if sid is None:
                    continue
                atk, dec, sus_cb, rls = envelope(a, dcy, sus, rel)
                root = 69 if kind == 2 else (60 if kind == 3 else note)
                loop = samples[sid][2] is not None
                gens = [(43, lo | (hi << 8)), (34, atk), (36, dec), (37, sus_cb), (38, rls),
                        (17, int((pan - 64) / 64 * 500)), (58, root), (54, 1 if loop else 0)]
                zones.append((sid, gens))
        inst_zones.append(zones)

    if not any(inst_zones):
        raise ValueError("none of its instruments are in its bank (nothing to play)")
    # sample data (each followed by 46 zeros, as the format asks)
    smpl, shdr = bytearray(), bytearray()
    for i, (pcm, rate, ls, le, name) in enumerate(samples):
        start = len(smpl) // 2
        smpl += struct.pack(f"<{len(pcm)}h", *pcm) + b"\0" * 92
        end = start + len(pcm)
        lstart = start + (ls if ls is not None else 0)
        lend = start + (le if ls is not None else len(pcm))
        if ls is not None and lend - lstart < 2:
            lstart, lend = start, end
        shdr += struct.pack("<20sIIIIIBbHH", name.encode()[:20], start, end, lstart, lend, max(400, rate), 60, 0, 0, 1)
    shdr += struct.pack("<20sIIIIIBbHH", b"EOS", 0, 0, 0, 0, 0, 0, 0, 0, 0)

    inst, ibag, igen = bytearray(), bytearray(), bytearray()
    phdr, pbag, pgen = bytearray(), bytearray(), bytearray()
    ni = 0
    for p, zones in enumerate(inst_zones):
        if not zones:
            continue
        inst += struct.pack("<20sH", f"i{p}".encode(), len(ibag) // 4)
        for sid, gens in zones:
            ibag += struct.pack("<HH", len(igen) // 4, 0)
            for op, val in gens:                        # keyRange must come first; sampleID last
                igen += struct.pack("<Hh" if op != 43 else "<HH", op, val)
            igen += struct.pack("<HH", 53, sid)
        phdr += struct.pack("<20sHHHIII", f"p{p}".encode(), p % 128, p // 128, len(pbag) // 4, 0, 0, 0)
        pbag += struct.pack("<HH", len(pgen) // 4, 0)
        pgen += struct.pack("<HH", 41, ni)
        ni += 1
    inst += struct.pack("<20sH", b"EOI", len(ibag) // 4)
    ibag += struct.pack("<HH", len(igen) // 4, 0)
    igen += struct.pack("<HH", 0, 0)
    phdr += struct.pack("<20sHHHIII", b"EOP", 0, 0, len(pbag) // 4, 0, 0, 0)
    pbag += struct.pack("<HH", len(pgen) // 4, 0)
    pgen += struct.pack("<HH", 0, 0)
    mod = struct.pack("<HHhHH", 0, 0, 0, 0, 0)
    info = _chunk(b"ifil", struct.pack("<HH", 2, 1)) + _chunk(b"isng", b"EMU8000\0") + _chunk(b"INAM", b"DS bank\0")
    pdta = (_chunk(b"phdr", bytes(phdr)) + _chunk(b"pbag", bytes(pbag)) + _chunk(b"pmod", mod) +
            _chunk(b"pgen", bytes(pgen)) + _chunk(b"inst", bytes(inst)) + _chunk(b"ibag", bytes(ibag)) +
            _chunk(b"imod", mod) + _chunk(b"igen", bytes(igen)) + _chunk(b"shdr", bytes(shdr)))
    body = (b"sfbk" + _chunk(b"LIST", b"INFO" + info) + _chunk(b"LIST", b"sdta" + _chunk(b"smpl", bytes(smpl))) +
            _chunk(b"LIST", b"pdta" + pdta))
    return b"RIFF" + struct.pack("<I", len(body)) + body


# ------------------------------------------------------------------------------------------- SSEQ -> MIDI
def _varlen(d, p):
    v = 0
    while True:
        b = d[p]
        p += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, p


ARGS = {  # command -> argument bytes (fixed size); others handled below
    0xC0: 1, 0xC1: 1, 0xC2: 1, 0xC3: 1, 0xC4: 1, 0xC5: 1, 0xC6: 1, 0xC7: 1, 0xC8: 1, 0xC9: 1, 0xCA: 1, 0xCB: 1,
    0xCC: 1, 0xCD: 1, 0xCE: 1, 0xCF: 1, 0xD0: 1, 0xD1: 1, 0xD2: 1, 0xD3: 1, 0xD4: 1, 0xD5: 1, 0xD6: 1, 0xD7: 1,
    0xD8: 1, 0xE0: 2, 0xE1: 2, 0xE3: 2, 0xFC: 0, 0xFD: 0, 0xFE: 2, 0xFF: 0,
}


def sseq_to_midi(seq, master_vol=127, max_ticks=48 * 4 * 300):
    """A Type 1 MIDI file (bytes) from SSEQ data: plays once through, loops taken once."""
    if seq[:4] != b"SSEQ":
        raise ValueError("not an SSEQ")
    base = struct.unpack_from("<I", seq, 0x18)[0]
    d = seq[base:]
    tracks = {0: 0}
    events = {}                                       # track -> [(tick, order, bytes)]
    p = 0
    if d[0] == 0xFE:                                  # multitrack: the 0x93 "open track" commands follow
        p = 3
        while p < len(d) and d[p] == 0x93:
            t, off = d[p + 1], d[p + 2] | (d[p + 3] << 8) | (d[p + 4] << 16)
            tracks[t] = off
            p += 5
        tracks[0] = p
    end_tick = 0
    tempo_events = []
    for t, start in sorted(tracks.items()):
        ev = events.setdefault(t, [])
        ch = t if t < 9 else t + 1 if t < 15 else 15   # (keep clear of channel 10)
        ch = min(ch, 15)
        tick, p, order = 0, start, 0
        stack, loops, visited = [], [], set()
        notewait, transpose, tie, last_tie = True, 0, False, None

        def put(tk, data):
            nonlocal order
            ev.append((tk, order, bytes(data)))
            order += 1
        put(0, (0xB0 | ch, 101, 0)); put(0, (0xB0 | ch, 100, 0)); put(0, (0xB0 | ch, 6, 2))  # bend range 2
        put(0, (0xB0 | ch, 7, master_vol)); put(0, (0xB0 | ch, 10, 64)); put(0, (0xB0 | ch, 11, 127))
        steps = 0
        while p < len(d) and tick < max_ticks and steps < 200000:
            steps += 1
            cmd = d[p]
            p += 1
            cond = False
            if cmd == 0xA2:                            # "if": play the next command as if true
                cmd = d[p]
                p += 1
            if cmd < 0x80:                             # note
                vel = d[p]
                dur, p = _varlen(d, p + 1)
                key = max(0, min(127, cmd + transpose))
                if tie:
                    if last_tie is not None:
                        put(tick, (0x80 | ch, last_tie, 0))
                    put(tick, (0x90 | ch, key, max(1, vel)))
                    last_tie = key
                else:
                    put(tick, (0x90 | ch, key, max(1, vel)))
                    put(tick + max(1, dur), (0x80 | ch, key, 0))
                if notewait:
                    tick += dur
            elif cmd == 0x80:
                w, p = _varlen(d, p)
                tick += w
            elif cmd == 0x81:
                prg, p = _varlen(d, p)
                put(tick, (0xB0 | ch, 0, (prg >> 7) & 0x7F))
                put(tick, (0xC0 | ch, prg & 0x7F))
            elif cmd in (0x93,):
                p += 4
            elif cmd in (0x94, 0x95):                  # jump, call
                off = d[p] | (d[p + 1] << 8) | (d[p + 2] << 16)
                p += 3
                if cmd == 0x95:
                    stack.append(p)
                    p = off
                else:
                    if off <= p - 4 or off in visited:  # (jumping back: the song loops, so it's over)
                        break
                    visited.add(off)
                    p = off
            elif cmd == 0xA0:                          # random: cmd, its args but the last, min, max
                sub = d[p]
                p += 1
                n = 1 if sub < 0x80 else max(0, ARGS.get(sub, 1) - 1) if sub >= 0xB0 else 0
                if sub < 0x80:
                    vel = d[p]
                    lo, hi = struct.unpack_from("<hh", d, p + 1)
                    p += 5
                    dur = (lo + hi) // 2
                    put(tick, (0x90 | ch, sub, max(1, vel))); put(tick + max(1, dur), (0x80 | ch, sub, 0))
                    if notewait:
                        tick += max(0, dur)
                else:
                    p += n + 4 + (1 if 0xB0 <= sub <= 0xBD else 0)
            elif cmd == 0xA1:                          # variable: cmd, its args but the last, var number
                sub = d[p]
                p += 1
                p += (1 if sub < 0x80 else ARGS.get(sub, 1)) + (1 if 0xB0 <= sub <= 0xBD else 0)
            elif 0xB0 <= cmd <= 0xBD:
                p += 3
            elif cmd == 0xC0:
                put(tick, (0xB0 | ch, 10, d[p])); p += 1
            elif cmd == 0xC1:
                put(tick, (0xB0 | ch, 7, min(127, d[p] * master_vol // 127))); p += 1
            elif cmd == 0xC3:
                transpose = d[p] - 256 if d[p] > 127 else d[p]; p += 1
            elif cmd == 0xC4:
                v = d[p] - 256 if d[p] > 127 else d[p]; p += 1
                b = max(0, min(16383, 8192 + v * 64))
                put(tick, (0xE0 | ch, b & 0x7F, b >> 7))
            elif cmd == 0xC5:
                put(tick, (0xB0 | ch, 101, 0)); put(tick, (0xB0 | ch, 100, 0)); put(tick, (0xB0 | ch, 6, min(24, d[p]))); p += 1
            elif cmd == 0xC7:
                notewait = d[p] != 0; p += 1
            elif cmd == 0xC8:
                tie = d[p] != 0
                if not tie and last_tie is not None:
                    put(tick, (0x80 | ch, last_tie, 0)); last_tie = None
                p += 1
            elif cmd == 0xC9:
                put(tick, (0xB0 | ch, 84, max(0, min(127, d[p] + transpose)))); p += 1
            elif cmd == 0xCA:
                put(tick, (0xB0 | ch, 1, min(127, d[p]))); p += 1
            elif cmd == 0xCE:
                put(tick, (0xB0 | ch, 65, 127 if d[p] else 0)); p += 1
            elif cmd == 0xCF:
                put(tick, (0xB0 | ch, 5, min(127, d[p]))); p += 1
            elif cmd == 0xD4:                          # loop start (count; 0 = forever)
                loops.append([p + 1, d[p]]); p += 1
            elif cmd == 0xFC:                          # loop end
                if loops:
                    top = loops[-1]
                    if top[1] == 0:
                        break                          # (a forever loop: once through is the song)
                    top[1] -= 1
                    if top[1] > 0:
                        p = top[0]
                    else:
                        loops.pop()
            elif cmd == 0xD5:
                put(tick, (0xB0 | ch, 11, min(127, d[p]))); p += 1
            elif cmd == 0xE1:
                bpm = struct.unpack_from("<H", d, p)[0]; p += 2
                if bpm:
                    tempo_events.append((tick, bpm))
            elif cmd == 0xFD:                          # return
                if not stack:
                    break
                p = stack.pop()
            elif cmd == 0xFF:
                break
            elif cmd in ARGS:
                p += ARGS[cmd]
            else:
                break                                  # (an unknown command: stop this track)
        if last_tie is not None:
            put(tick, (0x80 | ch, last_tie, 0))
        end_tick = max(end_tick, tick, max((e[0] for e in ev), default=0))

    def vlq(n):
        out = [n & 0x7F]
        n >>= 7
        while n:
            out.insert(0, 0x80 | (n & 0x7F))
            n >>= 7
        return bytes(out)

    def track_chunk(evs):
        evs = sorted(evs, key=lambda e: (e[0], e[1]))
        out, last = bytearray(), 0
        for tk, _o, data in evs:
            out += vlq(tk - last) + data
            last = tk
        out += vlq(max(0, end_tick - last)) + b"\xFF\x2F\x00"
        return b"MTrk" + struct.pack(">I", len(out)) + bytes(out)

    conductor = [(0, -1, b"\xFF\x51\x03" + struct.pack(">I", 500000)[1:])]
    seen = set()
    for tk, bpm in sorted(tempo_events):
        if (tk, bpm) in seen:
            continue
        seen.add((tk, bpm))
        conductor.append((tk, 0, b"\xFF\x51\x03" + struct.pack(">I", int(60000000 / bpm))[1:]))
    chunks = [track_chunk(conductor)] + [track_chunk(evs) for _t, evs in sorted(events.items())]
    return b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), 48) + b"".join(chunks), end_tick


def programs_used(midi_bytes):
    """Program numbers (bank*128 + program) a MIDI file asks for."""
    out, p = set(), 14
    banks = {}
    d = midi_bytes
    while p < len(d) and d[p:p + 4] == b"MTrk":
        n = struct.unpack_from(">I", d, p + 4)[0]
        q, end, run = p + 8, p + 8 + n, 0
        while q < end:
            while d[q] & 0x80:
                q += 1
            q += 1
            st = d[q]
            if st == 0xFF:
                ln = d[q + 2]
                q += 3 + ln
                continue
            q += 1
            if st & 0xF0 == 0xB0 and d[q] == 0:
                banks[st & 0xF] = d[q + 1]
            if st & 0xF0 == 0xC0:
                out.add(banks.get(st & 0xF, 0) * 128 + d[q])
                q += 1
            elif st & 0xF0 in (0x80, 0x90, 0xB0, 0xE0, 0xA0):
                q += 2
            else:
                q += 1
        p = end
    return out


def sdat_of(rom_path):
    """[(path in ROM, SDAT)] for every .sdat file in a .nds game file."""
    out = []
    for path, (off, size) in sorted(nitro_files(rom_path).items()):
        if path.lower().endswith(".sdat"):
            data = read_part(rom_path, off, size)
            try:
                out.append((path, SDAT(data)))
            except (ValueError, struct.error):
                pass
    return out


def convert(sdat, i, folder, stem):
    """SEQ i -> folder/stem.mid + folder/stem.sf2. Returns the MIDI's length in ticks."""
    s = sdat.seqs[i]
    midi, ticks = sseq_to_midi(sdat.file(s["file"]), s["vol"])
    sf2 = build_sf2(sdat, s["bank"], programs_used(midi))
    with open(os.path.join(folder, stem + ".mid"), "wb") as f:
        f.write(midi)
    with open(os.path.join(folder, stem + ".sf2"), "wb") as f:
        f.write(sf2)
    return ticks


if __name__ == "__main__":
    if sys.argv[1] == "list":
        for path, sd in sdat_of(sys.argv[2]):
            names = [sd.seq_name(i) for i, s in enumerate(sd.seqs) if s]
            print(path, len(names), "sequences:", " ".join(names))
    elif sys.argv[1] == "one":
        for path, sd in sdat_of(sys.argv[2]):
            for i, s in enumerate(sd.seqs):
                if s and sd.seq_name(i) == sys.argv[3]:
                    print(convert(sd, i, sys.argv[4], sys.argv[3]), "ticks")
