import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from sismic.interpreter import Interpreter
from sismic.io import import_from_yaml
from sismic.model import Event
from sismic.testing import ConditionFailed

H_SPACE = 4
V_SPACE = 4

# TODO: Event parameter: event list that populates a field, + additional dict
# TODO: Load statechart frame
# TODO: TreeView for states
# TODO: TreeView (for the columns) for logs

class EventsFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)
        self._events = []

        self._event_variable = tk.StringVar()
        self._create_widgets()
        self.reset(interpreter)

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Events')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self._w_labelframe, text='select event name').pack(side=tk.TOP)
        self._w_eventlist = ttk.Combobox(self._w_labelframe, textvariable=self._event_variable)
        self._w_eventlist.pack(side=tk.TOP, fill=tk.X)

        self._w_btn_send = ttk.Button(self._w_labelframe, text='Queue event', width=14, command=self._cmd_btn_send)
        self._w_btn_send.pack(side=tk.BOTTOM)

        ttk.Frame(self._w_labelframe, height=V_SPACE).pack(side=tk.BOTTOM)

    def _cmd_btn_send(self):
        event_name = self._event_variable.get()
        self._interpreter.queue(Event(event_name))

    def reset(self, interpreter):
        self._events = []
        self._interpreter = interpreter
        self._w_eventlist.config(values=sorted(self._interpreter._statechart.events()) + ['<new>'])

    def update_content(self, steps=None):
        pass


class TimeFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)

        self._automatic = tk.BooleanVar(value=True)
        self._time = tk.DoubleVar()

        self._create_widgets()
        self.reset(interpreter)

    @property
    def automatic(self):
        return self._automatic.get()

    @property
    def time(self):
        return self._time.get()

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Time')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        time = tk.Entry(self._w_labelframe, textvariable=self._time, width=8, justify=tk.RIGHT)
        checkbox = tk.Checkbutton(self._w_labelframe, text='autoupdate', variable=self._automatic)

        time.pack(side=tk.TOP, anchor=tk.CENTER)
        checkbox.pack(side=tk.TOP, anchor=tk.CENTER)

    def reset(self, interpreter):
        self._time.set(interpreter.time)

    def update_content(self, steps):
        pass

    def elapse_time(self, delta):
        if self.automatic:
            self._time.set(round(self._time.get() + delta, 3))


class StatechartFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)

        self._create_widgets()
        self.reset(interpreter)

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Statechart')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        self._w_content = ttk.Label(self._w_labelframe, anchor=tk.NW, justify=tk.LEFT)
        self._w_content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def reset(self, interpreter):
        self._interpreter = interpreter

    def update_content(self, steps):
        states = self._interpreter._statechart.states
        active = self._interpreter.configuration
        content = []
        for state in states:
            if state in active:
                content.append('{} *'.format(state))
            else:
                content.append(state)
        self._w_content.config(text='\n'.join(sorted(content)))


class ContextFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)

        self._create_widgets()
        self.reset(interpreter)

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Context')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        self._w_context = ttk.Treeview(self._w_labelframe, columns=('value',), selectmode=tk.NONE)
        self._w_context.column('#0', width=35)
        self._w_context.heading('#0', text='variable')
        self._w_context.column('value', width=100)
        self._w_context.heading('value', text='value')

        self._w_context.pack(fill=tk.BOTH, expand=True)

    def reset(self, interpreter):
        self._interpreter = interpreter
        self._w_context.delete(*self._w_context.get_children())

    def update_content(self, steps):
        for variable, value in self._interpreter.context.items():
            try:
                self._w_context.set(variable, 'value', value)
            except tk.TclError:
                self._w_context.insert('', tk.END, iid=variable, text=variable, values=(value,))



