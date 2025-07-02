import tkinter as tk
import math as math
import speech_recognition as sr
from sympy import sympify, pi, E, sin, cos, log, sqrt, deg
from sympy.core.sympify import SympifyError
import re
import os
from functools import partial

root = tk.Tk()
root.geometry("800x600")
root.title("Tytuł")

ciemny_tryb = False
growy_tryb = False

# Konfiguracja kolumn i wierszy root, aby wyśrodkować ramkę kalkulatora
root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_rowconfigure(0, weight=1)

root.configure(bg="#1e1e1e")


# Ramka środkowa (kalkulator)
lewa_ramka = tk.Frame(root)
lewa_ramka.configure(bg="#1e1e1e")
lewa_ramka.grid(row=0, column=1, sticky="e")
lewa_ramka.grid_columnconfigure((0, 1, 2, 3), weight=1)
lewa_ramka.grid_rowconfigure(1, weight=1)

# Menu na górze
ramka_menu = tk.Frame(lewa_ramka, bg="#1e1e1e")
ramka_menu.grid(row=0, column=0, sticky="e", columnspan=4, pady=(20,5))
ramka_menu.configure(bg="#1e1e1e")
menu = [
    ("Standardowy", 0, 0), ("Naukowy", 0,1), ("Programistyczny", 0,2)
]

for i, (tekst, _, _) in enumerate(menu):
    btn = tk.Button(
        ramka_menu, text=tekst, width=15, height=2,
        command=lambda x=tekst.lower(): przelacz_tryb(x),
        font=("Consolas", 14), bg="#3a3a3a", fg="white",
        activebackground="#505050", activeforeground="white",
        relief=tk.FLAT, bd=0, highlightthickness=0
    )
    btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")

for i in range(len(menu)):
    ramka_menu.grid_columnconfigure(i, weight=1)

# Ramka na przyciski
ramka_przyciskow = tk.Frame(lewa_ramka)
ramka_przyciskow.grid(row=2, column=0, columnspan=4, sticky="e", padx=(30,100))

# Prawa ramka (historia)
prawa_ramka = tk.Frame(root)
prawa_ramka.configure(bg="#1e1e1e")
prawa_ramka.grid(row=0, column=2, sticky="e")
prawa_ramka.grid_rowconfigure(1, weight=1)
prawa_ramka.grid_columnconfigure(0, weight=1)
prawa_ramka.grid_remove()

ramka_srodkowa = tk.Frame(lewa_ramka)
ramka_srodkowa.grid(row=1, column=0, columnspan=4, sticky="e", padx=(70,100))

lista_historia = tk.Listbox(prawa_ramka, width=24, height=10)
lista_historia.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
prawa_ramka_pokazana = False


scrollBar = tk.Scrollbar(prawa_ramka)
scrollBar.grid(row=0, column=2, sticky="ns")

lista_historia.config(yscrollcommand=scrollBar.set)
scrollBar.config(command=lista_historia.yview)

def tekst(znak):
    entry.insert(tk.END, znak)

def delete():
    entry.delete(0, tk.END)

def oblicz():
    try:
        wyrazenie = entry.get().replace("=", "").strip()
        if not czy_wyrazenie_poprawne(wyrazenie):
            raise ValueError("Niepoprawna sładnia działania")
        wyrazenie = wyrazenie.replace("sin(", "sin(deg(")
        wyrazenie = wyrazenie.replace("cos(", "cos(deg(")
        wyrazenie = wyrazenie.replace("tan(", "tan(deg(")
        wynik = sympify(wyrazenie)
        if (hasattr(wynik, "is_infinite") and wynik.is_infinite) or \
           (hasattr(wynik, "is_nan") and wynik.is_nan):
            raise ValueError("Niedozwolony wynik")
        entry.delete(0, tk.END)
        entry.insert(tk.END, str(wynik))
        add_to_history(wyrazenie, wynik)
        entry.config(highlightthickness=0)
        label_info.config(text="")
    except (SympifyError, ValueError, TypeError):
        entry.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
        label_info.config(text="Błąd składniowy lub niedozwolone działanie")

def operacje_programistyczne(op):
    try:
        wartosc = entry.get().strip()

        if op == "bin":
            wynik = bin(int(wartosc))[2:]
        elif op == "dec":
            wynik = str(int(wartosc, 2))
        elif op == "~":
            wynik = str(~int(wartosc))
        elif op in ("&", "|", "^"):
            if op in wartosc:
                a, b = wartosc.split(op)
                a, b = int(a.strip()), int(b.strip())
                wynik = str(eval(f"{a} {op}, {b}"))
            else:
                raise ValueError("Brak drugieo argumentu.")
        else:
            wynik = "Error"

        entry.delete(0, tk.END)
        entry.insert(tk.END, wynik)
        add_to_history(wartosc, wynik)

        entry.config(highlightthickness=0)
        label_info.config(text="")

    except Exception:
        entry.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
        label_info.config(text="Błąd w działaniu")

