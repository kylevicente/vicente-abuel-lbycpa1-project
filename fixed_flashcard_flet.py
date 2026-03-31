import random
from pathlib import Path
import flet as ft


class FlashcardFletApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.base_dir = Path(__file__).resolve().parent
        self.assets_dir = self.base_dir / "assets"

        # Data
        self.flashcards = []
        self.round_flashcards = []
        self.current_index = 0
        self.correct_count = 0
        self.score = 0.0
        self.points_per_question = 0.0
        self.correct_answer = ""

        # State
        self.current_screen = "menu"

        # Theme
        self.panel_color = "#061125DD"
        self.panel_border = "#7E6BFF"
        self.title_color = "#B6CCFF"
        self.text_color = "white"
        self.subtle_text = "#D0D0D0"
        self.button_color = "#4CAF50"
        self.answer_button_color = "#FFD966"

        # Asset paths inside /assets
        # IMPORTANT: Flet asset paths should start with "/".
        self.background_src = "/background_images/space-wallpaper-stars-background.gif"
        self.menu_music_src = "/sounds/menu_music.mp3"
        self.quiz_music_src = "/sounds/quiz_music.mp3"
        self.correct_sound_src = "/sounds/correct.mp3"
        self.wrong_sound_src = "/sounds/wrong.mp3"

        # Keep a file-system check too, so missing assets fail gracefully.
        self.background_file = self.assets_dir / "background_images" / "space-wallpaper-stars-background.gif"
        self.menu_music_file = self.assets_dir / "sounds" / "menu_music.mp3"
        self.quiz_music_file = self.assets_dir / "sounds" / "quiz_music.mp3"
        self.correct_sound_file = self.assets_dir / "sounds" / "correct.mp3"
        self.wrong_sound_file = self.assets_dir / "sounds" / "wrong.mp3"

        # Page setup
        self.page.title = "Flashcard Maker App"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        self.page.bgcolor = "black"
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER

        # Window settings are desktop-only; guard them.
        try:
            self.page.window.width = 1280
            self.page.window.height = 720
        except Exception:
            pass

        # Audio using built-in Flet Audio service.
        self.audio_supported = hasattr(ft, "Audio")
        self.music_enabled = self.audio_supported
        self.current_music_name = None

        if self.audio_supported:
            release_mode_stop = None
            try:
                release_mode_stop = ft.audio.ReleaseMode.STOP
            except Exception:
                try:
                    release_mode_stop = ft.ReleaseMode.STOP
                except Exception:
                    release_mode_stop = None

            self.menu_music = ft.Audio(src=self.menu_music_src, volume=0.45, autoplay=False)
            self.quiz_music = ft.Audio(src=self.quiz_music_src, volume=0.35, autoplay=False)
            self.correct_sfx = ft.Audio(src=self.correct_sound_src, volume=0.9, autoplay=False)
            self.wrong_sfx = ft.Audio(src=self.wrong_sound_src, volume=0.9, autoplay=False)

            if release_mode_stop is not None:
                self.menu_music.release_mode = release_mode_stop
                self.quiz_music.release_mode = release_mode_stop
                self.correct_sfx.release_mode = release_mode_stop
                self.wrong_sfx.release_mode = release_mode_stop

            self.page.services.extend(
                [self.menu_music, self.quiz_music, self.correct_sfx, self.wrong_sfx]
            )

        # File picker must use on_result instead of awaiting a return value.
        self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result)
        self.page.overlay.append(self.file_picker)
        self.page.update()

        self.render()
        self.report_missing_assets_once()

        if self.audio_supported:
            self.page.run_task(self.play_menu_music)
        else:
            self.show_message("Audio control is not available in this Flet installation.")

    # ---------- small helpers ----------
    def show_message(self, text: str):
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(text),
                duration=2500,
            )
        )

    def report_missing_assets_once(self):
        missing = []
        if not self.background_file.exists():
            missing.append(str(self.background_file))
        if not self.menu_music_file.exists():
            missing.append(str(self.menu_music_file))
        if not self.quiz_music_file.exists():
            missing.append(str(self.quiz_music_file))
        if not self.correct_sound_file.exists():
            missing.append(str(self.correct_sound_file))
        if not self.wrong_sound_file.exists():
            missing.append(str(self.wrong_sound_file))

        if missing:
            self.show_message(
                "Some assets are missing. Background/audio will fall back until these files exist in the assets folder."
            )

    def reset_quiz_state(self):
        self.round_flashcards = []
        self.current_index = 0
        self.correct_count = 0
        self.score = 0.0
        self.points_per_question = 0.0
        self.correct_answer = ""

    def asset_exists(self, file_path: Path) -> bool:
        return file_path.exists() and file_path.is_file()

    def build_background(self):
        if self.asset_exists(self.background_file):
            return ft.Image(
                src=self.background_src,
                expand=True,
                fit=ft.ImageFit.COVER,
            )

        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#01040D", "#061125", "#101C44"],
            ),
        )

    def build_panel(self, content: ft.Control, width: int = 430, height: int | None = None):
        return ft.Container(
            content=content,
            width=width,
            height=height,
            padding=20,
            border_radius=22,
            bgcolor=self.panel_color,
            border=ft.border.all(2, self.panel_border),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=18,
                color="#66000000",
                offset=ft.Offset(0, 6),
            ),
        )

    def button_text(self, text: str, color: str):
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
                alignment=ft.Alignment.center,
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
                alignment=ft.Alignment.center,
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
    async def stop_all_audio(self):
        if not self.audio_supported:
            return
        for audio in [self.menu_music, self.quiz_music, self.correct_sfx, self.wrong_sfx]:
            try:
                await audio.pause()
                await audio.seek(0)
            except Exception:
                pass
        self.current_music_name = None

    async def play_menu_music(self):
        if not self.audio_supported:
            return
        if not self.asset_exists(self.menu_music_file):
            return
        if self.current_music_name == "menu":
            return
        try:
            try:
                await self.quiz_music.pause()
                await self.quiz_music.seek(0)
            except Exception:
                pass
            await self.menu_music.seek(0)
            await self.menu_music.play()
            self.current_music_name = "menu"
        except Exception as error:
            self.show_message(f"Menu music failed: {error}")

    async def play_quiz_music(self):
        if not self.audio_supported:
            return
        if not self.asset_exists(self.quiz_music_file):
            return
        if self.current_music_name == "quiz":
            return
        try:
            try:
                await self.menu_music.pause()
                await self.menu_music.seek(0)
            except Exception:
                pass
            await self.quiz_music.seek(0)
            await self.quiz_music.play()
            self.current_music_name = "quiz"
        except Exception as error:
            self.show_message(f"Quiz music failed: {error}")

    async def play_correct(self):
        if not self.audio_supported or not self.asset_exists(self.correct_sound_file):
            return
        try:
            await self.correct_sfx.seek(0)
            await self.correct_sfx.play()
        except Exception:
            pass

    async def play_wrong(self):
        if not self.audio_supported or not self.asset_exists(self.wrong_sound_file):
            return
        try:
            await self.wrong_sfx.seek(0)
            await self.wrong_sfx.play()
        except Exception:
            pass

    # ---------- import ----------
    def browse_txt_file(self, e=None):
        try:
            self.file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["txt"],
                dialog_title="Choose a TXT flashcard file",
            )
        except Exception as error:
            self.show_message(f"Browse failed: {error}. Use Load From Path or paste the text instead.")

    def on_file_picker_result(self, e: ft.FilePickerResultEvent):
        if not e.files:
            self.show_message("No file selected.")
            return

        selected = e.files[0]
        file_path = getattr(selected, "path", None)

        if file_path:
            self.load_flashcards_from_file(file_path)
            return

        # In some mobile/web cases no path is exposed.
        self.show_message(
            "This platform did not return a readable file path. Use Load From Path on desktop or paste the TXT content instead."
        )

    def load_from_path(self, e=None):
        file_path = (self.path_box.value or "").strip().strip('"')
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
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as file:
                    raw_text = file.read()
            except Exception as error:
                self.show_message(f"Failed to read file: {error}")
                return
        except Exception as error:
            self.show_message(f"Failed to read file: {error}")
            return

        if self.load_flashcards_from_text(raw_text):
            self.open_round_dialog()

    def load_flashcards_from_text(self, raw_text: str):
        loaded_flashcards = []

        try:
            for line_number, line in enumerate(raw_text.splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue

                parts = [part.strip() for part in line.split("|")]
                if len(parts) != 5:
                    continue

                question, correct, wrong1, wrong2, wrong3 = parts
                choices = [correct, wrong1, wrong2, wrong3]

                # Ignore bad rows with empty values or duplicate choices.
                if not all(choices) or not question:
                    continue
                if len(set(choices)) < 4:
                    continue

                loaded_flashcards.append(
                    {
                        "question": question,
                        "correct": correct,
                        "choices": choices,
                    }
                )

            if not loaded_flashcards:
                self.show_message(
                    "No valid flashcards found. Use this format per line: Question|Correct|Wrong1|Wrong2|Wrong3"
                )
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
            raw_value = (count_input.value or "").strip()
            try:
                count = int(raw_value)
            except Exception:
                self.show_message("Enter a valid whole number.")
                return

            if count < 1 or count > len(self.flashcards):
                self.show_message("Number is out of range.")
                return

            self.page.pop_dialog()
            self.start_quiz(count)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Start Round"),
            content=count_input,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog()),
                ft.TextButton("Start", on_click=start_round),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

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

        if len({correct, wrong1, wrong2, wrong3}) < 4:
            self.show_message("All four answer choices must be different.")
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
        if not self.flashcards:
            self.show_message("There are no flashcards to start.")
            return

        self.reset_quiz_state()
        self.round_flashcards = random.sample(self.flashcards, count)
        self.points_per_question = 100 / len(self.round_flashcards)
        self.current_screen = "quiz"
        self.render()

        if self.audio_supported:
            self.page.run_task(self.play_quiz_music)

    def check_answer(self, selected_answer: str):
        if selected_answer == self.correct_answer:
            self.correct_count += 1
            self.score = self.correct_count * self.points_per_question
            if self.correct_count == len(self.round_flashcards):
                self.score = 100.0
            self.show_message(f"Correct! +{self.points_per_question:.2f}")
            if self.audio_supported:
                self.page.run_task(self.play_correct)
        else:
            self.show_message(f"Wrong! Correct answer: {self.correct_answer}")
            if self.audio_supported:
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
                    "Browse usually works best on desktop. On some mobile/web setups, use Load From Path or paste the TXT content.",
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

        return self.build_panel(content, width=430, height=640)

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

        return self.build_panel(content, width=430, height=640)

    def build_quiz_screen(self):
        if not self.round_flashcards:
            return self.build_panel(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("No quiz round is active.", color="white", size=20),
                        self.main_button("Back to Main Menu", lambda e: self.go_menu()),
                    ],
                ),
                width=430,
                height=260,
            )

        current = self.round_flashcards[self.current_index]
        self.correct_answer = current["correct"]
        choices = current["choices"][:]
        random.shuffle(choices)

        buttons = [
            self.answer_button(choice, lambda e, c=choice: self.check_answer(c))
            for choice in choices
        ]

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

        return self.build_panel(content, width=430, height=580)

    def build_final_screen(self):
        if self.round_flashcards:
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
        if self.audio_supported:
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
                    alignment=ft.Alignment.center,
                    content=ft.SafeArea(
                        content=ft.Container(
                            alignment=ft.Alignment.center,
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
