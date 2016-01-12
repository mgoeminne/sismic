import tkinter as tk

from . import io, model, interpreter

FRAME_OPTIONS = {'padx': 6, 'pady': 6}
LABELFRAME_OPTIONS = {}
BUTTON_OPTIONS = {'padx': 3, 'pady': 3}
LABEL_OPTIONS = {}
TEXT_OPTIONS = {}
SCROLLBAR_OPTIONS = {}


class EventsFrame(tk.Frame):
    def __init__(self, master, interpreter):
        super().__init__(master)
        self._interpreter = interpreter
        self._events = []

        self._create_widgets()

    def _create_widgets(self):
        self._w_labelframe = tk.LabelFrame(self, text='Events', **LABELFRAME_OPTIONS)
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        self._w_btn_send = tk.Button(self._w_labelframe, text='Send', command=self._cmd_btn_send)
        self._w_btn_send.pack(side=tk.BOTTOM, fill=tk.X)

    def _cmd_btn_send(self):
        self._events.append('start')

    def get_events(self):
        """
        List of events to send
        """
        events = self._events[:]
        self._events = []
        return events

    def update_content(self, steps):
        pass

    def set_interpreter(self, interpreter):
        self._interpreter = interpreter


class TimeFrame(tk.Frame):
    def __init__(self, master, interpreter):
        super().__init__(master)
        self._interpreter = interpreter
        self.automatic = True
        self.time = 0
        self._create_widgets()

    def _create_widgets(self):
        self._w_labelframe = tk.LabelFrame(self, text='Time', **LABELFRAME_OPTIONS)
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

    def update_content(self, steps):
        pass

    def elapse_time(self, delta):
        if self.automatic:
            self.time += delta

    def set_interpreter(self, interpreter):
        self._interpreter = interpreter


class StatechartFrame(tk.Frame):
    def __init__(self, master, interpreter):
        super().__init__(master)
        self._interpreter = interpreter

        self._create_widgets()

    def _create_widgets(self):
        self._w_labelframe = tk.LabelFrame(self, text='Statechart', **LABELFRAME_OPTIONS)
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        self._w_content = tk.Label(self._w_labelframe, anchor=tk.NW, justify=tk.LEFT, **LABEL_OPTIONS)
        self._w_content.pack(fill=tk.BOTH, expand=True)

    def update_content(self, steps):
        content = '\n'.join(self._interpreter.configuration)
        self._w_content.config(text=content)

    def set_interpreter(self, interpreter):
        self._interpreter = interpreter


class ContextFrame(tk.Frame):
    def __init__(self, master, interpreter):
        super().__init__(master)
        self._interpreter = interpreter

        self._create_widgets()

    def _create_widgets(self):
        self._w_labelframe = tk.LabelFrame(self, text='Context', **LABELFRAME_OPTIONS)
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        self._w_content = tk.Label(self._w_labelframe, anchor=tk.NW, justify=tk.LEFT, **LABEL_OPTIONS)
        self._w_content.pack(fill=tk.BOTH, expand=True)

    def update_content(self, steps):
        content = '\n'.join(['{}: {}'.format(k,v) for k,v in self._interpreter.context.items()])
        self._w_content.config(text=content)

    def set_interpreter(self, interpreter):
        self._interpreter = interpreter


class LogsFrame(tk.Frame):
    def __init__(self, master, interpreter):
        super().__init__(master)
        self._interpreter = interpreter

        self._create_widgets()

    def _create_widgets(self):
        self._w_labelframe = tk.LabelFrame(self, text='Logs', **LABELFRAME_OPTIONS)
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        self._w_content_frame = tk.Frame(self._w_labelframe, **FRAME_OPTIONS)
        self._w_content_frame.pack(fill=tk.BOTH)

        self._w_content = tk.Text(self._w_content_frame, height=12, **TEXT_OPTIONS)

        self._w_scrollbar_v = tk.Scrollbar(self._w_content_frame, command=self._w_content.yview, **SCROLLBAR_OPTIONS)
        self._w_scrollbar_h = tk.Scrollbar(self._w_content_frame, orient=tk.HORIZONTAL, command=self._w_content.xview, **SCROLLBAR_OPTIONS)
        self._w_content.config(xscrollcommand=self._w_scrollbar_h.set,
                               yscrollcommand=self._w_scrollbar_v.set)

        self._w_content_frame.grid_rowconfigure(0, weight=1)
        self._w_content_frame.grid_columnconfigure(0, weight=1)
        self._w_content.grid(row=0, column=0, sticky=tk.N + tk.E + tk.S + tk.W)
        self._w_scrollbar_v.grid(row=0, column=1, sticky=tk.N + tk.S)
        self._w_scrollbar_h.grid(row=1, column=0, sticky=tk.E + tk.W)

    def update_content(self, steps):
        for step in steps:
            self._w_content.insert(tk.END, str(step) + '\n')
        self._w_content.see(tk.END)

    def set_interpreter(self, interpreter):
        self._interpreter = interpreter


