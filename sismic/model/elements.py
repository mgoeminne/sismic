class ContractMixin:
    """
    Mixin with a contract: preconditions, postconditions and invariants.
    """

    def __init__(self):
        self.preconditions = []
        self.postconditions = []
        self.invariants = []


class StateMixin:
    """
    State element with a name.

    :param name: name of the state
    """

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

    def __eq__(self, other):
        return isinstance(other, StateMixin) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class ActionStateMixin:
    """
    State that can define actions on entry and on exit.

    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, on_entry: str = None, on_exit: str = None):
        self.on_entry = on_entry
        self.on_exit = on_exit


class TransitionStateMixin:
    """
    A simple state can host transitions
    """
    pass


class CompositeStateMixin:
    """
    Composite state can have children states.
    """
    pass


class HistoryStateMixin:
    """
    History state has a memory that can be resumed.

    :param memory: name of the initial state
    """

    def __init__(self, memory: str = None):
        self.memory = memory


class BasicState(ContractMixin, StateMixin, ActionStateMixin, TransitionStateMixin):
    """
    A basic state, with a name, transitions, actions, etc. but no child state.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, on_entry: str = None, on_exit: str = None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        TransitionStateMixin.__init__(self)


class CompoundState(ContractMixin, StateMixin, ActionStateMixin, TransitionStateMixin, CompositeStateMixin):
    """
    Compound states must have children states.

    :param name: name of this state
    :param initial: name of the initial state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, initial: str = None, on_entry: str = None, on_exit: str = None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        TransitionStateMixin.__init__(self)
        CompositeStateMixin.__init__(self)
        self.initial = initial


class OrthogonalState(ContractMixin, StateMixin, ActionStateMixin, TransitionStateMixin, CompositeStateMixin):
    """
    Orthogonal states run their children simultaneously.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, on_entry: str = None, on_exit: str = None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        TransitionStateMixin.__init__(self)
        CompositeStateMixin.__init__(self)


class ShallowHistoryState(ContractMixin, StateMixin, ActionStateMixin, HistoryStateMixin):
    """
    A shallow history state resumes the execution of its parent.
    It activates the latest visited state of its parent.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    :param memory: name of the initial state
    """
    def __init__(self, name: str, on_entry: str=None, on_exit: str=None, memory: str=None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        HistoryStateMixin.__init__(self, memory)


class DeepHistoryState(ContractMixin, StateMixin, ActionStateMixin, HistoryStateMixin):
    """
    A deep history state resumes the execution of its parent, and of every nested
    active states in its parent.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    :param memory: name of the initial state
    """
    def __init__(self, name: str, on_entry: str=None, on_exit: str=None, memory: str=None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)
        HistoryStateMixin.__init__(self, memory)


class FinalState(ContractMixin, StateMixin, ActionStateMixin):
    """
    Final state has NO transition and is used to detect state machine termination.

    :param name: name of this state
    :param on_entry: code to execute when state is entered
    :param on_exit: code to execute when state is exited
    """

    def __init__(self, name: str, on_entry: str = None, on_exit: str = None):
        ContractMixin.__init__(self)
        StateMixin.__init__(self, name)
        ActionStateMixin.__init__(self, on_entry, on_exit)


class Transition(ContractMixin):
    """
    Represent a transition from a source state to a target state.

    A transition can be eventless (no event) or internal (no target).
    A condition (code as string) can be specified as a guard.

    :param source: name of the source state
    :param target: name of the target state (if transition is not internal)
    :param event: event name (if any)
    :param guard: condition as code (if any)
    :param action: action as code (if any)
    """

    def __init__(self, source: str, target: str = None, event: str = None, guard: str = None, action: str = None):
        ContractMixin.__init__(self)
        self._source = source
        self._target = target
        self.event = event
        self.guard = guard
        self.action = action

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target

    @property
    def internal(self):
        """
        Boolean indicating whether this transition is an internal transition.
        """
        return self._target is None

    @property
    def eventless(self):
        """
        Boolean indicating whether this transition is an eventless transition.
        """
        return self.event is None

    def __eq__(self, other):
        return (isinstance(other, Transition) and
                self.source == other.source and
                self.target == other.target and
                self.event == other.event and
                self.guard == other.guard and
                self.action == other.action)

    def __repr__(self):
        return 'Transition({0}, {1}, {2})'.format(self.source, self.target, self.event)

    def __str__(self):
        return '{} [{}] -> {}'.format(self.source, self.event, self.target if self.target else '')

    def __hash__(self):
        return hash(self.source)
