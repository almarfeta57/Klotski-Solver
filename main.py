import copy
import os
import sys
import time
import stopit

class NodParcurgere:
    def __init__(self, info, parinte, cost=0, h=0, mutare = ""):
        self.info = info    # Informatia dintr-un nod al grafului (o matrice de caractere ce reprezinta tabla de joc)
        self.parinte = parinte  # parintele din arborele de parcurgere
        self.g = cost  # consider cost=1 pentru piesa speciala, iar pentru restul cost=dimenisunea piesei
        self.h = h  # Valoarea data de euristica
        self.f = self.g + self.h    # Suma dintre cost si euristica
        self.mutare = mutare    # Retine cum s-a ajuns la starea curenta (daca s-a facut o mutare la stanga, sus, jos, dreapta)


    def obtineDrum(self):   # O functie ce returneaza drumul de la un nod dat la radacina arborelui
        l = [self]
        nod = self
        while nod.parinte is not None:
            l.insert(0, nod.parinte)
            nod = nod.parinte
        return l


    def afisDrum(self, g, afisCost=False, afisLung=False):  # Afiseaza drumul
        l = self.obtineDrum()
        for i, nod in enumerate(l):
            g.write(str(i + 1) + ")\n" + nod.mutare + "\n" + str(nod))
        if afisCost:
            g.write("Cost: " + str(self.g) + "\n")
        if afisLung:
            g.write("Lungime: " + str(len(l)) + "\n")
        return len(l)


    def contineInDrum(self, infoNodNou):    # O functie care verifica daca un nod nou se afla deja in arbore
        nodDrum = self
        while nodDrum is not None:
            if infoNodNou == nodDrum.info:
                return True
            nodDrum = nodDrum.parinte

        return False


    def __repr__(self):
        sir = ""
        sir += str(self.info)
        return sir


    def __str__(self):
        sir = ""
        for linie in self.info:
            sir += " ".join([str(elem) for elem in linie]) + "\n"
        sir += "\n"
        return sir