class App(tk.Frame):
    def __init__(self, master, statechart, ignore_contract=False, initial_context=None):
        super().__init__(master)

        self._statechart = statechart
        self._ignore_contract =ignore_contract
        self._initial_context = initial_context

        self._interpreter = interpreter.Interpreter(self._statechart,
                                                    ignore_contract=self._ignore_contract,
                                                    initial_context=self._initial_context)
        self._autorun = False

        self._create_widgets()
        self.update_content([])

    def _create_widgets(self):
        # Create frames and widgets
        left_frame = tk.Frame(self)
        right_frame = tk.Frame(self)

        self._w_events_frame = EventsFrame(left_frame, self._interpreter)
        self._w_time_frame = TimeFrame(left_frame, self._interpreter)
        self._w_statechart_frame = StatechartFrame(right_frame, self._interpreter)
        self._w_context_frame = ContextFrame(right_frame, self._interpreter)
        self._w_logs_frame = LogsFrame(right_frame, self._interpreter)

        actions_frame = tk.LabelFrame(left_frame, text='Execution')
        self._w_execute_btn = tk.Button(actions_frame, text='Execute', command=self.execute)
        self._w_run_btn = tk.Button(actions_frame, text='Run', command=self._cmd_run_btn)
        self._w_reset_btn = tk.Button(actions_frame, text='Reset', command=self.reset)

        # Positions
        actions_frame.pack(side=tk.BOTTOM, fill=tk.X, **FRAME_OPTIONS)
        self._w_execute_btn.pack(side=tk.LEFT, **BUTTON_OPTIONS)
        self._w_run_btn.pack(side=tk.LEFT, **BUTTON_OPTIONS)
        self._w_reset_btn.pack(side=tk.LEFT, **BUTTON_OPTIONS)

        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self._w_time_frame.pack(side=tk.BOTTOM, fill=tk.X, **FRAME_OPTIONS)
        self._w_events_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, **FRAME_OPTIONS)

        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._w_logs_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, **FRAME_OPTIONS)
        self._w_statechart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, **FRAME_OPTIONS)
        self._w_context_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, **FRAME_OPTIONS)

    def execute(self):
        # Grep events
        events = self._w_events_frame.get_events()
        for event in events:
            self._interpreter.send(event)

        steps = self._interpreter.execute()
        self.update_content(steps)

    def update_content(self, steps):
        self._w_events_frame.update_content(steps)
        self._w_time_frame.update_content(steps)
        self._w_statechart_frame.update_content(steps)
        self._w_context_frame.update_content(steps)
        self._w_logs_frame.update_content(steps)

    def _cmd_run_btn(self):
        pass

    def reset(self):
        self._interpreter = interpreter.Interpreter(self._statechart,
                                                    ignore_contract=self._ignore_contract,
                                                    initial_context=self._initial_context)
        self._autorun = False
        self._w_time_frame.time = 0
        self.update_content([])


def main():
    with open('docs/examples/stopwatch.yaml') as f:
        statechart = io.import_from_yaml(f)

    root = tk.Tk()
    root.wm_title('Sismic-ui')
    root.wm_minsize(800, 480)
    app = App(root, statechart=statechart, ignore_contract=False, initial_context={})
    app.pack(fill=tk.BOTH, expand=True)

    root.mainloop()

if __name__ == '__main__':
    main()