class LogsFrame(ttk.Frame):
    def __init__(self, master, interpreter, **kwargs):
        super().__init__(master, **kwargs)

        self._autoscroll_variable = tk.BooleanVar(value=True)
        self._create_widgets()
        self.reset(interpreter)

    def _create_widgets(self):
        self._w_labelframe = ttk.LabelFrame(self, text='Logs')
        self._w_labelframe.pack(fill=tk.BOTH, expand=True)

        # Reset and autoscroll
        option_frame = ttk.Frame(self._w_labelframe)
        option_frame.pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Frame(option_frame, height=V_SPACE).pack(side=tk.TOP)

        self._w_clear_btn = ttk.Button(option_frame, text='Clear', command=self._cmd_btn_clear)
        self._w_clear_btn.pack(side=tk.RIGHT, anchor=tk.E)

        self._w_autoscroll = ttk.Checkbutton(option_frame, variable=self._autoscroll_variable, text='automatic scrolling')
        self._w_autoscroll.pack(side=tk.LEFT, anchor=tk.W)

        # Log panel
        self._w_content_frame = ttk.Frame(self._w_labelframe)
        self._w_content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._w_content = tk.Text(self._w_content_frame, height=6, wrap=tk.NONE)

        self._w_scrollbar_v = ttk.Scrollbar(self._w_content_frame, command=self._w_content.yview)
        self._w_scrollbar_h = ttk.Scrollbar(self._w_content_frame, orient=tk.HORIZONTAL, command=self._w_content.xview)
        self._w_content.config(xscrollcommand=self._w_scrollbar_h.set,
                               yscrollcommand=self._w_scrollbar_v.set)

        self._w_content_frame.grid_rowconfigure(0, weight=1)
        self._w_content_frame.grid_columnconfigure(0, weight=1)
        self._w_content.grid(row=0, column=0, sticky=tk.N + tk.E + tk.S + tk.W)
        self._w_scrollbar_v.grid(row=0, column=1, sticky=tk.N + tk.S)
        self._w_scrollbar_h.grid(row=1, column=0, sticky=tk.E + tk.W)

    def reset(self, interpreter):
        self._interpreter = interpreter
        self._cmd_btn_clear()

    def _cmd_btn_clear(self):
        self._w_content.delete('1.0', tk.END)

    def update_content(self, steps):
        for step in steps:
            self._w_content.insert(tk.END, str(step) + '\n')
        if self._autoscroll_variable.get():
            self._w_content.see(tk.END)


