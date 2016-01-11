import tkinter as tk

from . import io, model, interpreter


class EventsFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()


class SimulationFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()


class StatechartFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()


class LogsFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack()


class App(tk.Frame):
    def __init__(self, master, statechart, ignore_contract=False, initial_context=None):
        super().__init__(master)

        self._statechart = statechart
        self._ignore_contract =ignore_contract
        self._initial_context = initial_context

        self._interpreter = interpreter.Interpreter(statechart,
                                                    ignore_contract=self._ignore_contract,
                                                    initial_context=initial_context)
        self.pack(fill=tk.BOTH, expand=True)
        self._create_widgets()

    def _create_widgets(self):
        # Create label frames and frames
        events_labelframe = tk.LabelFrame(self, text='Events')
        self.w_events_frame = EventsFrame(events_labelframe)

        simulation_labelframe = tk.LabelFrame(self, text='Actions')
        self.w_simulationa_frame = SimulationFrame(simulation_labelframe)

        statechart_labelframe = tk.LabelFrame(self, text='Statechart')
        self.w_statechart_frame = StatechartFrame(statechart_labelframe)

        logs_labelframe = tk.LabelFrame(self, text='Logs')
        self.w_logs_frame = LogsFrame(logs_labelframe)

        # Label frame positions
        logs_labelframe.pack(side=tk.BOTTOM, fill=tk.X)
        events_labelframe.pack(side=tk.LEFT, fill=tk.Y)
        simulation_labelframe.pack(side=tk.TOP, fill=tk.X)
        statechart_labelframe.pack(side=tk.TOP, fill=tk.BOTH, expand=True)




def main():
    with open('docs/examples/elevator.yaml') as f:
        statechart = io.import_from_yaml(f)

    root = tk.Tk()
    root.wm_title('Sismic-ui')

    app = App(root, statechart=statechart, ignore_contract=False, initial_context={})

    root.mainloop()

if __name__ == '__main__':
    main()