class Graph:
    def __init__(self, nume_fisier):
        def verificare(nodStart):   # Functie de verificare a datelor de intrare
            if len(nodStart) == 1 and len(nodStart[0]) == 0:    # Verifica mai intai daca lista data e goala
                return False
            ok = 0
            for elem in nodStart[0]:    # Verifica daca prima linie contine o singura iesire si restul ziduri
                if ok == 0 and elem != '#':
                    ok = 1
                elif ok == 1 and elem == '#':
                    ok = 2
                elif ok == 2 and elem != '#':
                    return False
            if ok == 0:
                return False
            for i in range(len(nodStart)):  # Verificam daca zidurile se afla unde trebuie
                if nodStart[i][0] != '#' or nodStart[i][len(nodStart[0])-1] != '#':
                    return False
            for elem in nodStart[len(nodStart)-1]:
                if elem != '#':
                    return False
            for linie in nodStart:  # In final verificam daca datele de intrare contin doar caractere admise
                for elem in linie:
                    if not (elem.isalnum() == True or elem == '.' or elem == '#' or elem == '*'):
                        return False
            return True


        f = open(nume_fisier, "r")
        sirFisier = f.read()
        try:
            listaLinii = sirFisier.strip().split("\n")
            self.start = []
            self.piese = set()
            for linie in listaLinii:
                for elem in linie.strip():
                    if elem != '.' and elem != '#':
                        self.piese.add(elem)    # Adaugam fiecare piesa intr-un set, pentru a nu exista dubluri
                self.start.append([str(x) for x in linie.strip()])  # In start vom avea matricea de caractere data
            if verificare(self.start) == False: # Verificam daca informatia data este corecta
                print("Date de intrare gresite")
                sys.exit(0)
            print(self.start)
        except:
            print("Eroare la parsare!")
            sys.exit(0)


    def testeaza_scop(self, infoNod):   # O functie care testeaza daca nodul dat contine o configuratie finala
        for i in range(len(infoNod)):
            for j in range(len(infoNod[i])):
                if infoNod[i][j] == '*':    # Verific daca mai exista piesa speciala in matrice
                    return False
        return True


    def nuAreSolutii(self, infoNod):    # O functie care verifica daca inputul are solutii
        gap = 0
        for caracter in infoNod[0]:
            if caracter != '#':
                gap += 1    # Calculam dimensiunea iesirii

        nrmaxStar = 0
        iStarMax = -1
        for i in range(len(infoNod)):
            nrStar = 0
            for j in range(len(infoNod[i])):
                if infoNod[i][j] == '*':
                    nrStar += 1
            if nrStar > nrmaxStar:  # Calculam numarul maxim de stelute de pe o linie
                nrmaxStar = nrStar
                iStarMax = i

        nrPiesaMax = 0
        for i in range(iStarMax):   # Determinam lungimea celei mai mari piese
            caracterAnte = ''
            nrPiesa = 0
            for j in range(len(infoNod[i])):
                if infoNod[i][j] != '#' and infoNod[i][j] != '.' and infoNod[i][j] != '*':
                    if infoNod[i][j] != caracterAnte:
                        if nrPiesa > nrPiesaMax:
                            nrPiesaMax = nrPiesa
                        nrPiesa = 1
                        caracterAnte = infoNod[i][j]
                    else:
                        nrPiesa += 1
            if nrPiesa > nrPiesaMax:
                nrPiesaMax = nrPiesa

        if nrmaxStar > gap: # Daca lungimea piesei speciale este mai mare decat cea a iesirii, nu putem avea solutii
            return True
        if nrmaxStar + nrPiesaMax > len(infoNod[0]) - 2: # Nu avem solutii nici daca avem o piesa prea mare, care blocheaza iesirea
            return True
        return False


    def genereazaSuccesori(self, nodCurent, tip_euristica="euristica banala"):  # Returneaza lista de succesori a unui nod
        # Luam fiecare piesa in parte, o cautam in matrice si verificam mai intai daca putem muta acea
        #piesa sus, jos, stanga sau dreapta. Apoi, daca piesa se poate muta, creeam o copie a matricei
        #in care vom muta efectiv piesa selectata si ii calculam costul.
        listaSuccesori = []
        for elem in self.piese:
            mutaSus = True
            mutaJos = True
            mutaSt = True
            mutaDr = True
            for i in range(len(nodCurent.info)):
                for j in range(len(nodCurent.info[i])):
                    if nodCurent.info[i][j] == elem:
                        if mutaSus == True and \
                                not (i-1 >= 0 and (nodCurent.info[i-1][j] == '.' or nodCurent.info[i-1][j] == elem)):
                            if elem == '*' and i-1 < 0:
                                pass
                            else:
                                mutaSus = False
                        if mutaSt == True and \
                                not (j-1 >= 0 and (nodCurent.info[i][j-1] == '.' or nodCurent.info[i][j-1] == elem)):
                            mutaSt = False
                        if mutaJos == True and \
                                not (i+1 < len(nodCurent.info) and (nodCurent.info[i+1][j] == '.' or nodCurent.info[i+1][j] == elem)):
                            mutaJos = False
                        if mutaDr == True and \
                                not (j+1 < len(nodCurent.info[i]) and (nodCurent.info[i][j+1] == '.' or nodCurent.info[i][j+1] == elem)):
                            mutaDr = False
            if mutaSus == True:
                cost = 0
                copieMatrice = copy.deepcopy(nodCurent.info)
                for i in range(len(nodCurent.info)):
                    for j in range(len(nodCurent.info[i])):
                        if copieMatrice[i][j] == elem:
                            cost += 1
                            if elem == '*' and i-1 < 0:
                                copieMatrice[i][j] = '.'
                            else:
                                copieMatrice[i][j], copieMatrice[i-1][j] = copieMatrice[i-1][j], copieMatrice[i][j]
                if not nodCurent.contineInDrum(copieMatrice):
                    if elem == '*':
                        cost = 1
                    listaSuccesori.append(NodParcurgere(copieMatrice, nodCurent, nodCurent.g + cost,
                                                        self.calculeaza_h(copieMatrice, tip_euristica), "Mutam {} in sus".format(elem)))
            if mutaJos == True:
                cost = 0
                copieMatrice = copy.deepcopy(nodCurent.info)
                for i in range(len(nodCurent.info)-1, -1, -1):
                    for j in range(len(nodCurent.info[i])):
                        if copieMatrice[i][j] == elem:
                            cost += 1
                            copieMatrice[i][j], copieMatrice[i+1][j] = copieMatrice[i+1][j], copieMatrice[i][j]
                if not nodCurent.contineInDrum(copieMatrice):
                    if elem == '*':
                        cost = 1
                    listaSuccesori.append(NodParcurgere(copieMatrice, nodCurent, nodCurent.g + cost,
                                                        self.calculeaza_h(copieMatrice, tip_euristica), "Mutam {} in jos".format(elem)))
            if mutaSt == True:
                cost = 0
                copieMatrice = copy.deepcopy(nodCurent.info)
                for i in range(len(nodCurent.info)):
                    for j in range(len(nodCurent.info[i])):
                        if copieMatrice[i][j] == elem:
                            cost += 1
                            copieMatrice[i][j], copieMatrice[i][j-1] = copieMatrice[i][j-1], copieMatrice[i][j]
                if not nodCurent.contineInDrum(copieMatrice):
                    if elem == '*':
                        cost = 1
                    listaSuccesori.append(NodParcurgere(copieMatrice, nodCurent, nodCurent.g + cost,
                                                        self.calculeaza_h(copieMatrice, tip_euristica), "Mutam {} in stanga".format(elem)))
            if mutaDr == True:
                cost = 0
                copieMatrice = copy.deepcopy(nodCurent.info)
                for i in range(len(nodCurent.info)):
                    for j in range(len(nodCurent.info[i])-1, -1, -1):
                        if copieMatrice[i][j] == elem:
                            cost += 1
                            copieMatrice[i][j], copieMatrice[i][j+1] = copieMatrice[i][j+1], copieMatrice[i][j]
                if not nodCurent.contineInDrum(copieMatrice):
                    if elem == '*':
                        cost = 1
                    listaSuccesori.append(NodParcurgere(copieMatrice, nodCurent, nodCurent.g + cost,
                                                        self.calculeaza_h(copieMatrice, tip_euristica), "Mutam {} in dreapta".format(elem)))

        return listaSuccesori


    def calculeaza_h(self, infoNod, tip_euristica="euristica banala"):  # Functia de calculare a euristicii
        if self.testeaza_scop(infoNod):
            return 0
        if tip_euristica == "euristica banala": # Returneaza 1 daca nu e stare finala si 0 daca este
            return 1
        elif tip_euristica == "euristica 1":    # Calculam numarul de linii de la iesire pana la piesa speciala
            for i in range(len(infoNod)):
                for j in range(len(infoNod[i])):
                    if infoNod[i][j] == '*':
                        return i
        elif tip_euristica == "euristica 2":    # Calculam distanta manhattan de la iesire pana la piesa speciala
            jGap = -1
            for j in range(len(infoNod[0])):
                if infoNod[0][j] != '#':
                    jGap = j
            for i in range(len(infoNod)):
                for j in range(len(infoNod[i])):
                    if infoNod[i][j] == '*':
                        return i + abs(jGap - j)
        elif tip_euristica == "euristica neadmisibila":
            nr = 0  # Returneaza numarul de caractere (piese) din jurul piesei speciale
            for i in range(len(infoNod)):
                for j in range(len(infoNod[i])):
                    if infoNod[i][j] == '*':
                        if i-1 >= 0 and infoNod[i-1][j] != '.' and infoNod[i-1][j] != '#' and infoNod[i-1][j] != '*':
                            nr += 1
                        if infoNod[i+1][j] != '.' and infoNod[i+1][j] != '#' and infoNod[i+1][j] != '*':
                            nr += 1
                        if infoNod[i][j-1] != '.' and infoNod[i][j-1] != '#' and infoNod[i][j-1] != '*':
                            nr += 1
                        if infoNod[i][j+1] != '.' and infoNod[i][j+1] != '#' and infoNod[i][j+1] != '*':
                            nr += 1
            return nr



    def __repr__(self):
        sir = ""
        for (k, v) in self.__dict__.items():
            sir += "{} = {}\n".format(k, v)
        return (sir)


