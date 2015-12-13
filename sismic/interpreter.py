from collections import deque
from . import model
from .evaluator import Evaluator, PythonEvaluator


class MicroStep:
    """
    Create a micro step. A step consider ``event``, takes ``transition`` and results in a list
    of ``entered_states`` and a list of ``exited_states``.
    Order in the two lists is REALLY important!

    :param event: Event or None in case of eventless transition
    :param transition: a ''Transition`` or None if no processed transition
    :param entered_states: possibly empty list of entered states
    :param exited_states: possibly empty list of exited states
    """
    def __init__(self, event: model.Event=None, transition: model.Transition=None,
                 entered_states: list=None, exited_states: list=None):
        self.event = event
        self.transition = transition if transition else []
        self.entered_states = entered_states if entered_states else []
        self.exited_states = exited_states if exited_states else []

    def __repr__(self):
        return 'MicroStep({}, {}, {}, {})'.format(self.event, self.transition, self.entered_states, self.exited_states)


class MacroStep:
    """
    A macro step is a list of micro steps instances, corresponding to the process of at most one transition and
    the conseuctive stabilization micro steps.

    :param steps: a list of ``MicroStep`` instances
    """
    def __init__(self, steps: list):
        self.steps = steps

    @property
    def event(self) -> model.Event:
        """
        Event (or ``None``) that were consumed.
        """
        try:
            self.steps[0].event
        except IndexError:
            return None

    @property
    def transitions(self) -> list:
        """
        A (possibly empty) list of transitions that were triggered.
        """
        return [step.transition for step in self.steps if step.transition]

    @property
    def entered_states(self) -> list:
        """
        List of the states names that were entered.
        """
        states = []
        for step in self.steps:
            states += step.entered_states
        return states

    @property
    def exited_states(self) -> list:
        """
        List of the states names that were exited.
        """
        states = []
        for step in self.steps:
            states += step.exited_states
        return states

    def __repr__(self):
        return 'MacroStep({}, {}, {}, {})'.format(self.event, self.transitions, self.entered_states, self.exited_states)


