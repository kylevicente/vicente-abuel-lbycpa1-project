import asyncio
import random
from pathlib import Path

import flet as ft

try:
    import flet_audio as fta
    AUDIO_AVAILABLE = True
except Exception:
    fta = None
    AUDIO_AVAILABLE = False


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

        # Asset paths inside assets/
        self.background_src = "/background_images/space-wallpaper-stars-background.gif"
        self.menu_music_src = "/sounds/menu_music.mp3"
        self.quiz_music_src = "/sounds/quiz_music.mp3"
        self.correct_sound_src = "/sounds/correct.mp3"
        self.wrong_sound_src = "/sounds/wrong.mp3"

        self.background_file = self.assets_dir / "background_images" / "space-wallpaper-stars-background.gif"
        self.menu_music_file = self.assets_dir / "sounds" / "menu_music.mp3"
        self.quiz_music_file = self.assets_dir / "sounds" / "quiz_music.mp3"
        self.correct_sound_file = self.assets_dir / "sounds" / "correct.mp3"
        self.wrong_sound_file = self.assets_dir / "sounds" / "wrong.mp3"

        self.menu_music_data = None
        self.quiz_music_data = None
        self.correct_sound_data = None
        self.wrong_sound_data = None

        # Page setup
        self.page.title = "Flashcard Maker App"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.spacing = 0
        self.page.bgcolor = "black"
        self.page.scroll = ft.ScrollMode.AUTO

        try:
            self.page.window.width = 1280
            self.page.window.height = 720
        except Exception:
            pass

        # Audio setup
        self.audio_enabled = AUDIO_AVAILABLE
        self.current_music = None
        self.bgm = None
        self.correct_sfx = None
        self.wrong_sfx = None
        self.music_request_id = 0
        self.audio_message_shown = False
        self.desired_music = None
        self.pending_loaded_music = None

        if self.audio_enabled:
            self.setup_audio()

        try:
            self.page.on_connect = lambda e: self.schedule_music_for_current_screen(force=True)
        except Exception:
            pass

        try:
            self.page.on_app_lifecycle_state_change = lambda e: self.schedule_music_for_current_screen(force=True)
        except Exception:
            pass

        self.render()
        self.report_missing_assets_once()

        if self.audio_enabled:
            self.page.run_task(self.delayed_startup_music)
        else:
            self.show_message("Audio is off. Install with: pip install flet-audio")

    # ---------- compatibility helpers ----------
    def show_message(self, text: str):
        try:
            self.page.snack_bar = ft.SnackBar(ft.Text(text))
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            try:
                self.page.snack_bar = ft.SnackBar(content=ft.Text(text))
                self.page.snack_bar.open = True
                self.page.update()
            except Exception:
                print(text)

    def open_dialog(self, dialog: ft.AlertDialog):
        try:
            self.page.show_dialog(dialog)
        except Exception:
            self.page.dialog = dialog
            self.page.dialog.open = True
            self.page.update()

    def close_dialog(self):
        try:
            self.page.pop_dialog()
        except Exception:
            if getattr(self.page, "dialog", None):
                self.page.dialog.open = False
                self.page.update()

    def asset_exists(self, path_obj: Path) -> bool:
        return path_obj.exists() and path_obj.is_file()

    def load_asset_data(self, path_obj: Path):
        try:
            if self.asset_exists(path_obj):
                return path_obj.read_bytes()
        except Exception:
            pass
        return None

    def decode_bytes(self, data: bytes) -> str:
        try:
            return data.decode("utf-8")
        except Exception:
            return data.decode("latin-1", errors="replace")

    def center_alignment(self):
        try:
            return ft.alignment.center
        except Exception:
            return ft.Alignment(0, 0)

    def cover_fit(self):
        try:
            return ft.ImageFit.COVER
        except Exception:
            try:
                return ft.BoxFit.COVER
            except Exception:
                return None

    def border_all(self, width, color):
        try:
            return ft.border.all(width, color)
        except Exception:
            try:
                return ft.Border.all(width, color)
            except Exception:
                return None

    def is_ios_web(self) -> bool:
        try:
            platform_text = str(getattr(self.page, "platform", "")).lower()
        except Exception:
            platform_text = ""

        try:
            user_agent = (getattr(self.page, "client_user_agent", "") or "").lower()
        except Exception:
            user_agent = ""

        return bool(
            getattr(self.page, "web", False)
            and (
                "ios" in platform_text
                or "iphone" in platform_text
                or "ipad" in platform_text
                or "iphone" in user_agent
                or "ipad" in user_agent
            )
        )

    def music_target_for_screen(self) -> str | None:
        if self.current_screen in ("quiz", "final"):
            return "quiz"
        if self.current_screen in ("menu", "manual"):
            return "menu"
        return None

    def schedule_music_for_current_screen(self, force: bool = False):
        if not self.audio_enabled:
            return

        target = self.music_target_for_screen()
        if target:
            if not force and self.current_music == target:
                return
            self.page.run_task(self.switch_music_with_retry, target, force)

    # ---------- setup ----------
    def music_src_for(self, target: str):
        if target == "quiz":
            return self.quiz_music_data
        return self.menu_music_data

    def music_file_for(self, target: str):
        if target == "quiz":
            return self.quiz_music_file
        return self.menu_music_file

    def music_volume_for(self, target: str):
        if target == "quiz":
            return 0.35
        return 0.45

    def setup_audio(self):
        try:
            self.menu_music_data = self.load_asset_data(self.menu_music_file)
            self.quiz_music_data = self.load_asset_data(self.quiz_music_file)
            self.correct_sound_data = self.load_asset_data(self.correct_sound_file)
            self.wrong_sound_data = self.load_asset_data(self.wrong_sound_file)

            self.bgm = fta.Audio(
                src=None,
                volume=self.music_volume_for("menu"),
                autoplay=False,
                release_mode=fta.ReleaseMode.LOOP,
                on_loaded=self.on_bgm_loaded,
            )
            self.correct_sfx = fta.Audio(
                src=self.correct_sound_data,
                volume=0.9,
                autoplay=False,
                release_mode=fta.ReleaseMode.STOP,
            )
            self.wrong_sfx = fta.Audio(
                src=self.wrong_sound_data,
                volume=0.9,
                autoplay=False,
                release_mode=fta.ReleaseMode.STOP,
            )

            try:
                self.page.services.extend([self.bgm, self.correct_sfx, self.wrong_sfx])
                self.page.update()
            except Exception:
                pass
        except Exception as error:
            self.audio_enabled = False
            self.show_message(f"Audio setup failed: {error}")

    def report_missing_assets_once(self):
        missing = []
        if not self.asset_exists(self.background_file):
            missing.append("background")
        if not self.asset_exists(self.menu_music_file):
            missing.append("menu music")
        if not self.asset_exists(self.quiz_music_file):
            missing.append("quiz music")
        if not self.asset_exists(self.correct_sound_file):
            missing.append("correct sound")
        if not self.asset_exists(self.wrong_sound_file):
            missing.append("wrong sound")

        if missing:
            self.show_message(
                "Some assets are missing: " + ", ".join(missing) + "."
            )

    def reset_quiz_state(self):
        self.round_flashcards = []
        self.current_index = 0
        self.correct_count = 0
        self.score = 0.0
        self.points_per_question = 0.0
        self.correct_answer = ""

    # ---------- ui builders ----------
    def build_background(self):
        if self.asset_exists(self.background_file):
            return ft.Image(
                src=self.background_src,
                expand=True,
                fit=self.cover_fit(),
            )

        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1),
                end=ft.Alignment(1, 1),
                colors=["#01040D", "#061125", "#101C44"],
            ),
        )

    def build_panel(self, content: ft.Control, width: int = 430, height=None):
        return ft.Container(
            content=content,
            width=width,
            height=height,
            padding=20,
            border_radius=22,
            bgcolor=self.panel_color,
            border=self.border_all(2, self.panel_border),
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
        return ft.ElevatedButton(
            content=ft.Container(
                content=self.button_text(text, "white"),
                alignment=self.center_alignment(),
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
        return ft.ElevatedButton(
            content=ft.Container(
                content=self.button_text(text, "black"),
                alignment=self.center_alignment(),
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
    async def delayed_startup_music(self):
        if not self.audio_enabled:
            return
        for delay in (0.0, 0.15, 0.5, 1.0):
            if delay:
                await asyncio.sleep(delay)
            if self.current_screen not in ("menu", "manual"):
                return
            await self.switch_music_with_retry("menu", force=True)
            if self.current_music == "menu":
                return

    async def switch_music_with_retry(self, target: str, force: bool = False):
        if not self.audio_enabled or not self.bgm:
            return

        music_file = self.music_file_for(target)
        if not self.asset_exists(music_file):
            return

        if not force and self.current_music == target:
            self.desired_music = target
            return

        self.desired_music = target
        self.music_request_id += 1
        request_id = self.music_request_id

        for delay in (0.0, 0.12, 0.35, 0.8, 1.5):
            if delay > 0:
                await asyncio.sleep(delay)

            if request_id != self.music_request_id or self.desired_music != target:
                return

            ok = await self.switch_music_once(target, force=force)
            if ok:
                return

        if not self.audio_message_shown:
            self.audio_message_shown = True
            self.show_message(
                "Audio did not start automatically yet. Tap any button once and it should begin."
            )

    def on_bgm_loaded(self, e):
        target = self.pending_loaded_music or self.desired_music or self.music_target_for_screen()
        if not self.bgm or not target:
            return

        if getattr(self.bgm, "src", None) != self.music_src_for(target):
            return

        self.page.run_task(self.play_loaded_music, target)

    async def play_loaded_music(self, target: str) -> bool:
        if not self.bgm:
            return False

        wanted_src = self.music_src_for(target)
        if not wanted_src:
            return False

        try:
            self.bgm.volume = self.music_volume_for(target)
            try:
                await self.bgm.seek(0)
            except Exception:
                pass

            try:
                await self.bgm.play(0)
            except Exception:
                try:
                    await self.bgm.play()
                except Exception:
                    try:
                        await self.bgm.resume()
                    except Exception:
                        return False

            self.current_music = target
            self.pending_loaded_music = None
            self.audio_message_shown = False
            return True
        except Exception:
            return False

    async def switch_music_once(self, target: str, force: bool = False) -> bool:
        if not self.bgm:
            return False

        wanted_src = self.music_src_for(target)
        wanted_volume = self.music_volume_for(target)

        if not wanted_src:
            return False

        current_src = getattr(self.bgm, "src", None)
        src_changed = current_src != wanted_src

        if not force and self.current_music == target and not src_changed:
            return True

        try:
            self.bgm.volume = wanted_volume

            if src_changed:
                self.pending_loaded_music = target
                self.current_music = None

                try:
                    await self.bgm.pause()
                except Exception:
                    pass

                try:
                    await self.bgm.release()
                except Exception:
                    pass

                self.bgm.src = wanted_src
                try:
                    self.page.update()
                except Exception:
                    pass

                # Give the new bytes source time to load, then try to play it.
                for delay in (0.08, 0.18, 0.35):
                    await asyncio.sleep(delay)
                    if self.desired_music != target:
                        return False
                    ok = await self.play_loaded_music(target)
                    if ok:
                        return True

                return False

            return await self.play_loaded_music(target)
        except Exception:
            return False

    async def play_menu_music(self):
        await self.switch_music_with_retry("menu", force=True)

    async def play_quiz_music(self):
        await self.switch_music_with_retry("quiz", force=True)

    async def play_correct(self):
        if not self.audio_enabled or not self.correct_sfx:
            return
        if not self.asset_exists(self.correct_sound_file):
            return
        try:
            await self.correct_sfx.seek(0)
        except Exception:
            pass
        try:
            await self.correct_sfx.play()
        except Exception:
            try:
                await self.correct_sfx.resume()
            except Exception:
                pass

    async def play_wrong(self):
        if not self.audio_enabled or not self.wrong_sfx:
            return
        if not self.asset_exists(self.wrong_sound_file):
            return
        try:
            await self.wrong_sfx.seek(0)
        except Exception:
            pass
        try:
            await self.wrong_sfx.play()
        except Exception:
            try:
                await self.wrong_sfx.resume()
            except Exception:
                pass

    # ---------- import ----------
    async def browse_txt_file(self, e=None):
        if self.is_ios_web():
            self.show_message(
                "TXT browse is unreliable in iPhone/iPad web preview right now. Please use Paste TXT or Manual Input on iOS."
            )
            return

        try:
            picker = ft.FilePicker()
            try:
                self.page.services.append(picker)
            except Exception:
                pass

            picker_kwargs = {
                "allow_multiple": False,
                "dialog_title": "Choose a TXT flashcard file",
            }

            file_type_enum = getattr(ft, "FilePickerFileType", None)
            if file_type_enum is not None:
                picker_kwargs["file_type"] = file_type_enum.CUSTOM
                picker_kwargs["allowed_extensions"] = ["txt"]

            try:
                picker_kwargs["with_data"] = True
                files = await picker.pick_files(**picker_kwargs)
            except TypeError:
                picker_kwargs.pop("with_data", None)
                files = await picker.pick_files(**picker_kwargs)

        except Exception as error:
            self.show_message(
                f"Browse failed: {error}. Use Load From Path or paste the TXT content instead."
            )
            return

        if not files:
            self.show_message("No file selected.")
            return

        selected = files[0]
        file_path = getattr(selected, "path", None)
        file_bytes = getattr(selected, "bytes", None)

        if file_bytes:
            raw_text = self.decode_bytes(file_bytes)
            if self.load_flashcards_from_text(raw_text):
                self.open_round_dialog()
            return

        if file_path:
            self.load_flashcards_from_file(file_path)
            return

        self.show_message(
            "Could not read the selected file. Use Load From Path on desktop or paste the TXT content instead."
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
            for line in raw_text.splitlines():
                line = line.strip()
                if not line:
                    continue

                parts = [part.strip() for part in line.split("|")]
                if len(parts) != 5:
                    continue

                question, correct, wrong1, wrong2, wrong3 = parts
                choices = [correct, wrong1, wrong2, wrong3]

                if not question or not all(choices):
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
                    "No valid flashcards found. Use: Question|Correct|Wrong1|Wrong2|Wrong3"
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
            try:
                count = int((count_input.value or "").strip())
            except Exception:
                self.show_message("Enter a valid whole number.")
                return

            if count < 1 or count > len(self.flashcards):
                self.show_message("Number is out of range.")
                return

            self.close_dialog()
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
        self.open_dialog(dialog)

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
                    "Use Browse on desktop and Android. If Browse is not supported, use Load From Path or paste the TXT content.",
                    size=12,
                    italic=True,
                    color=self.subtle_text,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "On iPhone/iPad web preview, TXT browsing may not return the selected file. Paste the TXT content instead.",
                    size=12,
                    italic=True,
                    color=self.subtle_text,
                    text_align=ft.TextAlign.CENTER,
                    visible=self.is_ios_web(),
                ),
                self.main_button(
                    "Browse TXT File",
                    self.browse_txt_file,
                ) if not self.is_ios_web() else ft.Container(),
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

        return self.build_panel(content, width=430, height=630)

    def build_quiz_screen(self):
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
                    alignment=self.center_alignment(),
                    content=ft.SafeArea(
                        content=ft.Container(
                            alignment=self.center_alignment(),
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
        self.schedule_music_for_current_screen()


def main(page: ft.Page):
    FlashcardFletApp(page)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