@stopit.threading_timeoutable(default="Functia a intrat in timeout")
def breadth_first(g, gr, nrSolutiiCautate):
    if gr.nuAreSolutii(gr.start):
        g.write("Nu are solutii\n")
        return "Functie finalizata"

    c = [NodParcurgere(gr.start, None)]
    max_noduri_memorie = 1
    noduri_calculate = 1

    while len(c) > 0:
        nodCurent = c.pop(0)

        if gr.testeaza_scop(nodCurent.info):
            g.write("Solutie: \n")
            nodCurent.afisDrum(g, afisCost=True, afisLung=True)
            g.write(str(time.time() - t1) + "secunde\n")
            g.write("Numarul maxim de noduri aflate in memorie: " + str(max_noduri_memorie) + "\n")
            g.write("Numarul total de noduri calculate: " + str(noduri_calculate) + "\n")
            g.write("\n----------------\n")
            nrSolutiiCautate -= 1
            if nrSolutiiCautate == 0:
                return "Functie finalizata"
        lSuccesori = gr.genereazaSuccesori(nodCurent)
        noduri_calculate += len(lSuccesori)
        c.extend(lSuccesori)
        if len(c) > max_noduri_memorie:
            max_noduri_memorie = len(c)

    g.write("Nu are solutii\n")
    return "Functie finalizata"


