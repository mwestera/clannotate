import sys
import csv
import os
import json

from textual.app import App, ComposeResult
from textual.widgets import Markdown, Static, Input, Button, ProgressBar, Rule, Footer, Header
from textual.containers import Vertical, Horizontal
from textual import events, on


class AnnotationApp(App):
    CSS = """
    #container {
        align: center middle;
        margin: 1 2 1 2;
    }
    Input {
        width: 80%;
    }
    Button {
        margin: 0 2 0 2;
    }
    """

    def __init__(self, items, progress_file=None, rating_tiers=('rating',)):
        super().__init__()

        self.progress_file = progress_file
        self.lines = ['\n\n'.join(map(str, item)) for item in items]
        self.rating_tiers = rating_tiers

        self.annotations, self.current_index = self.load_progress() if os.path.exists(self.progress_file) else ([([None for _ in rating_tiers] + ['']) for _ in self.lines], 0)

        self.progress_bar = ProgressBar(len(self.lines), id='progress-bar', show_eta=False)
        self.line_display = Markdown(id="line-display")
        self.line_input = Input(id="line-input")    # placeholder="Comment (optional)",

        self.line_display.styles.border = ("solid", "green")
        self.line_display.styles.padding = 0, 1, 0, 1
        self.line_display.border_title = "Item X"

        self.line_input.border_title = "Comment"
        self.line_input.styles.padding = 0, 1, 0, 1
        self.line_input.styles.border = ("solid", "green")

        self.rating_button_groups = []
        self.rating_panels = []

        for i, rating_name in enumerate(rating_tiers):
            bad_button = Button("Bad")
            mwah_button = Button("Mwah")
            good_button = Button("Good")
            # TODO: Use an actual radio button group?
            self.rating_button_groups.append([(bad_button, -1), (mwah_button, 0), (good_button, 1)])
            self.rating_panels.append(Vertical(Static(rating_name), Horizontal(bad_button, mwah_button, good_button), id=f'panel{i}'))

        delete_button = Button("Delete", id="del-btn")

        self.buttonbar = Horizontal(
                *self.rating_panels,
                delete_button,
            )
        self.buttonbar.styles.margin = (1, 2, 0, 2)

        home_button = Button("First", id="home-btn")
        prev_button = Button("Previous", id="prev-btn")
        next_button = Button("Next", id="next-btn")
        end_button = Button("New/Last", id="last-btn")

        save_button = Button("Save", id="save-btn")
        load_button = Button("Load", id="load-btn")

        self.navbar = Horizontal(
            home_button, prev_button, next_button, end_button,
            Vertical(self.progress_bar,),
            *([save_button, load_button] if self.progress_file else [])
        )

        # TODO: Use textual.binding.Binding instead?
        self.hotkeys = {
            'enter': next_button,
            'alt+right': next_button,
            'alt+left': prev_button,
            'alt+up': home_button,
            'alt+down': end_button,
            'f1': self.rating_button_groups[0][0][0],
            'f2': self.rating_button_groups[0][1][0],
            'f3': self.rating_button_groups[0][2][0],
            'alt+delete': delete_button,
            'ctrl+s': save_button,
            'ctrl+l': load_button,
        }
        if len(self.rating_tiers) > 1:
            self.hotkeys.update({
                'f4': self.rating_button_groups[1][0][0],
                'f5': self.rating_button_groups[1][1][0],
                'f6': self.rating_button_groups[1][2][0],
            })
        if len(self.rating_tiers) > 2:
            self.hotkeys.update({
                'f7': self.rating_button_groups[2][0][0],
                'f8': self.rating_button_groups[2][1][0],
                'f9': self.rating_button_groups[2][2][0],
            })

        for hotkey, button in self.hotkeys.items():
            button.tooltip = hotkey

    def compose(self) -> ComposeResult:
        yield Vertical(
            self.navbar,
            # Rule(line_style="heavy"),
            self.line_display,
            # Rule(line_style="heavy"),
            self.line_input,
            self.buttonbar,
            # Footer(),
            id='container',
        )

    def get_first_unannotated_index(self):
        empty = ([None] * len(self.rating_button_groups)) + ['']
        return self.annotations.index(empty) if empty in self.annotations else None

    @on(Input.Changed)
    def save_input(self, event: Input.Changed) -> None:
        if event.input == self.line_input:
            self.annotations[self.current_index][-1] = event.value

    async def on_button_pressed(self, event):
        for i, rating_button_group in enumerate(self.rating_button_groups):
            for button, rating in rating_button_group:
                if event.button == button:
                    if self.annotations[self.current_index][i] == rating:
                        self.annotations[self.current_index][i] = None
                    else:
                        self.annotations[self.current_index][i] = rating
                    self.update()
                    return

        if event.button.id == "del-btn":
            self.annotations[self.current_index] = [None for _ in self.rating_button_groups] + ['']
            self.line_input.value = ''
        elif event.button.id == "home-btn":
            self.current_index = 0
        elif event.button.id == "prev-btn":
            self.current_index -= 1
        elif event.button.id == "next-btn":
            self.current_index += 1
        elif event.button.id == "last-btn":
            the_index = self.get_first_unannotated_index()
            self.current_index = the_index if the_index is not None and the_index != self.current_index else -1

        elif event.button.id == "save-btn":
            self.save_progress()
        elif event.button.id == "load-btn":
            self.annotations, self.current_index = self.load_progress()
        else:
            return

        self.update()

    @on(events.Mount)
    def update(self):
        self.title = "Command-line Annotation"

        self.current_index = self.current_index % len(self.lines)

        self.progress_bar.update(progress=sum(any(x for x in a) for a in self.annotations))
        self.line_display.border_title = f'Item {self.current_index}.'

        self.line_input.value = self.annotations[self.current_index][-1]
        self.line_input.focus()
        self.line_display.update(self.lines[self.current_index])

        for i, button_group in enumerate(self.rating_button_groups):
            for button, score in button_group:
                button.variant = 'success' if self.annotations[self.current_index][i] == score else 'default'

    async def on_key(self, event: events.Key) -> None:
        if button := self.hotkeys.get(event.key):
            button.press()

    def save_progress(self):
        # TODO: Save more info about the annotations, like rating tiers?
        with open(self.progress_file, 'w') as file:
            file.write(json.dumps(
                {'annotations': self.annotations, 'current_index': self.current_index}
            ))

    def load_progress(self):
        with open(self.progress_file, 'r') as file:
            d = json.loads(file.read())
        return d['annotations'], d['current_index']