class ExecuteInterpreterFrame(ttk.Frame):
    def __init__(self, master, statechart, ignore_contract=False, initial_context=None):
        super().__init__(master)

        self._statechart = statechart
        self._ignore_contract =ignore_contract
        self._initial_context = initial_context

        self._interpreter = Interpreter(self._statechart,
                                        ignore_contract=self._ignore_contract,
                                        initial_context=self._initial_context)
        self._autorun = False
        self._autorun_delay = tk.IntVar(value=500)  # in ms

        self._create_widgets()
        self.update_content([])

    def _create_widgets(self):
        # Vertical pane
        vertical_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        vertical_pane.pack(fill=tk.BOTH, expand=True)

        main_frame = ttk.Frame(vertical_pane)
        self._w_logs_frame = LogsFrame(vertical_pane, self._interpreter)
        vertical_pane.add(main_frame, weight=1)
        vertical_pane.add(self._w_logs_frame)

        # Statechart & context
        horizontal_pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        horizontal_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._w_statechart_frame = StatechartFrame(horizontal_pane, self._interpreter)
        horizontal_pane.add(self._w_statechart_frame, weight=1)

        self._w_context_frame = ContextFrame(horizontal_pane, self._interpreter)
        horizontal_pane.add(self._w_context_frame, weight=1)

        # Events, time and execution
        self._w_events_frame = EventsFrame(main_frame, self._interpreter)
        self._w_time_frame = TimeFrame(main_frame, self._interpreter)
        execution_frame = ttk.LabelFrame(main_frame, text='Execution')

        ttk.Frame(main_frame, width=H_SPACE).pack(side=tk.RIGHT)
        self._w_events_frame.pack(side=tk.TOP, fill=tk.X)
        self._w_time_frame.pack(side=tk.TOP, fill=tk.X)
        execution_frame.pack(side=tk.TOP, fill=tk.X)

        label = ttk.Label(execution_frame, text='execution rate (in ms)')
        self._w_refresh_entry = ttk.Entry(execution_frame, width=5, justify=tk.RIGHT, textvariable=self._autorun_delay)
        self._w_execute_btn = ttk.Button(execution_frame, text='Execute step', width=14, command=self.execute)
        self._w_run_btn = ttk.Button(execution_frame, text='Run statechart', width=14, command=self._cmd_run_btn)
        self._w_reset_btn = ttk.Button(execution_frame, text='Reset statechart', width=14, command=self.reset)

        execution_frame.grid_columnconfigure(0, weight=1)
        label.grid(row=0)
        self._w_refresh_entry.grid(row=1)
        ttk.Frame(execution_frame, height=V_SPACE).grid(row=2)
        self._w_execute_btn.grid(row=3)
        self._w_run_btn.grid(row=4)
        self._w_reset_btn.grid(row=5)

    def execute(self):
        # Update time
        if self._w_time_frame.automatic:
            self._w_time_frame.elapse_time(self._autorun_delay.get() / 1000)

        self._interpreter.time = round(self._w_time_frame.time, 3)  # Interpreter's clock is in second
        try:
            steps = self._interpreter.execute()
            self.update_content(steps)
        except ConditionFailed as e:
            if self._autorun:
                self._w_run_btn.invoke()
            messagebox.showwarning('Contrat not satisfied', '{}\n\n{}'.format(str(e.__class__.__name__), str(e)))
            self.update_content([])
        except Exception as e:
            if self._autorun:
                self._w_run_btn.invoke()
            messagebox.showerror('An error has occured', '{}\n\n{}'.format(str(e.__class__.__name__), str(e)))
            self.update_content([])

        # Autorun?
        if self._autorun:
            self.after(self._autorun_delay.get(), self.execute)

    def update_content(self, steps):
        self._w_events_frame.update_content(steps)
        self._w_time_frame.update_content(steps)
        self._w_statechart_frame.update_content(steps)
        self._w_context_frame.update_content(steps)
        self._w_logs_frame.update_content(steps)

    def _cmd_run_btn(self):
        if self._autorun:
            self._autorun = False
            self._w_run_btn.config(text='Run')
            self._w_execute_btn.config(state=tk.NORMAL)
        else:
            self._autorun = True
            self._w_run_btn.config(text='Stop')
            self._w_execute_btn.config(state=tk.DISABLED)
            self.execute()

    def reset(self):
        # confirm?
        if messagebox.askyesno('Confirmation', 'Reset current simulation?'):
            self._interpreter = Interpreter(self._statechart,
                                            ignore_contract=self._ignore_contract,
                                            initial_context=self._initial_context)
            if self._autorun:
                self._w_run_btn.invoke()
            self._w_events_frame.reset(self._interpreter)
            self._w_time_frame.reset(self._interpreter)
            self._w_statechart_frame.reset(self._interpreter)
            self._w_context_frame.reset(self._interpreter)
            self._w_logs_frame.reset(self._interpreter)

            self.update_content([])


def main():
    with open('docs/examples/stopwatch.yaml') as f:
        statechart = import_from_yaml(f)

    root = tk.Tk()
    root.wm_title('Sismic-ui')
    root.wm_minsize(800, 600)

    style = ttk.Style()
    style.configure('TLabelframe', padding=H_SPACE)

    app = ExecuteInterpreterFrame(root, statechart=statechart, ignore_contract=False, initial_context={})
    app.pack(fill=tk.BOTH, expand=True, padx=H_SPACE, pady=V_SPACE)

    root.mainloop()

if __name__ == '__main__':
    main()