@stopit.threading_timeoutable(default="Functia a intrat in timeout")
def depth_first(g, gr, nrSolutiiCautate=1):
    if gr.nuAreSolutii(gr.start):
        g.write("Nu are solutii\n")
        return "Functie finalizata"

    noduri_calculate = 1
    nrSolutiiCautate, max_noduri_memorie, noduri_calculate =\
        df(g, NodParcurgere(gr.start, None), nrSolutiiCautate, 1, noduri_calculate)
    return "Functie finalizata"

def df(g, nodCurent, nrSolutiiCautate, max_noduri_memorie, noduri_calculate):
    if nrSolutiiCautate <= 0:
        return nrSolutiiCautate, max_noduri_memorie, noduri_calculate
    if gr.testeaza_scop(nodCurent.info):
        g.write("Solutie: \n")
        nodCurent.afisDrum(g, afisCost=True, afisLung=True)
        g.write(str(time.time() - t1) + "secunde\n")
        g.write("Numarul maxim de noduri aflate in memorie: " + str(max_noduri_memorie) + "\n")
        g.write("Numarul total de noduri calculate: " + str(noduri_calculate) + "\n")
        g.write("\n----------------\n")
        nrSolutiiCautate -= 1
        if nrSolutiiCautate == 0:
            return nrSolutiiCautate, max_noduri_memorie, noduri_calculate
    lSuccesori = gr.genereazaSuccesori(nodCurent)
    max_noduri_memorie += len(lSuccesori)
    noduri_calculate += len(lSuccesori)
    for sc in lSuccesori:
        if nrSolutiiCautate != 0:
            nrSolutiiCautate, max_noduri_nou, noduri_calculate = df(g, sc, nrSolutiiCautate, max_noduri_memorie, noduri_calculate)
        if max_noduri_nou > max_noduri_memorie:
            max_noduri_memorie = max_noduri_nou
    return nrSolutiiCautate, max_noduri_memorie, noduri_calculate


