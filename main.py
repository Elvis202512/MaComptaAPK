import os
import sqlite3
from kivy.utils import platform
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.core.window import Window
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime

# --- CONFIGURATION DES CHEMINS (CRUCIAL POUR ANDROID) ---
if platform == 'android':
    from android.storage import app_storage_path
    BASE_PATH = app_storage_path()
else:
    BASE_PATH = "."

DB_PATH = os.path.join(BASE_PATH, 'compta.db')

Window.size = (950, 750)

Builder.load_string('''
<MainScreen>:
    canvas.before:
        Color:
            rgba: 0.08, 0.09, 0.12, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: 15
        spacing: 10

        BoxLayout:
            size_hint_y: None
            height: 70
            canvas.before:
                Color:
                    rgba: 0.12, 0.4, 0.7, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [0, 0, 15, 15]
            Image:
                source: root.logo_path
                size_hint_x: None
                width: 80
            Label:
                text: root.ste_display
                bold: True
                font_size: 22
            Button:
                text: "LOGO"
                size_hint: None, None
                size: 80, 35
                pos_hint: {'center_y': .5}
                on_release: root.choose_logo()

        BoxLayout:
            spacing: 15
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.35
                spacing: 8
                TextInput:
                    id: p_name
                    hint_text: "Article"
                    size_hint_y: None
                    height: 40
                TextInput:
                    id: p_pu
                    hint_text: "Prix (FCFA)"
                    size_hint_y: None
                    height: 40
                TextInput:
                    id: p_qte
                    text: "1"
                    size_hint_y: None
                    height: 40
                BoxLayout:
                    size_hint_y: None
                    height: 35
                    CheckBox:
                        id: check_debt
                        size_hint_x: None
                        width: 40
                    Label:
                        text: "Dette Client"
                Button:
                    text: "AJOUTER"
                    size_hint_y: None
                    height: 50
                    background_color: 0.1, 0.5, 0.3, 1
                    on_release: root.add_sale(p_name.text, p_pu.text, p_qte.text, check_debt.active)
                TextInput:
                    id: note_input
                    hint_text: "Note rapide..."
                Button:
                    text: "SAUVER NOTE"
                    size_hint_y: None
                    height: 40
                    on_release: root.save_note(note_input.text)
                Button:
                    text: "EXPORTER NOTES (TXT)"
                    size_hint_y: None
                    height: 40
                    background_color: 0.2, 0.4, 0.6, 1
                    on_release: root.export_txt()
                Button:
                    text: "VIDER TOUTES LES NOTES"
                    size_hint_y: None
                    height: 40
                    background_color: 0.6, 0.2, 0.2, 1
                    on_release: root.clear_data("notes")

            BoxLayout:
                orientation: 'vertical'
                spacing: 10
                ScrollView:
                    canvas.before:
                        Color:
                            rgba: 0.15, 0.17, 0.22, 1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [10]
                    BoxLayout:
                        id: container
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        padding: 10
                        spacing: 5
                BoxLayout:
                    size_hint_y: None
                    height: 140
                    orientation: 'vertical'
                    spacing: 5
                    TextInput:
                        id: date_filter
                        hint_text: "Ex: 2026-02-22 ou 2025-12-01-2026-02-22"
                        size_hint_y: None
                        height: 35
                    BoxLayout:
                        spacing: 5
                        Button:
                            text: "GÉNÉRER PDF PRO"
                            background_color: 0.12, 0.4, 0.7, 1
                            on_release: root.gen_pdf(date_filter.text)
                        Button:
                            text: "NETTOYER L'ÉCRAN"
                            background_color: 0.4, 0.4, 0.4, 1
                            on_release: root.clear_screen()
                    Button:
                        text: "VIDER DÉFINITIVEMENT LE PANIER"
                        background_color: 0.8, 0.1, 0.1, 1
                        bold: True
                        on_release: root.clear_data("sales")
''')

