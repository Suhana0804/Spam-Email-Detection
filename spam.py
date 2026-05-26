import os # Operating System : used for interacting with folders and files
import re # Regular Expression : used for searching patterns inside text
import csv # Comma Separated Value : used for saving results in spreadsheet format
import tkinter as tk # used for creating GUI applications
from tkinter import ttk, messagebox, filedialog
import random # used for shuffling files randomly

# -------------------- KEYWORDS --------------------

# Words commonly found in spam emails
SPAM_WORDS = {
    "lottery", "winner", "free", "claim", "urgent",
    "money", "prize", "congratulations", "click here",
    "act now", "limited time", "buy now", "cash",
    "win", "subscribe"
}

# Words commonly found in promotional emails
PROMO_WORDS = {
    "discount", "offer", "sale", "deal", "save",
    "coupon", "special", "promo", "exclusive",
    "subscribe", "newsletter", "shop", "clearance",
    "buy", "order"
}

# Words commonly found in important emails
IMPORTANT_WORDS = {
    "project", "meeting", "deadline", "invoice",
    "schedule", "payment", "client", "report",
    "proposal", "action required", "follow up",
    "important", "urgent", "appointment"
}

# score limits
SPAM_THRESHOLD = 2
PROMO_THRESHOLD = 2

# default folder
DEFAULT_FOLDER = "emails"

# -------------------- TEXT CLEANING --------------------

# clean and preprocess the text
def clean_text(text: str) -> str:
    if not text:
        return ""

    # convert text to lowercase
    text = text.lower()

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    # remove starting and ending spaces
    return text.strip()

# -------------------- MATCH FINDER --------------------

# check if keywords are present in the text
def find_matches(text: str, keywords: set) -> list:
    matches = []

    for kw in keywords:
        if kw in text:
            matches.append(kw)

    return matches

# -------------------- EMAIL CLASSIFICATION --------------------

def classify_email(text: str) -> dict:

    # clean the text
    text_clean = clean_text(text)

    # find matching keywords
    spam_matches = find_matches(text_clean, SPAM_WORDS)
    promo_matches = find_matches(text_clean, PROMO_WORDS)
    important_matches = find_matches(text_clean, IMPORTANT_WORDS)

    # calculate scores
    spam_score = len(spam_matches)
    promo_score = len(promo_matches)
    important_score = len(important_matches)

    # extra spam checks
    if re.search(r"[A-Z]{2,}", text):
        spam_score += 0.5

    spam_score += text.count("!") * 0.2

    # extra important checks
    if "invoice" in text_clean or "payment" in text_clean or "client" in text_clean:
        important_score += 1

    # default label
    label = "Important"

    # classification logic
    if spam_score >= SPAM_THRESHOLD and spam_score > promo_score and spam_score > important_score:
        label = "Spam"

    elif promo_score >= PROMO_THRESHOLD and promo_score > spam_score and promo_score > important_score:
        label = "Promotional"

    else:
        if len(text_clean) < 50 and ("http" in text_clean or "www." in text_clean):
            label = "Promotional"
        else:
            label = "Important"

    # return all results
    return {
        "label": label,
        "spam_matches": spam_matches,
        "promo_matches": promo_matches,
        "important_matches": important_matches,
        "scores": {
            "spam_score": spam_score,
            "promo_score": promo_score,
            "important_score": important_score
        }
    }

# -------------------- GUI APPLICATION --------------------