@stopit.threading_timeoutable(default="Functia a intrat in timeout")
def depth_first_iterativ(g, gr, nrSolutiiCautate=1):
    if gr.nuAreSolutii(gr.start):
        g.write("Nu are solutii\n")
        return "Functie finalizata"
    i = 1
    noduri_calculate = 1
    while nrSolutiiCautate != 0:
        nrSolutiiCautate, max_noduri_memorie, noduri_calculate =\
            dfi(g, NodParcurgere(gr.start, None), i, nrSolutiiCautate, 1, noduri_calculate)
        i += 1
    return "Functie finalizata"

def dfi(g, nodCurent, adancime, nrSolutiiCautate, max_noduri_memorie, noduri_calculate):
    if adancime == 1 and gr.testeaza_scop(nodCurent.info):
        g.write("Solutie: \n")
        nodCurent.afisDrum(g, afisCost=True, afisLung=True)
        g.write(str(time.time() - t1) + "secunde\n")
        g.write("Numarul maxim de noduri aflate in memorie: " + str(max_noduri_memorie) + "\n")
        g.write("Numarul total de noduri calculate: " + str(noduri_calculate) + "\n")
        g.write("\n----------------\n")
        nrSolutiiCautate -= 1
        if nrSolutiiCautate == 0:
            return nrSolutiiCautate, max_noduri_memorie, noduri_calculate
    if adancime > 1:
        lSuccesori = gr.genereazaSuccesori(nodCurent)
        max_noduri_memorie += len(lSuccesori)
        noduri_calculate += len(lSuccesori)
        for sc in lSuccesori:
            if nrSolutiiCautate != 0:
                nrSolutiiCautate, max_noduri_nou, noduri_calculate = \
                    dfi(g, sc, adancime - 1, nrSolutiiCautate, max_noduri_memorie, noduri_calculate)
            if max_noduri_nou > max_noduri_memorie:
                max_noduri_memorie = max_noduri_nou
    return nrSolutiiCautate, max_noduri_memorie, noduri_calculate


@stopit.threading_timeoutable(default="Functia a intrat in timeout")
def a_star(g, gr, nrSolutiiCautate, tip_euristica):

    if gr.nuAreSolutii(gr.start):
        g.write("Nu are solutii\n")
        return "Functie finalizata"

    c = [NodParcurgere(gr.start, None, 0, gr.calculeaza_h(gr.start, tip_euristica))]
    max_noduri_memorie = 1
    noduri_calculate = 1

    while len(c) > 0:
        nodCurent = c.pop(0)

        if gr.testeaza_scop(nodCurent.info):
            g.write("Solutie: \n")
            nodCurent.afisDrum(g, afisCost=True, afisLung=True)
            g.write(str(time.time() - t1) + "secunde\n")
            g.write("Numarul maxim de noduri aflate in memorie: " + str(max_noduri_memorie) + "\n")
            g.write("Numarul total de noduri calculate: " + str(noduri_calculate) + "\n")
            g.write("\n----------------\n")
            nrSolutiiCautate -= 1
            if nrSolutiiCautate == 0:
                return "Functie finalizata"
        lSuccesori = gr.genereazaSuccesori(nodCurent, tip_euristica=tip_euristica)
        noduri_calculate += len(lSuccesori)
        for s in lSuccesori:
            i = 0
            gasit_loc = False
            for i in range(len(c)):
                if c[i].f >= s.f:
                    gasit_loc = True
                    break
            if gasit_loc:
                c.insert(i, s)
            else:
                c.append(s)
        if len(c) > max_noduri_memorie:
            max_noduri_memorie = len(c)

    g.write("Nu are solutii\n")
    return "Functie finalizata"


