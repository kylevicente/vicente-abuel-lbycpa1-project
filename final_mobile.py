import random
from pathlib import Path
import flet as ft


class FlashcardFletApp:
    def __init__(self, page: ft.Page):
        self.page = page

        # Data
        self.flashcards = []
        self.round_flashcards = []
        self.current_index = 0
        self.correct_count = 0
        self.score = 0.0
        self.points_per_question = 0.0

        # UI state
        self.current_screen = "menu"
        self.correct_answer = ""
        self.selected_answer = None

        # Theme colors
        self.panel_color = "#0B1026CC"
        self.panel_border = "#6C63FF"
        self.title_color = "#A9C9FF"
        self.text_color = "white"
        self.button_color = "#4CAF50"
        self.answer_button_color = "#FFD966"

        # File picker service
        self.file_picker = ft.FilePicker()
        self.page.overlay.append(self.file_picker)

        # Configure page
        self.page.title = "Flashcard Maker App"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        self.page.bgcolor = ft.Colors.BLACK
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.START

        self.render()

    # -------------------------
    # Helpers
    # -------------------------
    def show_message(self, text: str):
        self.page.snack_bar = ft.SnackBar(ft.Text(text))
        self.page.snack_bar.open = True
        self.page.update()

    def reset_quiz_state(self):
        self.round_flashcards = []
        self.current_index = 0
        self.correct_count = 0
        self.score = 0.0
        self.points_per_question = 0.0
        self.correct_answer = ""
        self.selected_answer = None

    def build_background(self):
        return ft.Image(
            src="background_images/space-wallpaper-stars-background.gif",
            fit=ft.BoxFit.COVER,
            expand=True,
        )

    def build_panel(self, content: ft.Control, width: int = 380):
        return ft.Container(
            content=content,
            width=width,
            padding=20,
            border_radius=20,
            bgcolor=self.panel_color,
            border=ft.Border.all(2, self.panel_border),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=18,
                color="#66000000",
                offset=ft.Offset(0, 6),
            ),
        )

    def main_button(self, text, on_click, icon=None):
        return ft.Button(
            content=text,
            icon=icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=self.button_color,
                color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=16,
            ),
            width=240,
        )

    def answer_button(self, text, on_click):
        return ft.Button(
            content=text,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=self.answer_button_color,
                color=ft.Colors.BLACK,
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=16,
            ),
            width=320,
        )

    # -------------------------
    # File import
    # -------------------------
    async def pick_txt_file(self, e):
        files = await self.file_picker.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["txt"],
            dialog_title="Select flashcard TXT file",
        )

        if not files:
            self.show_message("No file selected.")
            return

        file_path = files[0].path
        if not file_path:
            self.show_message("Could not read the selected file path.")
            return

        self.load_flashcards_from_file(file_path)

    def load_flashcards_from_file(self, file_path):
        loaded_flashcards = []

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) != 5:
                    continue

                question = parts[0].strip()
                correct = parts[1].strip()
                wrong1 = parts[2].strip()
                wrong2 = parts[3].strip()
                wrong3 = parts[4].strip()

                loaded_flashcards.append(
                    {
                        "question": question,
                        "correct": correct,
                        "choices": [correct, wrong1, wrong2, wrong3],
                    }
                )

            if not loaded_flashcards:
                self.show_message(
                    "No valid flashcards found. Use: Question|Correct|Wrong1|Wrong2|Wrong3"
                )
                return

            self.flashcards = loaded_flashcards
            self.show_message(f"{len(self.flashcards)} flashcards loaded.")
            self.open_round_dialog()

        except Exception as error:
            self.show_message(f"Failed to read file: {error}")

    # -------------------------
    # Round dialog
    # -------------------------
    def open_round_dialog(self):
        if not self.flashcards:
            self.show_message("No flashcards available.")
            return

        count_input = ft.TextField(
            label=f"How many flashcards this round? (1 to {len(self.flashcards)})",
            keyboard_type=ft.KeyboardType.NUMBER,
            autofocus=True,
        )

        def start_round(e):
            try:
                count = int(count_input.value)
            except Exception:
                self.show_message("Enter a valid number.")
                return

            if count < 1 or count > len(self.flashcards):
                self.show_message("Number is out of range.")
                return

            self.page.dialog.open = False
            self.start_quiz(count)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Start Round"),
            content=count_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.TextButton("Start", on_click=start_round),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def close_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    # -------------------------
    # Manual input
    # -------------------------
    def open_manual_input(self, e=None):
        self.current_screen = "manual"
        self.render()

    def add_manual_flashcard(self, e):
        question = self.manual_question.value.strip()
        correct = self.manual_correct.value.strip()
        wrong1 = self.manual_wrong1.value.strip()
        wrong2 = self.manual_wrong2.value.strip()
        wrong3 = self.manual_wrong3.value.strip()

        if not all([question, correct, wrong1, wrong2, wrong3]):
            self.show_message("Please fill in all fields.")
            return

        self.flashcards.append(
            {
                "question": question,
                "correct": correct,
                "choices": [correct, wrong1, wrong2, wrong3],
            }
        )

        self.manual_question.value = ""
        self.manual_correct.value = ""
        self.manual_wrong1.value = ""
        self.manual_wrong2.value = ""
        self.manual_wrong3.value = ""
        self.manual_count_text.value = f"Flashcards added: {len(self.flashcards)}"

        self.page.update()
        self.show_message("Flashcard added.")

    def finish_manual_input(self, e):
        if not self.flashcards:
            self.show_message("Please add at least one flashcard.")
            return
        self.open_round_dialog()

    # -------------------------
    # Quiz logic
    # -------------------------
    def start_quiz(self, count: int):
        self.reset_quiz_state()
        self.round_flashcards = random.sample(self.flashcards, count)
        self.points_per_question = 100 / len(self.round_flashcards)
        self.current_screen = "quiz"
        self.render()

    def check_answer(self, selected_answer: str):
        if selected_answer == self.correct_answer:
            self.correct_count += 1
            self.score = self.correct_count * self.points_per_question

            if self.correct_count == len(self.round_flashcards):
                self.score = 100.0

            self.show_message(f"Correct! +{self.points_per_question:.2f}")
        else:
            self.show_message(f"Wrong! Correct answer: {self.correct_answer}")

        self.current_index += 1

        if self.current_index >= len(self.round_flashcards):
            self.current_screen = "final"
        self.render()

    # -------------------------
    # Screens
    # -------------------------
    def build_menu_screen(self):
        content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Flashcard Maker App",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=self.title_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Choose how you want to prepare your flashcards.",
                    size=14,
                    color=self.text_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(color=ft.Colors.TRANSPARENT, height=8),
                ft.Text(
                    "TXT File Format Guide",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=self.title_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Each flashcard must be written on one line only.\n\n"
                    "Question|Correct Answer|Wrong1|Wrong2|Wrong3\n\n"
                    "Example:\n"
                    "What is 2 + 2?|4|3|5|6\n"
                    "What is the capital of France?|Paris|London|Berlin|Rome",
                    size=13,
                    color=self.text_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Note: Every line must have exactly 5 parts separated by |",
                    size=12,
                    italic=True,
                    color="#D6D6D6",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(color=ft.Colors.TRANSPARENT, height=4),
                self.main_button("Import TXT File", self.pick_txt_file, ft.Icons.UPLOAD_FILE),
                self.main_button("Manual Input", self.open_manual_input, ft.Icons.EDIT),
            ],
        )
        return self.build_panel(content)

    def build_manual_screen(self):
        self.manual_question = ft.TextField(label="Question", multiline=True, min_lines=2, max_lines=4)
        self.manual_correct = ft.TextField(label="Correct Answer")
        self.manual_wrong1 = ft.TextField(label="Wrong Choice 1")
        self.manual_wrong2 = ft.TextField(label="Wrong Choice 2")
        self.manual_wrong3 = ft.TextField(label="Wrong Choice 3")
        self.manual_count_text = ft.Text(
            f"Flashcards added: {len(self.flashcards)}",
            color=self.title_color,
            weight=ft.FontWeight.BOLD,
        )

        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Manual Flashcard Input",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=self.title_color,
                ),
                self.manual_question,
                self.manual_correct,
                self.manual_wrong1,
                self.manual_wrong2,
                self.manual_wrong3,
                self.manual_count_text,
                self.main_button("Add Flashcard", self.add_manual_flashcard, ft.Icons.ADD),
                self.main_button("Done / Start Quiz", self.finish_manual_input, ft.Icons.PLAY_ARROW),
                self.main_button("Back to Main Menu", lambda e: self.go_menu(), ft.Icons.HOME),
            ],
        )
        return self.build_panel(content, width=390)

    def build_quiz_screen(self):
        current = self.round_flashcards[self.current_index]
        self.correct_answer = current["correct"]
        choices = current["choices"][:]
        random.shuffle(choices)

        buttons = [
            self.answer_button(
                choice,
                lambda e, c=choice: self.check_answer(c),
            )
            for choice in choices
        ]

        content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    f"Flashcard {self.current_index + 1} of {len(self.round_flashcards)}",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=self.title_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    f"Score: {self.score:.2f}",
                    size=14,
                    color=self.text_color,
                ),
                ft.Container(
                    content=ft.Text(
                        current["question"],
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color="white",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    bgcolor="#111936CC",
                    border_radius=16,
                    padding=20,
                    margin=ft.margin.only(top=12, bottom=18),
                ),
                *buttons,
            ],
        )
        return self.build_panel(content)

    def build_final_screen(self):
        if self.correct_count == len(self.round_flashcards):
            self.score = 100.0
        else:
            self.score = self.correct_count * self.points_per_question

        content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    "Round Finished!",
                    size=26,
                    weight=ft.FontWeight.BOLD,
                    color=self.title_color,
                ),
                ft.Text(
                    f"Your Final Score: {self.score:.2f}",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color="white",
                ),
                ft.Text(
                    f"Correct Answers: {self.correct_count} out of {len(self.round_flashcards)}\n"
                    f"Points Per Correct Answer: {self.points_per_question:.2f}\n"
                    f"Total Possible Score: 100.00",
                    size=14,
                    color=self.text_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                self.main_button("Play Again", lambda e: self.open_round_dialog(), ft.Icons.REFRESH),
                self.main_button("Main Menu", lambda e: self.go_menu(), ft.Icons.HOME),
            ],
        )
        return self.build_panel(content)

    def go_menu(self):
        self.current_screen = "menu"
        self.render()

    # -------------------------
    # Render
    # -------------------------
    def render(self):
        if self.current_screen == "menu":
            panel = self.build_menu_screen()
        elif self.current_screen == "manual":
            panel = self.build_manual_screen()
        elif self.current_screen == "quiz":
            panel = self.build_quiz_screen()
        else:
            panel = self.build_final_screen()

        layout = ft.Stack(
            expand=True,
            controls=[
                self.build_background(),
                ft.SafeArea(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[panel],
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=20,
                        alignment=ft.Alignment.CENTER,
                    ),
                    expand=True,
                ),
            ],
        )

        self.page.controls.clear()
        self.page.add(layout)
        self.page.update()


def main(page: ft.Page):
    FlashcardFletApp(page)


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")