def czy_wyrazenie_poprawne(wyrazenie):
    if re.search(r"[\+\-\*/]{2,}", wyrazenie):
        return False
    if re.search(r"[\+\-\*/]$", wyrazenie.strip()):
        return False
    if re.search(r"\(\s*\)", wyrazenie):
        return False
    if re.search(r"[^\d\+\-\*/\.\(\)eπE\s\^a-zA-Z]", wyrazenie):
        return False
    
    return True

def klawisz(event):
    klawisz = event.keysym
    znak = event.char


    print(f"[DEBUG] Klawisz: {event.keysym}, Znak: {event.char}")
    if klawisz == "Return" or znak == "=":
        oblicz()
        return "break"
    elif klawisz == "BackSpace":
        obecny_tekst = entry.get()
        entry.delete(0, tk.END)
        entry.insert(0, obecny_tekst[:-1])
        return "break"
    elif znak.isalpha():
        return "break"

root.bind("<Key>", klawisz, add="+")

def wczytaj_historie():
    if os.path.exists("historia.txt"):
        try:
            with open("historia.txt", "r", encoding="utf-8") as plik:
                for linia in plik:
                    linia = linia.strip()
                    if linia:
                        historia.append(linia)
                        lista_historia.insert(tk.END, linia)
            lista_historia.yview_moveto(1)
        except Exception as e:
            print("Błąd przy wczytywaniu historii", e)

def skroty(event):
    if event.state & 0x4:
        if event.keysym == "h":
            toggle_history()
        elif event.keysym == "m":
            switcher()
        elif event.keysym == "l":
            delete()
    elif event.keysym == "Escape":
        root.quit() 

root.bind("<KeyPress>", skroty, add="+")

def switcher():
    global ciemny_tryb
    if not ciemny_tryb:
        root.config(bg="#2e2e2e")
        lewa_ramka.config(bg="#2e2e2e")
        prawa_ramka.config(bg="#2e2e2e")
        entry.config(bg="#1e1e1e", fg="white")
        lista_historia.config(bg="#1e1e1e", fg="white")
        ciemny_tryb = True
    else:
        root.config(bg="SystemButtonFace")
        lewa_ramka.config(bg="SystemButtonFace")
        entry.config(bg="SystemButtonFace", fg="black")
        lista_historia.config(bg="SystemButtonFace", fg="black")
        ciemny_tryb = False

def toggle_history():
    global prawa_ramka_pokazana
    if not prawa_ramka_pokazana:
        prawa_ramka.grid()
    else:
        prawa_ramka.grid_remove()
    prawa_ramka_pokazana = not prawa_ramka_pokazana

def add_to_history(wyrazenie, wynik):
    historia.append(f"{wyrazenie} = {wynik}")
    lista_historia.insert(tk.END, f"{wyrazenie} = {wynik}")
    lista_historia.yview_moveto(1)

def klik_historia(event):
    wybrane = lista_historia.curselection()
    if wybrane:
        tekst = lista_historia.get(wybrane[0])
        if "=" in tekst:
            wyrazenie = tekst.split("=")[0].strip()
            entry.delete(0, tk.END)
            entry.insert(tk.END, wyrazenie)

def save_history():
    if historia:
        try:
            with open("historia.txt", "w", encoding="utf-8") as plik:
                for linia in historia:
                    plik.write(linia + "\n")
                print("Historia utworzona")
        except Exception as e:
            print("Błąd przy zapisywaniu.", e)
    else:
        print("Historia jest pusta.")


lista_historia.bind("<Double-Button-1>", klik_historia) 

def nasluchaj():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = r.listen(source, timeout=5)
            tekst = r.recognize_google(audio, language="pl-PL")
            tekst = tekst.lower()
            tekst = tekst.replace("plus", "+").replace("minus", "-")
            tekst = tekst.replace("razy", "*").replace("podzielić", "/")
            tekst = tekst.replace("przez", "/").replace("do potęgi", "**")
            tekst = tekst.replace("pierwiastek z", "**0.5")
            entry.delete(0, tk.END)
            entry.insert(0, tekst)
        except Exception as e:
            print("Błąd:", e)

przyciski = [
    ("7",1,0),("8",1,1),("9",1,2),("+",1,3),
    ("4",2,0),("5",2,1),("6",2,2),("-",2,3),
    ("1",3,0),("2",3,1),("3",3,2),("*",3,3),
    ("0",4,0),("/",4,2)
]