@stopit.threading_timeoutable(default="Functia a intrat in timeout")
def a_star_opt(g, gr, tip_euristica):
    if gr.nuAreSolutii(gr.start):
        g.write("Nu are solutii\n")
        return "Functie finalizata"

    # l_open contine nodurile candidate pentru expandare (este echivalentul lui c din A* varianta neoptimizata)
    # l_closed contine nodurile expandate
    l_open = [NodParcurgere(gr.start, None, 0, gr.calculeaza_h(gr.start, tip_euristica))]
    l_closed = []
    max_noduri_memorie = 1
    noduri_calculate = 1

    while len(l_open) > 0:
        nodCurent = l_open.pop(0)
        l_closed.append(nodCurent)

        if gr.testeaza_scop(nodCurent.info):
            g.write("Solutie: \n")
            nodCurent.afisDrum(g, afisCost=True, afisLung=True)
            g.write(str(time.time() - t1) + "secunde\n")
            g.write("Numarul maxim de noduri aflate in memorie: " + str(max_noduri_memorie) + "\n")
            g.write("Numarul total de noduri calculate: " + str(noduri_calculate) + "\n")
            g.write("\n----------------\n")
            return "Functie finalizata"
        lSuccesori = gr.genereazaSuccesori(nodCurent, tip_euristica)
        noduri_calculate += len(lSuccesori)
        for s in lSuccesori:
            gasitC = False
            for nodC in l_open:
                if s.info == nodC.info:
                    gasitC = True
                    if s.f >= nodC.f:
                        lSuccesori.remove(s)
                    else:  # s.f<nodC.f
                        l_open.remove(nodC)
                    break
            if not gasitC:
                for nodC in l_closed:
                    if s.info == nodC.info:
                        if s.f >= nodC.f:
                            lSuccesori.remove(s)
                        else:  # s.f<nodC.f
                            l_closed.remove(nodC)
                        break
        for s in lSuccesori:
            i = 0
            gasit_loc = False
            for i in range(len(l_open)):
                # diferenta fata de UCS e ca ordonez crescator dupa f
                # daca f-urile sunt egale ordonez descrescator dupa g
                if l_open[i].f > s.f or (l_open[i].f == s.f and l_open[i].g <= s.g):
                    gasit_loc = True
                    break
            if gasit_loc:
                l_open.insert(i, s)
            else:
                l_open.append(s)
        if len(l_open) + len(l_closed) > max_noduri_memorie:
            max_noduri_memorie = len(l_open) + len(l_closed)

    g.write("Nu are solutii\n")
    return "Functie finalizata"


@stopit.threading_timeoutable(default="Functia a intrat in timeout")
def ida_star(g, gr, nrSolutiiCautate, tip_euristica):
    if gr.nuAreSolutii(gr.start):
        g.write("Nu are solutii\n")
        return "Functie finalizata"

    nodStart = NodParcurgere(gr.start, None, 0, gr.calculeaza_h(gr.start, tip_euristica))
    limita = nodStart.f
    noduri_calculate = 1
    while True:
        nrSolutiiCautate, rez, max_noduri_memorie, noduri_calculate =\
            construieste_drum(g, gr, nodStart, limita, nrSolutiiCautate, tip_euristica, 1, noduri_calculate)
        if rez == "gata":
            break
        if rez == float('inf'):
            g.write("Nu mai exista solutii!\n")
            break
        limita = rez
    return "Functie finalizata"

