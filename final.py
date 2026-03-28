import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import random
import os

# =========================
# IMAGE SUPPORT
# =========================
try:
    from PIL import Image, ImageTk, ImageSequence
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# =========================
# SOUND SUPPORT
# =========================
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcard Maker App")
        self.root.geometry("900x700")
        self.root.resizable(False, False)

        self.base_folder = os.path.dirname(os.path.abspath(__file__))

        # ==========================================
        # CUSTOMIZATION
        # ==========================================
        self.window_width = 900
        self.window_height = 700

        self.title_color = "#A9C9FF"
        self.text_color = "white"
        self.panel_color = "#0B1026"
        self.panel_border_color = "#6C63FF"

        self.button_color = "#4CAF50"
        self.button_text_color = "white"
        self.button_hover_color = "#45A049"

        self.answer_button_color = "#FFD966"
        self.answer_button_text_color = "black"
        self.answer_hover_color = "#F4C542"

        self.use_background_gif = True
        self.background_gif_path = os.path.join(
            self.base_folder,
            "assets",
            "background_images",
            "space-wallpaper-stars-background.gif"
        )

        self.use_sound = True
        self.correct_sound_path = os.path.join(
            self.base_folder,
            "assets",
            "sounds",
            "correct.mp3"
        )
        self.wrong_sound_path = os.path.join(
            self.base_folder,
            "assets",
            "sounds",
            "wrong.mp3"
        )
        self.background_music_path = os.path.join(
            self.base_folder,
            "assets",
            "sounds",
            "quiz_music.mp3"
        )

        # ==========================================
        # APP VARIABLES
        # ==========================================
        self.flashcards = []
        self.round_flashcards = []
        self.current_index = 0
        self.score = 0.0
        self.correct_count = 0
        self.correct_answer = ""
        self.points_per_question = 0.0

        # Background GIF storage
        self.gif_frames = []
        self.gif_index = 0
        self.gif_delay = 100

        # Keep track if music is already playing
        self.music_playing = False

        # Initialize audio
        self.init_audio()

        # Background label
        self.bg_label = tk.Label(self.root, bd=0)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Load and animate GIF
        self.load_background_gif()
        self.animate_background()

        self.show_main_menu()

    # ==========================================
    # AUDIO
    # ==========================================
    def init_audio(self):
        if self.use_sound and PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as error:
                print("Could not initialize pygame mixer:", error)
                self.use_sound = False

    def play_correct_sound(self):
        if not self.use_sound or not PYGAME_AVAILABLE:
            return
        try:
            if os.path.exists(self.correct_sound_path):
                pygame.mixer.Sound(self.correct_sound_path).play()
            else:
                print("Correct sound not found:", self.correct_sound_path)
        except Exception as error:
            print("Error playing correct sound:", error)

    def play_wrong_sound(self):
        if not self.use_sound or not PYGAME_AVAILABLE:
            return
        try:
            if os.path.exists(self.wrong_sound_path):
                pygame.mixer.Sound(self.wrong_sound_path).play()
            else:
                print("Wrong sound not found:", self.wrong_sound_path)
        except Exception as error:
            print("Error playing wrong sound:", error)

    def start_background_music(self):
        if not self.use_sound or not PYGAME_AVAILABLE:
            return
        try:
            if os.path.exists(self.background_music_path):
                pygame.mixer.music.load(self.background_music_path)
                pygame.mixer.music.play(-1)
                self.music_playing = True
            else:
                print("Background music not found:", self.background_music_path)
        except Exception as error:
            print("Error playing background music:", error)

    def stop_background_music(self):
        if not self.use_sound or not PYGAME_AVAILABLE:
            return
        try:
            pygame.mixer.music.stop()
            self.music_playing = False
        except Exception as error:
            print("Error stopping background music:", error)

    # ==========================================
    # BACKGROUND GIF
    # ==========================================
    def load_background_gif(self):
        if not self.use_background_gif:
            return

        if not PIL_AVAILABLE:
            print("Pillow is not installed. GIF background disabled.")
            return

        if not os.path.exists(self.background_gif_path):
            print("GIF background file not found:", self.background_gif_path)
            return

        try:
            gif = Image.open(self.background_gif_path)
            self.gif_frames = []

            for frame in ImageSequence.Iterator(gif):
                frame = frame.copy().convert("RGBA")
                frame = frame.resize((self.window_width, self.window_height))
                photo = ImageTk.PhotoImage(frame)
                self.gif_frames.append(photo)

            if len(self.gif_frames) == 0:
                print("No GIF frames loaded.")
        except Exception as error:
            print("Error loading GIF background:", error)

    def animate_background(self):
        if self.gif_frames:
            self.bg_label.config(image=self.gif_frames[self.gif_index])
            self.gif_index = (self.gif_index + 1) % len(self.gif_frames)
        self.root.after(self.gif_delay, self.animate_background)

    # ==========================================
    # GENERAL HELPERS
    # ==========================================
    def clear_screen(self):
        for widget in self.root.winfo_children():
            if widget != self.bg_label:
                widget.destroy()

    def create_panel(self, width=760, height=560):
        panel = tk.Frame(
            self.root,
            bg=self.panel_color,
            bd=3,
            relief="solid",
            highlightbackground=self.panel_border_color,
            highlightthickness=2
        )
        panel.place(relx=0.5, rely=0.5, anchor="center", width=width, height=height)
        return panel

    def create_main_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            font=("Arial", 12, "bold"),
            width=22,
            bg=self.button_color,
            fg=self.button_text_color,
            activebackground=self.button_hover_color,
            activeforeground=self.button_text_color,
            relief="raised",
            bd=3,
            command=command
        )

    def create_answer_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            font=("Arial", 12, "bold"),
            width=35,
            bg=self.answer_button_color,
            fg=self.answer_button_text_color,
            activebackground=self.answer_hover_color,
            activeforeground=self.answer_button_text_color,
            relief="raised",
            bd=3,
            wraplength=500,
            command=command
        )

    # ==========================================
    # MAIN MENU
    # ==========================================
    def show_main_menu(self):
        self.stop_background_music()
        self.clear_screen()

        panel = self.create_panel(760, 560)

        title = tk.Label(
            panel,
            text="Flashcard Maker App",
            font=("Arial", 28, "bold"),
            bg=self.panel_color,
            fg=self.title_color
        )
        title.pack(pady=20)

        instructions = tk.Label(
            panel,
            text="Choose how you want to prepare your flashcards.",
            font=("Arial", 13),
            bg=self.panel_color,
            fg=self.text_color
        )
        instructions.pack(pady=5)

        format_title = tk.Label(
            panel,
            text="TXT File Format Guide",
            font=("Arial", 16, "bold"),
            bg=self.panel_color,
            fg=self.title_color
        )
        format_title.pack(pady=15)

        format_label = tk.Label(
            panel,
            text=(
                "Each flashcard must be written on one line only.\n"
                "Use this format:\n\n"
                "Question|Correct Answer|Wrong1|Wrong2|Wrong3\n\n"
                "Example:\n"
                "What is 2 + 2?|4|3|5|6\n"
                "What is the capital of France?|Paris|London|Berlin|Rome"
            ),
            font=("Arial", 12),
            justify="center",
            bg=self.panel_color,
            fg=self.text_color,
            wraplength=650
        )
        format_label.pack(pady=10)

        note_label = tk.Label(
            panel,
            text="Note: Make sure every line has exactly 5 parts separated by |",
            font=("Arial", 11, "italic"),
            bg=self.panel_color,
            fg="#D6D6D6"
        )
        note_label.pack(pady=5)

        self.create_main_button(panel, "Import TXT File", self.import_text_file).pack(pady=10)
        self.create_main_button(panel, "Manual Input", self.manual_input_menu).pack(pady=10)
        self.create_main_button(panel, "Exit", self.root.quit).pack(pady=10)

    # ==========================================
    # IMPORT TXT FILE
    # ==========================================
    def import_text_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Flashcard Text File",
            filetypes=[("Text Files", "*.txt")]
        )

        if not file_path:
            return

        loaded_flashcards = []

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            for line in lines:
                line = line.strip()

                if line == "":
                    continue

                parts = line.split("|")

                if len(parts) != 5:
                    continue

                question = parts[0].strip()
                correct = parts[1].strip()
                wrong1 = parts[2].strip()
                wrong2 = parts[3].strip()
                wrong3 = parts[4].strip()

                flashcard = {
                    "question": question,
                    "correct": correct,
                    "choices": [correct, wrong1, wrong2, wrong3]
                }

                loaded_flashcards.append(flashcard)

            if len(loaded_flashcards) == 0:
                messagebox.showerror(
                    "Error",
                    "No valid flashcards found.\n\n"
                    "Make sure each line follows this format:\n"
                    "Question|Correct Answer|Wrong1|Wrong2|Wrong3"
                )
                return

            self.flashcards = loaded_flashcards
            messagebox.showinfo("Success", f"{len(self.flashcards)} flashcards loaded successfully!")
            self.ask_round_count()

        except Exception as error:
            messagebox.showerror("Error", f"Failed to read file.\n\n{error}")

    # ==========================================
    # MANUAL INPUT
    # ==========================================
    def manual_input_menu(self):
        self.stop_background_music()
        self.clear_screen()

        panel = self.create_panel(820, 610)

        title = tk.Label(
            panel,
            text="Manual Flashcard Input",
            font=("Arial", 22, "bold"),
            bg=self.panel_color,
            fg=self.title_color
        )
        title.pack(pady=15)

        def make_label(text):
            return tk.Label(panel, text=text, font=("Arial", 12), bg=self.panel_color, fg=self.text_color)

        make_label("Question:").pack(anchor="w", padx=30)
        self.question_entry = tk.Entry(panel, font=("Arial", 12), width=75, bd=3)
        self.question_entry.pack(pady=5)

        make_label("Correct Answer:").pack(anchor="w", padx=30)
        self.correct_entry = tk.Entry(panel, font=("Arial", 12), width=75, bd=3)
        self.correct_entry.pack(pady=5)

        make_label("Wrong Choice 1:").pack(anchor="w", padx=30)
        self.wrong1_entry = tk.Entry(panel, font=("Arial", 12), width=75, bd=3)
        self.wrong1_entry.pack(pady=5)

        make_label("Wrong Choice 2:").pack(anchor="w", padx=30)
        self.wrong2_entry = tk.Entry(panel, font=("Arial", 12), width=75, bd=3)
        self.wrong2_entry.pack(pady=5)

        make_label("Wrong Choice 3:").pack(anchor="w", padx=30)
        self.wrong3_entry = tk.Entry(panel, font=("Arial", 12), width=75, bd=3)
        self.wrong3_entry.pack(pady=5)

        self.create_main_button(panel, "Add Flashcard", self.add_manual_flashcard).pack(pady=10)
        self.create_main_button(panel, "Done / Start Quiz", self.finish_manual_input).pack(pady=5)
        self.create_main_button(panel, "Back to Main Menu", self.show_main_menu).pack(pady=5)

        self.manual_count_label = tk.Label(
            panel,
            text=f"Flashcards added: {len(self.flashcards)}",
            font=("Arial", 12, "bold"),
            bg=self.panel_color,
            fg=self.title_color
        )
        self.manual_count_label.pack(pady=10)

    def add_manual_flashcard(self):
        question = self.question_entry.get().strip()
        correct = self.correct_entry.get().strip()
        wrong1 = self.wrong1_entry.get().strip()
        wrong2 = self.wrong2_entry.get().strip()
        wrong3 = self.wrong3_entry.get().strip()

        if not question or not correct or not wrong1 or not wrong2 or not wrong3:
            messagebox.showwarning("Missing Input", "Please fill in all fields.")
            return

        flashcard = {
            "question": question,
            "correct": correct,
            "choices": [correct, wrong1, wrong2, wrong3]
        }

        self.flashcards.append(flashcard)

        self.question_entry.delete(0, tk.END)
        self.correct_entry.delete(0, tk.END)
        self.wrong1_entry.delete(0, tk.END)
        self.wrong2_entry.delete(0, tk.END)
        self.wrong3_entry.delete(0, tk.END)

        self.manual_count_label.config(text=f"Flashcards added: {len(self.flashcards)}")
        messagebox.showinfo("Added", "Flashcard added successfully!")

    def finish_manual_input(self):
        if len(self.flashcards) == 0:
            messagebox.showwarning("No Flashcards", "Please add at least one flashcard.")
            return
        self.ask_round_count()

    # ==========================================
    # QUIZ SETUP
    # ==========================================
    def ask_round_count(self):
        if len(self.flashcards) == 0:
            messagebox.showwarning("No Flashcards", "No flashcards available.")
            return

        count = simpledialog.askinteger(
            "Flashcard Round",
            f"You have {len(self.flashcards)} flashcards.\nHow many do you want to show this round?",
            minvalue=1,
            maxvalue=len(self.flashcards)
        )

        if count is None:
            return

        self.start_quiz(count)

    def start_quiz(self, count):
        self.score = 0.0
        self.correct_count = 0
        self.current_index = 0

        self.round_flashcards = random.sample(self.flashcards, count)
        self.points_per_question = 100 / len(self.round_flashcards)

        self.start_background_music()
        self.show_question()

    # ==========================================
    # QUIZ SCREEN
    # ==========================================
    def show_question(self):
        self.clear_screen()

        if self.current_index >= len(self.round_flashcards):
            self.show_final_score()
            return

        panel = self.create_panel(760, 560)

        current_flashcard = self.round_flashcards[self.current_index]
        question_text = current_flashcard["question"]
        self.correct_answer = current_flashcard["correct"]

        choices = current_flashcard["choices"][:]
        random.shuffle(choices)

        top_label = tk.Label(
            panel,
            text=f"Flashcard {self.current_index + 1} of {len(self.round_flashcards)}",
            font=("Arial", 14, "bold"),
            bg=self.panel_color,
            fg=self.title_color
        )
        top_label.pack(pady=10)

        score_label = tk.Label(
            panel,
            text=f"Score: {self.score:.2f}",
            font=("Arial", 12),
            bg=self.panel_color,
            fg=self.text_color
        )
        score_label.pack(pady=5)

        question_frame = tk.Frame(
            panel,
            bg="#111936",
            bd=2,
            relief="groove",
            highlightbackground=self.panel_border_color,
            highlightthickness=1
        )
        question_frame.pack(pady=20, padx=20, fill="x")

        question_label = tk.Label(
            question_frame,
            text=question_text,
            font=("Arial", 16, "bold"),
            wraplength=600,
            justify="center",
            bg="#111936",
            fg="white"
        )
        question_label.pack(pady=20)

        for choice in choices:
            self.create_answer_button(
                panel,
                choice,
                lambda selected=choice: self.check_answer(selected)
            ).pack(pady=6)

    def check_answer(self, selected_answer):
        if selected_answer == self.correct_answer:
            self.play_correct_sound()
            self.correct_count += 1
            self.score = self.correct_count * self.points_per_question

            if self.correct_count == len(self.round_flashcards):
                self.score = 100.0

            messagebox.showinfo(
                "Result",
                f"Correct!\nYou earned {self.points_per_question:.2f} points."
            )
        else:
            self.play_wrong_sound()
            messagebox.showinfo(
                "Result",
                f"Wrong!\nThe correct answer is:\n{self.correct_answer}"
            )

        self.current_index += 1
        self.show_question()

    # ==========================================
    # FINAL SCORE
    # ==========================================
    def show_final_score(self):
        self.stop_background_music()
        self.clear_screen()

        panel = self.create_panel(760, 420)

        if self.correct_count == len(self.round_flashcards):
            self.score = 100.0
        else:
            self.score = self.correct_count * self.points_per_question

        title = tk.Label(
            panel,
            text="Round Finished!",
            font=("Arial", 24, "bold"),
            bg=self.panel_color,
            fg=self.title_color
        )
        title.pack(pady=20)

        final_score_label = tk.Label(
            panel,
            text=f"Your Final Score: {self.score:.2f}",
            font=("Arial", 18, "bold"),
            bg=self.panel_color,
            fg="white"
        )
        final_score_label.pack(pady=10)

        summary_label = tk.Label(
            panel,
            text=(
                f"Correct Answers: {self.correct_count} out of {len(self.round_flashcards)}\n"
                f"Points Per Correct Answer: {self.points_per_question:.2f}\n"
                f"Total Possible Score: 100.00"
            ),
            font=("Arial", 14),
            justify="center",
            bg=self.panel_color,
            fg=self.text_color
        )
        summary_label.pack(pady=15)

        self.create_main_button(panel, "Play Again", self.ask_round_count).pack(pady=10)
        self.create_main_button(panel, "Main Menu", self.show_main_menu).pack(pady=5)
        self.create_main_button(panel, "Exit", self.root.quit).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()