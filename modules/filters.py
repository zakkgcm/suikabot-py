import string
import random
import datetime

class TrollOutputFilter:
    def __init__(self): 
        self.currentTroll = random.randint(0, 10)
        self.trollCounter = 0
        self.trolls = [
            #aradia
            { 'prefix': '', 'replace': lambda x: x.translate(string.maketrans('oo', '00')) },
            #terezi
            { 'prefix': '', 'replace': lambda x: x.upper().translate(string.maketrans('AIE', '413')) },
            #tavros
            { 'prefix': '', 'replace': lambda x: x.title().swapcase() },
            #sollux
            { 'prefix': '', 'replace': lambda x: x.replace('s', '2').replace('S', '2').replace('i', 'ii').replace('I', 'II') },
            #karkat
            { 'prefix': '', 'replace': lambda x: x.upper() },
            #nepeta
            { 'prefix': ':33 <', 'replace': lambda x: x.replace('ee', '33').replace('EE', '33') },
            #kanaya
            { 'prefix': '', 'replace': lambda x: x.capitalize() },
            #vriska
            { 'prefix': '', 'replace': lambda x: x.translate(string.maketrans('bB', '88')).replace('ate', '8') },
            #equius
            { 'prefix': 'D -->', 'replace': lambda x: x.translate(string.maketrans('xX', '%%')) },
            #gamzee TODO need a full func
            #eridan
            { 'prefix': '', 'replace': lambda x: x.replace('w', 'ww').replace('v', 'vv').replace('W', 'WW').replace('V', 'VV') },
            #feferi
            { 'prefix': '', 'replace': lambda x: x.replace('h', ')(').replace('H', ')(').replace('E', '-E') },
        ]

    def transform(self, message):
        d = datetime.date.today()
        if (d.month != 4 or d.day != 13):
            return message

        self.trollCounter += 1
        if (self.trollCounter > random.randint(6, 12)):
            self.currentTroll = random.randint(0, 10)
            self.trollCounter = 0
        
        def trollUnlessURL(x):
            if not x.startswith(('http://', 'https://', 'ftp://')):
                return self.trolls[self.currentTroll]['replace'](x)
            
            return x
        
        return self.trolls[self.currentTroll]['prefix'] + ' '.join(map(trollUnlessURL, message.split()))
