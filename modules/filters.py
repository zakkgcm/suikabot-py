import string
import random

class TrollOutputFilter:
    self.currentTroll = 1
    self.trollCounter = 0
    self.trolls = [
        #aradia
        lambda x: x.translate(string.maketrans('oO', '00')),
        #terezi
        lambda x: x.upper().translate(string.maketrans('AIE', '413')),
        #tavros
        lambda x: x.title().swapcase(),
        #sollux
        lambda x: x.replace('s', '2').replace('S', '2').replace('i', 'ii').replace('I', 'II'),
        #karkat
        lambda x: x.upper(),
        #nepeta
        lambda x: x.replace('ee', '33').replace('EE', '33'),
        #kanaya
        lambda x: x.title(),
        #vriska
        lambda x: x.translate(string.maketrans('bB', '88')).replace('ate', '8'),
        #equius
        lambda x: 'D -->' + x.translate(string.maketrans('xX', '%%')),
        #gamzee TODO need a full func
        #eridan
        lambda x: x.replace('w', 'ww').replace('v', 'vv').replace('W', 'WW').replace('V', 'VV'),
        #feferi
        lambda x: x.replace('h', ')(').replace('H', ')(').replace('E', '-E'),
    ]

    def transform(self, message):
        self.trollCounter += 1
        if (self.trollCounter > random.randint(6, 12))
            self.currentTroll = random.randint(0, 10)
            self.trollCounter = 0
        
        def trollUnlessURL(x):
            if !x.startswith(('http://', 'https://', 'ftp://')):
                return self.trolls[self.currentTroll](x)

            return x

       return map(trollUnlessURL, message.split()).join(' ')
