import tkinter as tk
from tkinter import messagebox
import requests
import json
import os
import webbrowser

FAVORITES_FILE = "favorites.json"
GITHUB_SEARCH_URL = "https://api.github.com/search/users"

def ensure_favorites_file():
    if not os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_favorites():
    ensure_favorites_file()
    with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_favorites(favs):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)

class GitHubFinderApp:
    def __init__(self, window):
        self.window = window
        self.window.title("GitHub User Finder")
        self.window.geometry("700x450")

        top_frame = tk.Frame(self.window)
        top_frame.pack(padx=10, pady=10, fill="x")

        tk.Label(top_frame, text="Поиск пользователя GitHub:").pack(side="left", padx=(0,5))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(top_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=(0,5))
        self.search_entry.bind("<Return>", lambda e: self.search())

        self.search_button = tk.Button(top_frame, text="Поиск", command=self.search)
        self.search_button.pack(side="left", padx=(0,5))

        self.clear_button = tk.Button(top_frame, text="Очистить", command=self.clear_results)
        self.clear_button.pack(side="left")

        middle_frame = tk.Frame(self.window)
        middle_frame.pack(padx=10, pady=(0,10), fill="both", expand=True)

        self.results_listbox = tk.Listbox(middle_frame, activestyle="none")
        self.results_listbox.pack(side="left", fill="both", expand=True)
        self.results_listbox.bind("<Double-Button-1>", lambda e: self.open_selected_profile())

        scrollbar = tk.Scrollbar(middle_frame, command=self.results_listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.results_listbox.config(yscrollcommand=scrollbar.set)

        right_frame = tk.Frame(self.window)
        right_frame.pack(padx=10, pady=(0,10), fill="x")

        self.add_fav_button = tk.Button(right_frame, text="Добавить в избранное", command=self.add_to_favorites)
        self.add_fav_button.pack(side="left", padx=(0,5))

        self.view_fav_button = tk.Button(right_frame, text="Просмотр избранных", command=self.show_favorites_window)
        self.view_fav_button.pack(side="left", padx=(0,5))

        self.status_label = tk.Label(self.window, text="", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=(0,10))

        self.results = []  # список словарей из API

    def set_status(self, text):
        self.status_label.config(text=text)

    def search(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Ошибка ввода", "Поле поиска не должно быть пустым.")
            return

        params = {"q": query, "per_page": 30}
        self.set_status("Поиск...")
        try:
            resp = requests.get(GITHUB_SEARCH_URL, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                self.results = items
                self.populate_results()
                self.set_status(f"Найдено: {len(items)}")
            elif resp.status_code == 403:
                self.set_status("Ошибка: превышен лимит запросов или доступ запрещён (403).")
                messagebox.showerror("Ошибка API", f"Код {resp.status_code}: {resp.text}")
            else:
                self.set_status(f"Ошибка: {resp.status_code}")
                messagebox.showerror("Ошибка API", f"Код {resp.status_code}: {resp.text}")
        except requests.RequestException as e:
            self.set_status("Ошибка сети")
            messagebox.showerror("Ошибка сети", str(e))

    def populate_results(self):
        self.results_listbox.delete(0, tk.END)
        for item in self.results:
            login = item.get("login", "")
            url = item.get("html_url", "")
            display = f"{login} — {url}"
            self.results_listbox.insert(tk.END, display)

    def clear_results(self):
        self.search_var.set("")
        self.results_listbox.delete(0, tk.END)
        self.results = []
        self.set_status("")

    def open_selected_profile(self):
        sel = self.results_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        item = self.results[idx]
        url = item.get("html_url")
        if url:
            webbrowser.open(url)

    def add_to_favorites(self):
        sel = self.results_listbox.curselection()
        if not sel:
            messagebox.showinfo("Информация", "Выберите пользователя в списке результатов, чтобы добавить в избранное.")
            return
        idx = sel[0]
        item = self.results[idx]
        favs = load_favorites()

        # проверка по логину
        login = item.get("login")
        if any(f.get("login") == login for f in favs):
            messagebox.showinfo("Информация", "Пользователь уже в избранных.")
            return

        # сохраняем минимум полей (login и url), можно сохранить полный объект
        fav_entry = {"login": login, "html_url": item.get("html_url")}
        favs.append(fav_entry)
        save_favorites(favs)
        messagebox.showinfo("Успех", f"Пользователь {login} добавлен в избранное.")

    def show_favorites_window(self):
        favs = load_favorites()
        win = tk.Toplevel(self.window)
        win.title("Избранные пользователи")
        win.geometry("400x300")

        listbox = tk.Listbox(win)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for f in favs:
            display = f"{f.get('login')} — {f.get('html_url')}"
            listbox.insert(tk.END, display)

        def open_selected():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            url = favs[idx].get("html_url")
            if url:
                webbrowser.open(url)

        def remove_selected():
            sel = listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            login = favs[idx].get("login")
            if messagebox.askyesno("Подтвердите", f"Удалить {login} из избранного?"):
                favs.pop(idx)
                save_favorites(favs)
                listbox.delete(idx)

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=(0,10))

        tk.Button(btn_frame, text="Открыть профиль", command=open_selected).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Удалить из избранного", command=remove_selected).pack(side="left", padx=5)

if __name__ == "__main__":
    window = tk.Tk()
    app = GitHubFinderApp(window)
    window.mainloop()
