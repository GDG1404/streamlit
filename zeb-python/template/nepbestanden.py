# Tekstbestanden in het geheugen, zodat oefeningen met open() overal werken:
# in build.py (gewone Python) en in de browser (Brython).
# Dezelfde code wordt op beide plaatsen gebruikt.


class NepBestand:
    def __init__(self, fs, naam, mode):
        self.fs = fs
        self.naam = naam
        self.mode = mode
        self.gesloten = False
        self.pos = 0
        if "r" in mode and "+" not in mode:
            if naam not in fs:
                raise FileNotFoundError("[Errno 2] No such file or directory: '" + str(naam) + "'")
            self.leesbaar = True
            self.schrijfbaar = False
        elif "w" in mode:
            fs[naam] = ""
            self.leesbaar = False
            self.schrijfbaar = True
        elif "a" in mode:
            if naam not in fs:
                fs[naam] = ""
            self.leesbaar = False
            self.schrijfbaar = True
        else:
            raise ValueError("invalid mode: '" + str(mode) + "'")

    def _controleer(self, lezen):
        if self.gesloten:
            raise ValueError("I/O operation on closed file.")
        if lezen and not self.leesbaar:
            raise OSError("not readable")
        if not lezen and not self.schrijfbaar:
            raise OSError("not writable")

    def read(self, n=-1):
        self._controleer(True)
        data = self.fs[self.naam]
        if n is None or n < 0:
            stuk = data[self.pos:]
        else:
            stuk = data[self.pos:self.pos + n]
        self.pos += len(stuk)
        return stuk

    def readline(self):
        self._controleer(True)
        data = self.fs[self.naam]
        i = data.find("\n", self.pos)
        einde = len(data) if i < 0 else i + 1
        stuk = data[self.pos:einde]
        self.pos = einde
        return stuk

    def readlines(self):
        regels = []
        while True:
            r = self.readline()
            if r == "":
                return regels
            regels.append(r)

    def __iter__(self):
        return iter(self.readlines())

    def write(self, s):
        self._controleer(False)
        if not isinstance(s, str):
            raise TypeError("write() argument must be str, not " + type(s).__name__)
        self.fs[self.naam] = self.fs[self.naam] + s
        return len(s)

    def writelines(self, regels):
        for r in regels:
            self.write(r)

    def close(self):
        self.gesloten = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False


def maak_open(fs):
    def nep_open(naam, mode="r", encoding=None, **andere):
        return NepBestand(fs, naam, mode)

    return nep_open


def geeft_fout(f, *args):
    """Hulpje voor tests: welke exception geeft f(*args)? None als er geen is."""
    try:
        f(*args)
    except Exception as e:
        return type(e).__name__
    return None
