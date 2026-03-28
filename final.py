import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import random


class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcard Maker App")
        self.root.geometry("750x620")
        self.root.config(padx=20, pady=20)

        # Flashcard storage
        self.flashcards = []

        # Quiz variables
        self.round_flashcards = []
        self.current_index = 0
        self.score = 0.0
        self.correct_count = 0
        self.correct_answer = ""
        self.points_per_question = 0.0

        self.show_main_menu()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_main_menu(self):
        self.clear_screen()

        title = tk.Label(
            self.root,
            text="Flashcard Maker App",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=15)

        instructions = tk.Label(
            self.root,
            text="Choose how you want to prepare your flashcards.",
            font=("Arial", 12)
        )
        instructions.pack(pady=8)

        format_title = tk.Label(
            self.root,
            text="TXT File Format Guide",
            font=("Arial", 14, "bold")
        )
        format_title.pack(pady=10)

        format_label = tk.Label(
            self.root,
            text=(
                "Each flashcard must be written on one line only.\n"
                "Use this format:\n\n"
                "Question|Correct Answer|Wrong1|Wrong2|Wrong3\n\n"
                "Example:\n"
                "What is 2 + 2?|4|3|5|6\n"
                "What is the capital of France?|Paris|London|Berlin|Rome"
            ),
            font=("Arial", 11),
            justify="center",
            wraplength=650
        )
        format_label.pack(pady=10)

        note_label = tk.Label(
            self.root,
            text="Note: Make sure every line has exactly 5 parts separated by |",
            font=("Arial", 10, "italic"),
            wraplength=650
        )
        note_label.pack(pady=5)

        import_button = tk.Button(
            self.root,
            text="Import TXT File",
            font=("Arial", 12),
            width=20,
            command=self.import_text_file
        )
        import_button.pack(pady=10)

        manual_button = tk.Button(
            self.root,
            text="Manual Input",
            font=("Arial", 12),
            width=20,
            command=self.manual_input_menu
        )
        manual_button.pack(pady=10)

        exit_button = tk.Button(
            self.root,
            text="Exit",
            font=("Arial", 12),
            width=20,
            command=self.root.quit
        )
        exit_button.pack(pady=10)

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

            messagebox.showinfo(
                "Success",
                f"{len(self.flashcards)} flashcards loaded successfully!"
            )

            self.ask_round_count()

        except Exception as error:
            messagebox.showerror("Error", f"Failed to read file.\n\n{error}")

    def manual_input_menu(self):
        self.clear_screen()

        title = tk.Label(
            self.root,
            text="Manual Flashcard Input",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=15)

        tk.Label(self.root, text="Question:", font=("Arial", 12)).pack(anchor="w")
        self.question_entry = tk.Entry(self.root, font=("Arial", 12), width=70)
        self.question_entry.pack(pady=5)

        tk.Label(self.root, text="Correct Answer:", font=("Arial", 12)).pack(anchor="w")
        self.correct_entry = tk.Entry(self.root, font=("Arial", 12), width=70)
        self.correct_entry.pack(pady=5)

        tk.Label(self.root, text="Wrong Choice 1:", font=("Arial", 12)).pack(anchor="w")
        self.wrong1_entry = tk.Entry(self.root, font=("Arial", 12), width=70)
        self.wrong1_entry.pack(pady=5)

        tk.Label(self.root, text="Wrong Choice 2:", font=("Arial", 12)).pack(anchor="w")
        self.wrong2_entry = tk.Entry(self.root, font=("Arial", 12), width=70)
        self.wrong2_entry.pack(pady=5)

        tk.Label(self.root, text="Wrong Choice 3:", font=("Arial", 12)).pack(anchor="w")
        self.wrong3_entry = tk.Entry(self.root, font=("Arial", 12), width=70)
        self.wrong3_entry.pack(pady=5)

        add_button = tk.Button(
            self.root,
            text="Add Flashcard",
            font=("Arial", 12),
            width=20,
            command=self.add_manual_flashcard
        )
        add_button.pack(pady=10)

        done_button = tk.Button(
            self.root,
            text="Done / Start Quiz",
            font=("Arial", 12),
            width=20,
            command=self.finish_manual_input
        )
        done_button.pack(pady=5)

        back_button = tk.Button(
            self.root,
            text="Back to Main Menu",
            font=("Arial", 12),
            width=20,
            command=self.show_main_menu
        )
        back_button.pack(pady=5)

        self.manual_count_label = tk.Label(
            self.root,
            text=f"Flashcards added: {len(self.flashcards)}",
            font=("Arial", 12, "bold")
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

        self.show_question()

    def show_question(self):
        self.clear_screen()

        if self.current_index >= len(self.round_flashcards):
            self.show_final_score()
            return

        current_flashcard = self.round_flashcards[self.current_index]
        question_text = current_flashcard["question"]
        self.correct_answer = current_flashcard["correct"]

        choices = current_flashcard["choices"][:]
        random.shuffle(choices)

        top_label = tk.Label(
            self.root,
            text=f"Flashcard {self.current_index + 1} of {len(self.round_flashcards)}",
            font=("Arial", 14, "bold")
        )
        top_label.pack(pady=10)

        score_label = tk.Label(
            self.root,
            text=f"Score: {self.score:.2f}",
            font=("Arial", 12)
        )
        score_label.pack(pady=5)

        question_label = tk.Label(
            self.root,
            text=question_text,
            font=("Arial", 16),
            wraplength=650,
            justify="center"
        )
        question_label.pack(pady=20)

        for choice in choices:
            button = tk.Button(
                self.root,
                text=choice,
                font=("Arial", 12),
                width=35,
                command=lambda selected=choice: self.check_answer(selected)
            )
            button.pack(pady=5)

    def check_answer(self, selected_answer):
        if selected_answer == self.correct_answer:
            self.correct_count += 1
            self.score = self.correct_count * self.points_per_question

            if self.correct_count == len(self.round_flashcards):
                self.score = 100.0

            messagebox.showinfo(
                "Result",
                f"Correct!\nYou earned {self.points_per_question:.2f} points."
            )
        else:
            messagebox.showinfo(
                "Result",
                f"Wrong!\nThe correct answer is:\n{self.correct_answer}"
            )

        self.current_index += 1
        self.show_question()

    def show_final_score(self):
        self.clear_screen()

        if self.correct_count == len(self.round_flashcards):
            self.score = 100.0
        else:
            self.score = self.correct_count * self.points_per_question

        title = tk.Label(
            self.root,
            text="Round Finished!",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=20)

        final_score_label = tk.Label(
            self.root,
            text=f"Your Final Score: {self.score:.2f}",
            font=("Arial", 18)
        )
        final_score_label.pack(pady=10)

        summary_label = tk.Label(
            self.root,
            text=(
                f"Correct Answers: {self.correct_count} out of {len(self.round_flashcards)}\n"
                f"Points Per Correct Answer: {self.points_per_question:.2f}\n"
                f"Total Possible Score: 100.00"
            ),
            font=("Arial", 14),
            justify="center"
        )
        summary_label.pack(pady=10)

        play_again_button = tk.Button(
            self.root,
            text="Play Again",
            font=("Arial", 12),
            width=20,
            command=self.ask_round_count
        )
        play_again_button.pack(pady=10)

        main_menu_button = tk.Button(
            self.root,
            text="Main Menu",
            font=("Arial", 12),
            width=20,
            command=self.show_main_menu
        )
        main_menu_button.pack(pady=5)

        exit_button = tk.Button(
            self.root,
            text="Exit",
            font=("Arial", 12),
            width=20,
            command=self.root.quit
        )
        exit_button.pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()