def construieste_drum(g, gr, nodCurent, limita, nrSolutiiCautate, tip_euristica, max_noduri_memorie, noduri_calculate):
    if nodCurent.f > limita:
        return nrSolutiiCautate, nodCurent.f, max_noduri_memorie, noduri_calculate
    if gr.testeaza_scop(nodCurent.info) and nodCurent.f == limita:
        g.write("Solutie: \n")
        nodCurent.afisDrum(g, afisCost=True, afisLung=True)
        g.write(str(time.time() - t1) + "secunde\n")
        g.write("Numarul maxim de noduri aflate in memorie: " + str(max_noduri_memorie) + "\n")
        g.write("Numarul total de noduri calculate: " + str(noduri_calculate) + "\n")
        g.write("\n----------------\n")
        nrSolutiiCautate -= 1
        if nrSolutiiCautate == 0:
            return 0, "gata", max_noduri_memorie, noduri_calculate
    lSuccesori = gr.genereazaSuccesori(nodCurent, tip_euristica)
    max_noduri_memorie += len(lSuccesori)
    noduri_calculate += len(lSuccesori)
    minim = float('inf')
    for s in lSuccesori:
        nrSolutiiCautate, rez, max_noduri_nou, noduri_calculate =\
            construieste_drum(g, gr, s, limita, nrSolutiiCautate, tip_euristica, max_noduri_memorie, noduri_calculate)
        if rez == "gata":
            return 0, "gata", max_noduri_memorie, noduri_calculate
        if rez < minim:
            minim = rez
        if max_noduri_nou > max_noduri_memorie:
            max_noduri_memorie = max_noduri_nou
    return nrSolutiiCautate, minim, max_noduri_memorie, noduri_calculate




# sys.argv[0] -> numele fisierului executat
# sys.argv[1] -> numele folderului de input
# sys.argv[2] -> numele folderului de output
# sys.argv[3] -> numarul de solutii
# sys.argv[4] -> o valoare pentru timeout

if not os.path.exists(sys.argv[2]): # Daca nu exista fisier de iesire il creez
    os.mkdir(sys.argv[2])