class MainScreen(Screen):
    ste_display = StringProperty("JUDES PRO MAX")
    logo_path = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        name TEXT, pu REAL, qte INTEGER, 
                        is_debt INTEGER, date TEXT)''')
        c.execute('CREATE TABLE IF NOT EXISTS config (name TEXT, logo TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS notes (content TEXT)')
        conn.commit(); conn.close()
        self.load_data()

    def load_data(self):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT name, logo FROM config LIMIT 1")
        res = c.fetchone()
        if res:
            self.ste_display = res[0]; self.logo_path = res[1] or ""
        conn.close(); self.refresh_list()

    def add_sale(self, name, pu, qte, is_debt):
        if not name or not pu: return
        try:
            p = float(pu.replace(',', '.').strip())
            q = int(qte.strip())
            dt = datetime.now().strftime('%Y-%m-%d')
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("INSERT INTO sales (name, pu, qte, is_debt, date) VALUES (?,?,?,?,?)", 
                      (name.upper().strip(), p, q, 1 if is_debt else 0, dt))
            last_id = c.lastrowid
            conn.commit(); conn.close()
            self.add_item_to_screen(last_id, name.upper(), p, q, is_debt, dt)
        except: pass

    def add_item_to_screen(self, idx, n, p, q, d, dt):
        txt = f"[{dt}] {n} | {p}x{q}={p*q}"
        btn = Button(text=txt, size_hint_y=None, height=40, 
                     background_color=(0.2, 0.23, 0.3, 1) if not d else (0.4, 0.2, 0.2, 1))
        btn.bind(on_release=lambda x, i=idx: self.delete_item(i, x))
        self.ids.container.add_widget(btn)

    def refresh_list(self):
        self.ids.container.clear_widgets()
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        c.execute("SELECT id, name, pu, qte, is_debt, date FROM sales ORDER BY id DESC")
        for row in c.fetchall():
            self.add_item_to_screen(row[0], row[1], row[2], row[3], row[4], row[5])
        conn.close()

    def clear_screen(self):
        self.ids.container.clear_widgets()

    def delete_item(self, item_id, widget):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM sales WHERE id = ?", (item_id,))
        conn.commit(); conn.close()
        self.ids.container.remove_widget(widget)

    def gen_pdf(self, date_filter):
        conn = sqlite3.connect(DB_PATH); c = conn.cursor()
        if "-" in date_filter and len(date_filter.split("-")) == 6:
            parts = date_filter.split("-")
            d1, d2 = f"{parts[0]}-{parts[1]}-{parts[2]}", f"{parts[3]}-{parts[4]}-{parts[5]}"
            query = "SELECT name, pu, qte, is_debt, date FROM sales WHERE date BETWEEN ? AND ?"
            data = c.execute(query, (d1, d2)).fetchall()
        elif date_filter.strip():
            data = c.execute("SELECT name, pu, qte, is_debt, date FROM sales WHERE date = ?", (date_filter.strip(),)).fetchall()
        else:
            data = c.execute("SELECT name, pu, qte, is_debt, date FROM sales").fetchall()

        if not data: return
        
        filename = f"Facture_{datetime.now().strftime('%H%M%S')}.pdf"
        full_path = os.path.join(BASE_PATH, filename)
        pdf = canvas.Canvas(full_path, pagesize=A4)
        width, height = A4

        # --- LOGO ET HEADER ---
        if self.logo_path and os.path.exists(self.logo_path):
            pdf.drawImage(self.logo_path, 50, height-100, width=60, height=60, preserveAspectRatio=True)
        
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawString(130, height-60, self.ste_display)
        pdf.setFont("Helvetica", 10)
        pdf.drawString(130, height-75, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        y = height - 180
        pdf.setFillColor(colors.HexColor("#124070"))
        pdf.rect(50, y, 500, 20, fill=1, stroke=0)
        pdf.setFillColor(colors.white)
        pdf.drawString(60, y+6, "DESIGNATION")
        pdf.drawRightString(540, y+6, "TOTAL (FCFA)")

        y -= 20
        total_final = 0
        pdf.setFillColor(colors.black)
        for r in data:
            sub = r[1]*r[2]
            if r[3]:
                pdf.setFillColor(colors.red); total_final -= sub
            else:
                pdf.setFillColor(colors.black); total_final += sub
            
            pdf.drawString(60, y+5, f"{r[4]} - {r[0]}")
            pdf.drawRightString(540, y+5, f"{sub:,.0f}")
            y -= 20
            if y < 100: pdf.showPage(); y = height - 50

        pdf.save(); conn.close()
        
        # Sur mobile, on affiche un message au lieu d'ouvrir
        if platform == 'android':
            self.show_popup("PDF Créé", f"Enregistré dans: {full_path}")
        else:
            os.startfile(full_path)

    def save_note(self, text):
        if text.strip():
            conn = sqlite3.connect(DB_PATH); conn.execute("INSERT INTO notes VALUES (?)", (text,))
            conn.commit(); conn.close(); self.ids.note_input.text = ""

    def export_txt(self):
        full_path = os.path.join(BASE_PATH, "Notes_Export.txt")
        conn = sqlite3.connect(DB_PATH)
        notes = [n[0] for n in conn.execute("SELECT content FROM notes").fetchall()]
        if notes:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("\n".join(notes))
            if platform != 'android': os.startfile(full_path)
            else: self.show_popup("Succès", "Notes exportées")
        conn.close()

    def clear_data(self, table):
        conn = sqlite3.connect(DB_PATH); conn.execute(f"DELETE FROM {table}"); conn.commit(); conn.close()
        self.refresh_list()

    def show_popup(self, title, msg):
        p = Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.4))
        p.open()

    def choose_logo(self):
        fc = FileChooserIconView(path=os.path.expanduser("~"))
        btn = Button(text="OK", size_hint_y=None, height=50)
        box = BoxLayout(orientation='vertical'); box.add_widget(fc); box.add_widget(btn)
        pop = Popup(title="Logo", content=box, size_hint=(0.9, 0.9))
        def set_l(obj):
            if fc.selection:
                p = fc.selection[0]
                conn = sqlite3.connect(DB_PATH); c = conn.cursor()
                c.execute("UPDATE config SET logo = ?", (p,))
                if c.rowcount == 0: c.execute("INSERT INTO config VALUES (?,?)", (self.ste_display, p))
                conn.commit(); conn.close(); self.logo_path = p; pop.dismiss()
        btn.bind(on_release=set_l); pop.open()

class ProComptaApp(App):
    def build(self): return MainScreen()

if __name__ == "__main__":
    ProComptaApp().run()