def main():

    import argparse

    parser = argparse.ArgumentParser(description="CLI app for data annotation.")
    parser.add_argument("file", type=argparse.FileType('r'), help="File with lines to annotate, or named pipe (stdin not allowed)")
    parser.add_argument('--csv', action='store_true', help='If input file has .csv format. Automatically inferred from file extension.')
    parser.add_argument('-y', '--yes', action='store_true', help='To overwrite savefile if exists.')
    parser.add_argument('-p', '--progress', required=False, type=str, default=None, help='Path to \'hidden\' file to save progress; default is input file with prefix .clanno_.')
    parser.add_argument('-t', '--tiers', required=False, nargs='*', type=str, default=['rating'], help='Names of the rating tiers to include (default: one scale called \'rating\').')
    parser.add_argument('--span_cols', required=False, type=str, default=None, help='Two column indices in the .csv input, separated by comma: a column containing spans (lists of dictionaries with "start" and "end" keys) and a column containing the text in which the spans live.')
    args = parser.parse_args()

    if args.file.name.endswith('.csv'):
        args.csv = True

    args.progress = args.progress or ('.clanno_stdin.csv' if args.file == sys.stdin else f'.clanno_{args.file.name}')
    if os.path.exists(args.progress) and not args.yes:
        input(f'Savefile {args.progress} already exists. Hit enter to continue.')

    items = list(csv.reader(args.file) if args.csv else args.file)

    if args.span_cols:
        import spanviz
        context_i, spans_i = (int(i) for i in args.span_cols.split(','))

        for item in items:
            item[context_i] = spanviz.spans_to_md(item[context_i], json.loads(item[spans_i]), with_labels=False)
            del item[spans_i]

    app = AnnotationApp(items, args.progress, rating_tiers=args.tiers)

    try:
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        app.save_progress()
        csv.writer(sys.stdout).writerows(app.annotations)   # TODO: With --tiers given, maybe output json?


if __name__ == "__main__":
    main()