for numeFisier in os.listdir(sys.argv[1]):  # Iau fiecare input
    gr = Graph(sys.argv[1] + "/" + numeFisier)  # Construiesc graful

    numeFisierOutput = "output_BF_" + numeFisier
    g = open(sys.argv[2] + "/" + numeFisierOutput, "w")
    g.write("BF\n\n")
    t1 = time.time()
    rez = breadth_first(g, gr, nrSolutiiCautate=int(sys.argv[3]), timeout=int(sys.argv[4]))
    print("BF: " + rez)
    g.write(rez + "\n")
    g.write("==========================================\n")
    g.close()

    numeFisierOutput = "output_DF_" + numeFisier
    g = open(sys.argv[2] + "/" + numeFisierOutput, "w")
    g.write("DF\n\n")
    t1 = time.time()
    rez = depth_first(g, gr, nrSolutiiCautate=int(sys.argv[3]), timeout=int(sys.argv[4]))
    print("DF: " + rez)
    g.write(rez + "\n")
    g.write("==========================================\n")
    g.close()

    numeFisierOutput = "output_DFI_" + numeFisier
    g = open(sys.argv[2] + "/" + numeFisierOutput, "w")
    g.write("DFI\n\n")
    t1 = time.time()
    rez = depth_first_iterativ(g, gr, nrSolutiiCautate=int(sys.argv[3]), timeout=int(sys.argv[4]))
    print("DFI: " + rez)
    g.write(rez + "\n")
    g.write("==========================================\n")
    g.close()

    numeFisierOutput = "output_Astar_" + numeFisier
    g = open(sys.argv[2] + "/" + numeFisierOutput, "w")
    g.write("A*, euristica banala\n\n")
    t1 = time.time()
    rez = a_star(g, gr, nrSolutiiCautate=int(sys.argv[3]), tip_euristica="euristica banala", timeout = int(sys.argv[4]))
    print("A* banala: " + rez)
    g.write(rez + "\n")
    g.write("==========================================\n")
    g.write("A*, euristica 1\n")
    t1 = time.time()
    rez = a_star(g, gr, nrSolutiiCautate=int(sys.argv[3]), tip_euristica="euristica 1", timeout = int(sys.argv[4]))
    print("A* 1: " + rez)
    g.write(str(rez) + "\n")
    g.write("==========================================\n")
    g.write("A*, euristica 2\n")
    t1 = time.time()
    rez = a_star(g, gr, nrSolutiiCautate=int(sys.argv[3]), tip_euristica="euristica 2", timeout = int(sys.argv[4]))
    print("A* 2: " + rez)
    g.write(str(rez) + "\n")
    g.write("==========================================\n")
    g.write("A*, euristica neadmisibila\n")
    t1 = time.time()
    rez = a_star(g, gr, nrSolutiiCautate=int(sys.argv[3]), tip_euristica="euristica neadmisibila", timeout = int(sys.argv[4]))
    print("A* neadmisibila: " + rez)
    g.write(str(rez) + "\n")
    g.write("==========================================\n")
    g.close()


    numeFisierOutput = "output_AstarOpt_" + numeFisier
    g = open(sys.argv[2] + "/" + numeFisierOutput, "w")
    g.write("A* optimizat, euristica banala\n\n")
    t1 = time.time()
    rez = a_star_opt(g, gr, tip_euristica="euristica banala", timeout=int(sys.argv[4]))
    print("A*opt banala: " + rez)
    g.write(rez + "\n")
    g.write("==========================================\n")
    g.write("A* optimizat, euristica 1\n")
    t1 = time.time()
    rez = a_star_opt(g, gr, tip_euristica="euristica 1", timeout=int(sys.argv[4]))
    print("A*opt 1: " + rez)
    g.write(str(rez) + "\n")
    g.write("==========================================\n")
    g.write("A* optimizat, euristica 2\n")
    t1 = time.time()
    rez = a_star_opt(g, gr, tip_euristica="euristica 2", timeout=int(sys.argv[4]))
    print("A*opt 2: " + rez)
    g.write(str(rez) + "\n")
    g.write("==========================================\n")
    g.write("A* optimizat, euristica neadmisibila\n")
    t1 = time.time()
    rez = a_star_opt(g, gr, tip_euristica="euristica neadmisibila", timeout=int(sys.argv[4]))
    print("A*opt neadmisibila: " + rez)
    g.write(str(rez) + "\n")
    g.write("==========================================\n")
    g.close()

    numeFisierOutput = "output_IDAstar_" + numeFisier
    g = open(sys.argv[2] + "/" + numeFisierOutput, "w")
    g.write("IDA*, euristica banala\n\n")
    t1 = time.time()
    rez = ida_star(g, gr, nrSolutiiCautate=int(sys.argv[3]), tip_euristica="euristica banala", timeout=int(sys.argv[4]))
    print("IDA* banala: " + rez)
    g.write(rez + "\n")
    g.write("==========================================\n")
    g.write("IDA*, euristica 1\n")
    t1 = time.time()
    rez = ida_star(g, gr, nrSolutiiCautate=int(sys.argv[3]), tip_euristica="euristica 1", timeout=int(sys.argv[4]))
    print("IDA* 1: " + rez)
    g.write(str(rez) + "\n")
    g.write("==========================================\n")
    g.write("IDA*, euristica 2\n")
    t1 = time.time()
    rez = ida_star(g, gr, nrSolutiiCautate=int(sys.argv[3]), tip_euristica="euristica 2", timeout=int(sys.argv[4]))
    print("IDA* 2: " + rez)
    g.write(str(rez) + "\n")
    g.write("==========================================\n")
    g.write("IDA*, euristica neadmisibila\n")
    t1 = time.time()
    rez = ida_star(g, gr, nrSolutiiCautate=int(sys.argv[3]), tip_euristica="euristica neadmisibila", timeout=int(sys.argv[4]))
    print("IDA* neadmisibila: " + rez)
    g.write(str(rez) + "\n")
    g.write("==========================================\n")
    g.close()
    input("Press any key to continue...")