class Interpreter:
    """
    A discrete interpreter that executes a statechart according to a semantic close to SCXML.

    :param statechart: statechart to interpret
    :param evaluator_klass: An optional callable (eg. a class) that takes no input and return a
        ``evaluator.Evaluator`` instance that will be used to initialize the interpreter.
        By default, an ``evaluator.PythonEvaluator`` will be used.
    """
    def __init__(self, statechart: model.StateChart, evaluator_klass=None):
        self._evaluator_klass = evaluator_klass
        self._evaluator = evaluator_klass() if evaluator_klass else PythonEvaluator()
        self._statechart = statechart
        self._memory = {}  # History states memory
        self._configuration = set()  # Set of active states
        self._events = deque()  # Events queue
        self._start()

    @property
    def configuration(self) -> list:
        """
        List of active states names, ordered by depth.
        """
        return sorted(self._configuration, key=lambda s: self._statechart.depth_of(s))

    @property
    def evaluator(self) -> Evaluator:
        """
        The ``Evaluator`` associated with this simulator.
        """
        return self._evaluator

    def send(self, event: model.Event, internal: bool=False):
        """
        Send an event to the interpreter, and add it into the event queue.

        :param event: an ``Event`` instance
        :param internal: set to True if the provided ``Event`` should be considered as
            an internal event (and thus, as to be prepended to the events queue).
        :return: ``self``
        """
        if internal:
            self._events.appendleft(event)
        else:
            self._events.append(event)
        return self

    def _start(self) -> list:
        """
        Make this statechart runnable:

         - Execute statechart initial code
         - Execute until a stable situation is reached.

        :return: A (possibly empty) list of executed MicroStep.
        """
        if self._statechart.on_entry:
            self._evaluator.execute_action(self._statechart.on_entry)

        # Initial step and stabilization
        step = MicroStep(entered_states=[self._statechart.initial])
        self._execute_step(step)

        return [step] + self._stabilize()

    @property
    def running(self) -> bool:
        """
        Boolean indicating whether this interpreter is not in a final configuration.
        """
        for state in self._statechart.leaf_for(list(self._configuration)):
            if not isinstance(self._statechart._states[state], model.FinalState):
                return True
        return False

    def reset(self):
        """
        Reset current interpreter to its initial state.
        This also resets history states memory.
        """
        self.__init__(self._statechart, self._evaluator_klass)

    def execute(self, max_steps: int=-1) -> list:
        """
        Repeatedly calls ``execute_once()`` and return a list containing
        the returned values of ``execute_once()``.

        Notice that this does NOT return an iterator but computes the whole list first
        before returning it.

        :param max_steps: An upper bound on the number steps that are computed and returned.
            Default is -1, no limit. Set to a positive integer to avoid infinite loops
            in the statechart execution.
        :return: A list of ``MacroStep`` instances
        """
        returned_steps = []
        i = 0
        macro_step = self.execute_once()
        while macro_step:
            returned_steps.append(macro_step)
            i += 1
            if max_steps > 0 and i == max_steps:
                break
            macro_step = self.execute_once()
        return returned_steps

    def execute_once(self) -> MacroStep:
        """
        Processes a transition based on the oldest queued event (or no event if an eventless transition
        can be processed), and stabilizes the interpreter in a stable situation (ie. processes initial states,
        history states, etc.).

        :return: a macro step or ``None`` if nothing happened
        """
        # Try eventless transitions
        main_steps = self._transition_step(event=None)  # Explicit is better than implicit

        # If there is no eventless transition, and there exists at least one event to process
        if len(main_steps) == 0 and len(self._events) > 0:
            event = self._events.popleft()
            main_steps = self._transition_step(event=event)

            # If this event can not be processed, discard it
            if len(main_steps) == 0:
                main_steps = [MicroStep(event=event)]

        if len(main_steps) > 0:
            returned_steps = []
            for step in main_steps:
                self._execute_step(step)
                returned_steps.append(step)

            return MacroStep(returned_steps + self._stabilize())
        else:
            return None

    def _actionable_transitions(self, event: model.Event=None) -> list:
        """
        Return a list of transitions that can be actioned wrt.
        the current configuration. The list is ordered in increasing state depth.

        :param event: Event to considered or None for eventless transitions
        :return: A (possibly empty) ordered list of ``Transition`` instances
        """
        transitions = []
        for transition in self._statechart.transitions:
            if transition.event != event:
                continue
            if transition.from_state not in self._configuration:
                continue
            if transition.guard is None or self._evaluator.evaluate_condition(transition.guard, event):
                transitions.append(transition)

        # Order by deepest first
        return sorted(transitions, key=lambda t: self._statechart.depth_of(t.from_state))

    def _stabilize_step(self) -> MicroStep:
        """
        Return a stabilization step, ie. a step that lead to a more stable situation
        for the current statechart (expand to initial state, expand to history state, etc.).

        :return: A ``MicroStep`` instance or ``None`` if this statechart can not be more stabilized
        """
        # Check if we are in a set of "stable" states
        leaves = self._statechart.leaf_for(list(self._configuration))
        for leaf in leaves:
            leaf = self._statechart.states[leaf]
            if isinstance(leaf, model.HistoryState):
                states_to_enter = self._memory.get(leaf.name, [leaf.initial])
                states_to_enter.sort(key=lambda x: self._statechart.depth_of(x))
                return MicroStep(entered_states=states_to_enter, exited_states=[leaf.name])
            elif isinstance(leaf, model.OrthogonalState):
                return MicroStep(entered_states=leaf.children)
            elif isinstance(leaf, model.CompoundState) and leaf.initial:
                return MicroStep(entered_states=[leaf.initial])

    def _stabilize(self) -> list:
        """
        Compute, apply and return stabilization steps.

        :return: A list of ``MicroStep`` instances
        """
        # Stabilization
        steps = []
        step = self._stabilize_step()
        while step:
            steps.append(step)
            self._execute_step(step)
            step = self._stabilize_step()
        return steps

    def _transition_step(self, event: model.Event=None) -> list:
        """
        Return a possibly empty list of ``MicroStep`` instances
        associated with the appropriate transition matching
        given event (or eventless transition if event is None).

        :param event: ``Event`` to consider (or None)
        :return: A list of ``MicroStep`` instances
        :raise: a Warning in case of non determinism
        """

        # Inner-first/source-state semantic
        transitions = self._actionable_transitions(event)
        transitions.reverse()  # In-place reverse

        if len(transitions) == 0:
            return []

        transition = transitions[0]

        transition_depth = self._statechart.depth_of(transition.from_state)
        for other_transition in transitions:
            if not(other_transition is transition) and self._statechart.depth_of(other_transition.from_state) == transition_depth:
                raise Warning('More than one transition can be processed: non-determinism!' +
                              '\nConfiguration is {}\nEvent is {}\nTransitions are:{}\n'
                              .format(self.configuration, event, transitions))

        # Internal transition
        if transition.to_state is None:
            return [MicroStep(event, transition, [], [])]

        lca = self._statechart.least_common_ancestor(transition.from_state, transition.to_state)
        from_ancestors = self._statechart.ancestors_for(transition.from_state)
        to_ancestors = self._statechart.ancestors_for(transition.to_state)

        # Exited states
        exited_states = []

        # last_before_lca is the "highest" ancestor or from_state that is a child of LCA
        last_before_lca = transition.from_state
        for state in from_ancestors:
            if state == lca:
                break
            last_before_lca = state

        # Take all the descendants of this state and list the ones that are active
        for descendant in self._statechart.descendants_for(last_before_lca)[::-1]:  # Mind the reversed order!
            # Only leave states that are currently active
            if descendant in self._configuration:
                exited_states.append(descendant)

        # Add last_before_lca as it is a child of LCA that must be exited
        if last_before_lca in self._configuration:
            exited_states.append(last_before_lca)

        # Entered states
        entered_states = [transition.to_state]
        for state in to_ancestors:
            if state == lca:
                break
            entered_states.insert(0, state)

        return [MicroStep(event, transition, entered_states, exited_states)]

    def _execute_step(self, step: MicroStep):
        """
        Apply given ``MicroStep`` on this statechart

        :param step: ``MicroStep`` instance
        """
        entered_states = list(map(lambda s: self._statechart.states[s], step.entered_states))
        exited_states = list(map(lambda s: self._statechart.states[s], step.exited_states))

        for state in exited_states:
            # Execute exit action
            if isinstance(state, model.ActionStateMixin) and state.on_exit:
                for event in self._evaluator.execute_action(state.on_exit):
                    # Internal event
                    self.send(event, internal=True)

        # Deal with history: this only concerns compound states
        exited_compound_states = list(filter(lambda s: isinstance(s, model.CompoundState), exited_states))
        for state in exited_compound_states:
            # Look for an HistoryState among its children
            for child_name in state.children:
                child = self._statechart.states[child_name]
                if isinstance(child, model.HistoryState):
                    if child.deep:
                        # This MUST contain at least one element!
                        active = self._configuration.intersection(self._statechart.descendants_for(state.name))
                        assert len(active) >= 1
                        self._memory[child.name] = list(active)
                    else:
                        # This MUST contain exactly one element!
                        active = self._configuration.intersection(state.children)
                        assert len(active) == 1
                        self._memory[child.name] = list(active)

        # Remove states from configuration
        self._configuration = self._configuration.difference(step.exited_states)

        # Execute transition
        if step.transition and step.transition.action:
            self._evaluator.execute_action(step.transition.action, step.event)

        for state in entered_states:
            # Execute entry action
            if isinstance(state, model.ActionStateMixin) and state.on_entry:
                for event in self._evaluator.execute_action(state.on_entry):
                    # Internal event
                    self.send(event, internal=True)

        # Add state to configuration
        self._configuration = self._configuration.union(step.entered_states)

    def __repr__(self):
        return '{}[{}]'.format(self.__class__.__name__, ', '.join(self.configuration))