historia = []

przyciski_naukowe = [
    ("√", "sqrt("), ("^", "**"), ("sin", "sin("), ("cos", "cos("),
    ("log", "log("), ("π", "pi"), ("e", "E")
]

przyciski_programistyczne = [
    ("BIN", "bin"), ("DEC", "dec"),
    ("AND", "&"), ("OR", "|"), ("XOR", "^"), ("NOT", "~") 
]

wiersz_prog = 9
kolumna_prog = 0

widgety_naukowe = [

]

widgety_programistyczne = [

]

przyciski_dolne = [
    ("C", delete, 0),
    ("Oblicz", oblicz, 1),
    ("H", toggle_history, 2),
    ("Motyw", switcher, 3),
]

def przelacz_tryb(nazwa):
    if nazwa == "standardowy":
        for widget in widgety_naukowe + widgety_programistyczne:
            widget.grid_remove()
    elif nazwa == "naukowy":
        for widget in widgety_naukowe:
            widget.grid()
        for widget in widgety_programistyczne:
            widget.grid_remove()
    elif nazwa == "programistyczny":
        for widget in widgety_programistyczne:
            widget.grid()
        for widget in widgety_naukowe:
            widget.grid_remove()



wiersz_start = 8
kolumna = 0

entry = tk.Entry(ramka_srodkowa, width=16, relief=tk.RIDGE, justify="right", font=("Consolas", 20), bg="#b2b2b2", fg="white", insertbackground="white")
entry.grid(row=0, column=0, columnspan=4, pady=(10,5), sticky="ew", padx=10)

label_info = tk.Label(ramka_srodkowa, text="", fg="red", font=("Consolas", 11), bg="#1e1e1e")
label_info.grid(row=1, column=0, columnspan=4, pady=(0, 10), padx=10, sticky="ew")

ramka_dolna = tk.Frame(lewa_ramka, bg="#1e1e1e")
ramka_dolna.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 10))
ramka_dolna.grid_columnconfigure((0, 1, 2, 3), weight=1)

for (label, wartosc) in przyciski_naukowe:
    btn = tk.Button(ramka_przyciskow, text=label, command=partial(tekst, wartosc), width=5, height=2, font=("Consolas", 14), bg="#3a3a3a", fg="white", activebackground="#505050", activeforeground="white", relief=tk.FLAT, bd=0, highlightthickness=0)
    btn.grid(row=wiersz_start, column=kolumna, padx=3, pady=3)
    widgety_naukowe.append(btn)
    kolumna +=1

for (text, wiersz, kolumna) in przyciski:
    btn = tk.Button(
        ramka_przyciskow,
        text=text,
        command=partial(tekst, text),
        width=5, height=2,
        font=("Consolas", 14),
        bg="#3a3a3a", fg="white",
        activebackground="#505050"
    )
    btn.grid(row=wiersz, column=kolumna, padx=3, pady=3, sticky="nsew")

for i in range(4):
    ramka_przyciskow.grid_columnconfigure(i, weight=1)
for i in range(1, 5):
    ramka_przyciskow.grid_rowconfigure(i, weight=1)

for (label, kod) in przyciski_programistyczne:
    btn = tk.Button(ramka_przyciskow, text=label, width=5, height=2, command=lambda x=kod: operacje_programistyczne(x), font=("Consolas", 14), bg="#3a3a3a", fg="white", activebackground="#505050")
    btn.grid(row=wiersz_prog, column=kolumna_prog, padx=3, pady=3)
    widgety_programistyczne.append(btn)
    entry(ramka_srodkowa, width=200)
    kolumna_prog +=1 

for tekst, funkcja, kol in przyciski_dolne:
    btn = tk.Button(
        ramka_dolna, text=tekst, command=funkcja,
        font=("Consolas", 14), bg="#3a3a3a", fg="white", activebackground="#505050"
    )
    btn.grid(row=0, column=kol, padx=5, ipadx=10, ipady=5, sticky="ew")

# PRZYCISKI MÓW I ZAPISZ HISTORIĘ – wiersze 3 i 4
tk.Button(
    lewa_ramka, text="🎙️ Mów", command=nasluchaj,
    font=("Consolas", 14), bg="#3a3a3a", fg="white", activebackground="#505050"
).grid(row=4, column=0, columnspan=4, sticky="ew", padx=10, pady=5)

tk.Button(
    lewa_ramka, text="💾 Zapisz historię", command=save_history,
    font=("Consolas", 14), bg="#3a3a3a", fg="white", activebackground="#505050"
).grid(row=5, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 10))

wczytaj_historie()
root.mainloop()
