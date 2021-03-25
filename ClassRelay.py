class relay:
    "Model of a relay with hysteresis"
    #Confronta un valore con una soglia con isteresi e ritorna 0=stato OFF oppure 1=stato ON
    #I valori sono tutti assoluti, compreso quelle dei delta che definiscono l'isteresi (asimmetrica perché deltapos e deltaneg sono definiti separatamente)
    #Attenzione: deltaneg deve essere negativo. Tuttavia non vengono imposti controlli di errore
    def __init__(self, treshold=0, deltapos=0, deltaneg=0):
        self.status=0
        self.treshold=treshold
        self.deltapos=deltapos
        self.deltaneg=deltaneg
    def trigger(self, value):
        if value<self.treshold+self.deltaneg: 
            self.status=0
            return 0
        if value<self.treshold+self.deltapos and self.status==0: 
            self.status=0
            return 0
        if value<self.treshold+self.deltapos and self.status==1: 
            self.status=1
            return 1
        if value>self.treshold+self.deltapos: 
            self.status=1
            return 1