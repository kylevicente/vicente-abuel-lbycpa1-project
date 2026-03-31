import random
from pathlib import Path
import flet as ft

try:
    import flet_audio as fta
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False


class FlashcardFletApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.base_dir = Path(__file__).parent

        # Data
        self.flashcards = []
        self.round_flashcards = []
        self.current_index = 0
        self.correct_count = 0
        self.score = 0.0
        self.points_per_question = 0.0
        self.correct_answer = ""

        # Screen state
        self.current_screen = "menu"

        # Theme
        self.panel_color = "#061125DD"
        self.panel_border = "#7E6BFF"
        self.title_color = "#B6CCFF"
        self.text_color = "white"
        self.subtle_text = "#D0D0D0"
        self.button_color = "#4CAF50"
        self.answer_button_color = "#FFD966"

        # Assets
        self.background_src = "background_images/space-wallpaper-stars-background.gif"
        self.menu_music_src = "sounds/menu_music.mp3"
        self.quiz_music_src = "sounds/quiz_music.mp3"
        self.correct_sound_src = "sounds/correct.mp3"
        self.wrong_sound_src = "sounds/wrong.mp3"

        # Audio
        self.audio_enabled = AUDIO_AVAILABLE
        self.current_music = None
        if self.audio_enabled:
            self.menu_music = fta.Audio(src=self.menu_music_src, volume=0.5)
            self.quiz_music = fta.Audio(src=self.quiz_music_src, volume=0.4)
            self.correct_sfx = fta.Audio(src=self.correct_sound_src, volume=0.8)
            self.wrong_sfx = fta.Audio(src=self.wrong_sound_src, volume=0.8)
            self.page.services.extend(
                [self.menu_music, self.quiz_music, self.correct_sfx, self.wrong_sfx]
            )

        # File picker: only add if supported
        self.file_picker = None
        try:
            self.file_picker = ft.FilePicker()
            self.page.overlay.append(self.file_picker)
        except Exception:
            self.file_picker = None

        # Page setup
        self.page.title = "Flashcard Maker App"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        self.page.bgcolor = "black"
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.window.width = 1280
        self.page.window.height = 720

        self.render()

        if not self.audio_enabled:
            self.show_message("Audio is off. Install with: pip install flet-audio")
        else:
            self.page.run_task(self.play_menu_music)

    # ---------- helpers ----------
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

    def build_background(self):
        # Use explicit width/height so the image fills instead of staying small at top-left.
        width = self.page.window.width or 1280
        height = self.page.window.height or 720
        return ft.Image(
            src=self.background_src,
            width=width,
            height=height,
            fit=ft.BoxFit.COVER,
        )

    def build_panel(self, content: ft.Control, width: int = 430, height: int | None = None):
        return ft.Container(
            content=content,
            width=width,
            height=height,
            padding=20,
            border_radius=22,
            bgcolor=self.panel_color,
            border=ft.Border.all(2, self.panel_border),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=18,
                color="#66000000",
                offset=ft.Offset(0, 6),
            ),
        )

    def button_text(self, text, color):
        return ft.Text(
            text,
            color=color,
            size=14,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )

    def main_button(self, text, on_click):
        return ft.Button(
            content=ft.Container(
                content=self.button_text(text, "white"),
                alignment=ft.Alignment(0, 0),
            ),
            on_click=on_click,
            width=260,
            style=ft.ButtonStyle(
                bgcolor=self.button_color,
                color="white",
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=16,
            ),
        )

    def answer_button(self, text, on_click):
        return ft.Button(
            content=ft.Container(
                content=self.button_text(text, "black"),
                alignment=ft.Alignment(0, 0),
            ),
            on_click=on_click,
            width=340,
            style=ft.ButtonStyle(
                bgcolor=self.answer_button_color,
                color="black",
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=16,
            ),
        )

    # ---------- audio ----------
    async def _stop_music(self):
        if not self.audio_enabled:
            return
        try:
            await self.menu_music.release()
        except Exception:
            pass
        try:
            await self.quiz_music.release()
        except Exception:
            pass
        self.current_music = None

    async def play_menu_music(self):
        if not self.audio_enabled or self.current_music == "menu":
            return
        try:
            await self.quiz_music.release()
        except Exception:
            pass
        try:
            await self.menu_music.play()
            self.current_music = "menu"
        except Exception as error:
            self.show_message(f"Menu music failed: {error}")

    async def play_quiz_music(self):
        if not self.audio_enabled or self.current_music == "quiz":
            return
        try:
            await self.menu_music.release()
        except Exception:
            pass
        try:
            await self.quiz_music.play()
            self.current_music = "quiz"
        except Exception as error:
            self.show_message(f"Quiz music failed: {error}")

    async def play_correct(self):
        if not self.audio_enabled:
            return
        try:
            await self.correct_sfx.play()
        except Exception:
            pass

    async def play_wrong(self):
        if not self.audio_enabled:
            return
        try:
            await self.wrong_sfx.play()
        except Exception:
            pass

    # ---------- import ----------
    async def browse_txt_file(self, e=None):
        if self.file_picker is None:
            self.show_message("Browse is not supported here. Use Load From Path instead.")
            return

        try:
            files = await self.file_picker.pick_files(allow_multiple=False)
        except Exception as error:
            self.show_message(f"Browse failed: {error}. Use Load From Path instead.")
            return

        if not files:
            self.show_message("No file selected.")
            return

        file_path = files[0].path
        if not file_path:
            self.show_message("Could not read the selected file path.")
            return

        self.load_flashcards_from_file(file_path)

    def load_from_path(self, e=None):
        file_path = (self.path_box.value or "").strip()
        if not file_path:
            self.show_message("Paste a TXT file path first.")
            return
        self.load_flashcards_from_file(file_path)

    def load_pasted_txt(self, e=None):
        raw_text = (self.paste_box.value or "").strip()
        if not raw_text:
            self.show_message("Paste your TXT content first.")
            return
        if self.load_flashcards_from_text(raw_text):
            self.open_round_dialog()

    def load_flashcards_from_file(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                raw_text = file.read()
        except Exception as error:
            self.show_message(f"Failed to read file: {error}")
            return

        if self.load_flashcards_from_text(raw_text):
            self.open_round_dialog()

    def load_flashcards_from_text(self, raw_text: str):
        loaded_flashcards = []

        try:
            for line in raw_text.splitlines():
                line = line.strip()
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) != 5:
                    continue

                loaded_flashcards.append(
                    {
                        "question": parts[0].strip(),
                        "correct": parts[1].strip(),
                        "choices": [
                            parts[1].strip(),
                            parts[2].strip(),
                            parts[3].strip(),
                            parts[4].strip(),
                        ],
                    }
                )

            if not loaded_flashcards:
                self.show_message("No valid flashcards found. Use Question|Correct|Wrong1|Wrong2|Wrong3")
                return False

            self.flashcards = loaded_flashcards
            self.show_message(f"{len(self.flashcards)} flashcards loaded.")
            return True

        except Exception as error:
            self.show_message(f"Failed to load text: {error}")
            return False

    # ---------- round dialog ----------
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
            self.page.update()
            self.start_quiz(count)

        self.page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Start Round"),
            content=count_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.close_dialog()),
                ft.TextButton("Start", on_click=start_round),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog.open = True
        self.page.update()

    def close_dialog(self):
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()

    # ---------- manual ----------
    def open_manual_input(self, e=None):
        self.current_screen = "manual"
        self.render()

    def add_manual_flashcard(self, e):
        question = (self.manual_question.value or "").strip()
        correct = (self.manual_correct.value or "").strip()
        wrong1 = (self.manual_wrong1.value or "").strip()
        wrong2 = (self.manual_wrong2.value or "").strip()
        wrong3 = (self.manual_wrong3.value or "").strip()

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

    # ---------- quiz ----------
    def start_quiz(self, count: int):
        self.reset_quiz_state()
        self.round_flashcards = random.sample(self.flashcards, count)
        self.points_per_question = 100 / len(self.round_flashcards)
        self.current_screen = "quiz"
        self.render()
        if self.audio_enabled:
            self.page.run_task(self.play_quiz_music)

    def check_answer(self, selected_answer: str):
        if selected_answer == self.correct_answer:
            self.correct_count += 1
            self.score = self.correct_count * self.points_per_question
            if self.correct_count == len(self.round_flashcards):
                self.score = 100.0
            self.show_message(f"Correct! +{self.points_per_question:.2f}")
            if self.audio_enabled:
                self.page.run_task(self.play_correct)
        else:
            self.show_message(f"Wrong! Correct answer: {self.correct_answer}")
            if self.audio_enabled:
                self.page.run_task(self.play_wrong)

        self.current_index += 1
        if self.current_index >= len(self.round_flashcards):
            self.current_screen = "final"
        self.render()

    # ---------- screens ----------
    def build_menu_screen(self):
        self.path_box = ft.TextField(
            label="Import from TXT file path",
            width=360,
            hint_text=r"Example: C:\Users\Kyle\Desktop\flashcards.txt",
        )
        self.paste_box = ft.TextField(
            label="Paste TXT flashcards here",
            multiline=True,
            min_lines=6,
            max_lines=10,
            width=360,
            hint_text="Question|Correct Answer|Wrong1|Wrong2|Wrong3",
        )

        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Flashcard Maker App", size=30, weight=ft.FontWeight.BOLD, color=self.title_color),
                ft.Text(
                    "Choose how you want to prepare your flashcards.",
                    size=15,
                    color=self.text_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text("TXT File Format Guide", size=18, weight=ft.FontWeight.BOLD, color=self.title_color),
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
                    "Use Browse if it works on your system. If not, use Load From Path or paste the TXT content.",
                    size=12,
                    italic=True,
                    color=self.subtle_text,
                    text_align=ft.TextAlign.CENTER,
                ),
                self.main_button("Browse TXT File", self.browse_txt_file),
                self.path_box,
                self.main_button("Load From Path", self.load_from_path),
                self.paste_box,
                self.main_button("Load Pasted TXT", self.load_pasted_txt),
                self.main_button("Manual Input", self.open_manual_input),
            ],
        )

        return self.build_panel(content, width=430, height=630)

    def build_manual_screen(self):
        self.manual_question = ft.TextField(label="Question", multiline=True, min_lines=2, max_lines=4)
        self.manual_correct = ft.TextField(label="Correct Answer")
        self.manual_wrong1 = ft.TextField(label="Wrong Choice 1")
        self.manual_wrong2 = ft.TextField(label="Wrong Choice 2")
        self.manual_wrong3 = ft.TextField(label="Wrong Choice 3")
        self.manual_count_text = ft.Text(f"Flashcards added: {len(self.flashcards)}", color=self.title_color, weight=ft.FontWeight.BOLD)

        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Manual Flashcard Input", size=24, weight=ft.FontWeight.BOLD, color=self.title_color),
                self.manual_question,
                self.manual_correct,
                self.manual_wrong1,
                self.manual_wrong2,
                self.manual_wrong3,
                self.manual_count_text,
                self.main_button("Add Flashcard", self.add_manual_flashcard),
                self.main_button("Done / Start Quiz", self.finish_manual_input),
                self.main_button("Back to Main Menu", lambda e: self.go_menu()),
            ],
        )

        return self.build_panel(content, width=430, height=630)

    def build_quiz_screen(self):
        current = self.round_flashcards[self.current_index]
        self.correct_answer = current["correct"]
        choices = current["choices"][:]
        random.shuffle(choices)

        buttons = [self.answer_button(choice, lambda e, c=choice: self.check_answer(c)) for choice in choices]

        content = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text(
                    f"Flashcard {self.current_index + 1} of {len(self.round_flashcards)}",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=self.title_color,
                ),
                ft.Text(f"Score: {self.score:.2f}", size=14, color=self.text_color),
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

        return self.build_panel(content, width=430, height=560)

    def build_final_screen(self):
        if self.correct_count == len(self.round_flashcards):
            self.score = 100.0
        else:
            self.score = self.correct_count * self.points_per_question

        content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("Round Finished!", size=26, weight=ft.FontWeight.BOLD, color=self.title_color),
                ft.Text(f"Your Final Score: {self.score:.2f}", size=20, weight=ft.FontWeight.BOLD, color="white"),
                ft.Text(
                    f"Correct Answers: {self.correct_count} out of {len(self.round_flashcards)}\n"
                    f"Points Per Correct Answer: {self.points_per_question:.2f}\n"
                    f"Total Possible Score: 100.00",
                    size=14,
                    color=self.text_color,
                    text_align=ft.TextAlign.CENTER,
                ),
                self.main_button("Play Again", lambda e: self.open_round_dialog()),
                self.main_button("Main Menu", lambda e: self.go_menu()),
            ],
        )

        return self.build_panel(content, width=430, height=420)

    def go_menu(self):
        self.current_screen = "menu"
        self.render()
        if self.audio_enabled:
            self.page.run_task(self.play_menu_music)

    # ---------- render ----------
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
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                    content=ft.SafeArea(
                        content=ft.Container(
                            alignment=ft.Alignment(0, 0),
                            content=panel,
                        ),
                        expand=True,
                    ),
                ),
            ],
        )

        self.page.controls.clear()
        self.page.add(layout)
        self.page.update()


def main(page: ft.Page):
    FlashcardFletApp(page)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