class EmailClassifierApp:

    def __init__(self, root):

        self.root = root
        self.root.title("Email Classifier")
        self.root.geometry("800x600")

        self.folder = DEFAULT_FOLDER
        self.file_list = []
        self.index = 0
        self.results = []

        # -------------------- TOP FRAME --------------------

        top_frame = tk.Frame(root)
        top_frame.pack(fill=tk.X, padx=10, pady=8)

        self.folder_label = tk.Label(top_frame, text=f"Folder: {self.folder}")
        self.folder_label.pack(side=tk.LEFT)

        load_btn = tk.Button(top_frame, text="Load Folder", command=self.choose_folder)
        load_btn.pack(side=tk.LEFT, padx=6)

        refresh_btn = tk.Button(top_frame, text="Load .txt Files", command=self.load_files)
        refresh_btn.pack(side=tk.LEFT)

        save_btn = tk.Button(top_frame, text="Save Results to CSV", command=self.save_results)
        save_btn.pack(side=tk.RIGHT)

        # -------------------- MIDDLE FRAME --------------------

        mid_frame = tk.Frame(root)
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        self.title_label = tk.Label(
            mid_frame,
            text="No file loaded",
            font=("Arial", 14, "bold")
        )

        self.title_label.pack(anchor="w")

        # area to display email text
        self.text_area = tk.Text(
            mid_frame,
            wrap=tk.WORD,
            height=18,
            font=("Consolas", 11)
        )

        self.text_area.pack(fill=tk.BOTH, expand=True, pady=6)
        self.text_area.config(state=tk.DISABLED)

        # -------------------- BOTTOM FRAME --------------------

        self.bottom_frame = tk.Frame(root)
        self.bottom_frame.pack(fill=tk.X, padx=10, pady=8)

        self.result_label = tk.Label(
            self.bottom_frame,
            text="Result: N/A",
            font=("Arial", 12)
        )

        self.result_label.pack(anchor="w")

        self.matches_label = tk.Label(
            self.bottom_frame,
            text="Matches: N/A"
        )

        self.matches_label.pack(anchor="w")

        # -------------------- NAVIGATION FRAME --------------------

        nav_frame = tk.Frame(self.bottom_frame)
        nav_frame.pack(fill=tk.X, pady=6)

        tk.Button(nav_frame, text="Previous", command=self.pre_file).pack(side=tk.LEFT)

        tk.Button(nav_frame, text="Classify", command=self.classify_current).pack(
            side=tk.LEFT,
            padx=8
        )

        tk.Button(nav_frame, text="Next", command=self.next_file).pack(side=tk.LEFT)

        tk.Button(nav_frame, text="Shuffle", command=self.shuffle_files).pack(side=tk.RIGHT)

        # -------------------- STATUS LABEL --------------------

        self.status_label = tk.Label(
            root,
            text="Status: Ready",
            anchor="w"
        )

        self.status_label.pack(fill=tk.X, padx=10, pady=(0, 8))

        # automatically load files
        self.load_files()

    # -------------------- CHOOSE FOLDER --------------------

    def choose_folder(self):

        folder_selected = filedialog.askdirectory()

        if folder_selected:
            self.folder = folder_selected

            self.folder_label.config(text=f"Folder: {self.folder}")

            self.load_files()

    # -------------------- LOAD FILES --------------------

    def load_files(self):

        self.file_list = []

        # check if folder exists
        if not os.path.isdir(self.folder):

            self.status_label.config(
                text=f"Status: Folder not found: {self.folder}"
            )

            return

        # load only txt files
        for f in sorted(os.listdir(self.folder)):

            if f.lower().endswith(".txt"):

                full = os.path.join(self.folder, f)

                try:
                    with open(full, "r", encoding="utf-8") as fh:

                        content = fh.read().strip()

                        # skip empty files
                        if content:
                            self.file_list.append(f)

                except Exception as e:
                    print("Error reading", full, e)

        # if no files found
        if not self.file_list:

            self.status_label.config(
                text="Status: No .txt files found"
            )

            self.title_label.config(text="No file loaded")

            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete("1.0", tk.END)
            self.text_area.config(state=tk.DISABLED)

            return

        self.index = 0
        self.results = []

        self.status_label.config(
            text=f"Status: Loaded {len(self.file_list)} files"
        )

        self.show_file()

    # -------------------- SHOW FILE --------------------

    def show_file(self):

        if not self.file_list:
            return

        fname = self.file_list[self.index]

        full = os.path.join(self.folder, fname)

        # open and display the file
        with open(full, "r", encoding="utf-8") as fh:
            content = fh.read()

        self.title_label.config(
            text=f"[{self.index + 1}/{len(self.file_list)}] {fname}"
        )

        # clear previous content
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)

        # insert new content
        self.text_area.insert(tk.END, content)

        self.text_area.config(state=tk.DISABLED)

        # reset previous results
        self.result_label.config(text="Result: N/A")
        self.matches_label.config(text="Matches: -")

        self.status_label.config(
            text=f"Status: Viewing {fname}"
        )

    # -------------------- CLASSIFY CURRENT EMAIL --------------------

    def classify_current(self):

        if not self.file_list:
            return

        content = self.text_area.get("1.0", tk.END)

        result = classify_email(content)

        self.result_label.config(
            text=f"Result: {result['label']}"
        )

        matches = (
            f"Spam: {', '.join(result['spam_matches'])} | "
            f"Promo: {', '.join(result['promo_matches'])} | "
            f"Important: {', '.join(result['important_matches'])}"
        )

        self.matches_label.config(text=matches)

        # store results
        self.results.append({
            "file": self.file_list[self.index],
            "label": result["label"]
        })

    # -------------------- NEXT FILE --------------------

    def next_file(self):

        if not self.file_list:
            return

        if self.index < len(self.file_list) - 1:
            self.index += 1
            self.show_file()

    # -------------------- PREVIOUS FILE --------------------

    def pre_file(self):

        if not self.file_list:
            return

        if self.index > 0:
            self.index -= 1
            self.show_file()

    # -------------------- SHUFFLE FILES --------------------

    def shuffle_files(self):

        random.shuffle(self.file_list)

        self.index = 0

        self.show_file()

    # -------------------- SAVE RESULTS --------------------

    def save_results(self):

        if not self.results:
            messagebox.showwarning(
                "Warning",
                "No results to save"
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not file_path:
            return

        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:

            writer = csv.writer(csvfile)

            writer.writerow(["File Name", "Classification"])

            for row in self.results:
                writer.writerow([row["file"], row["label"]])

        messagebox.showinfo(
            "Saved",
            "Results saved successfully"
        )

# -------------------- MAIN PROGRAM --------------------

if __name__ == "__main__":

    root = tk.Tk()

    app = EmailClassifierApp(root)

    root.mainloop()