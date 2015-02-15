# ======================================================================
# >> IMPORTS
# ======================================================================

# Python
from random import randint
from functools import wraps, WRAPPER_ASSIGNMENTS

# Source.Python
from listeners.tick.repeat import TickRepeat


# ======================================================================
# >> CLASSES
# ======================================================================

class classproperty(object):
    """Decorator to create a property for a class.

    http://stackoverflow.com/a/3203659/2505645
    """

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


class _Cooldown(object):
    def __init__(self, max_cooldown):
        self.max_cooldown = max_cooldown
        self.remaining_cooldown = 0

        self.tick_repeat = TickRepeat(self.reduce_cooldown)
        self.tick_repeat.start(1, self.max_cooldown)

    def reduce_cooldown(self):
        if self.remaining_cooldown <= 0:
            self.tick_repeat.stop()
        else:
            self.remaining_cooldown -= 1



# ======================================================================
# >> FUNCTIONS
# ======================================================================

def find_element(iterable, attr_name, attr_value):
    """Finds an element with matching attribute."""

    for element in iterable:
        if getattr(element, attr_name) == attr_value:
            return element

def find_elements(iterable, attr_name, attr_value):
    """Finds elements with matching attributes."""
    elements = []
    for element in iterable:
        if getattr(element, attr_name) == attr_value:
            elements.append(element)
    return elements

def get_subclasses(cls):
    """Gets a set of class' subclasses."""

    subclasses = set()
    for subcls in cls.__subclasses__():
        subclasses.add(subcls)
        subclasses.update(get_subclasses(subcls))
    return subclasses


def shiftattr(obj, attr_name, shift):
    """Shifts an attribute's value.

    Similar to getattr() and setattr(), shiftattr() shifts
    (increments or decrements) attributes value by the given shift.

    Args:
        obj: Object whose attribute to shift
        attr_name: Name of the attribute to shift
        shift: Shift to make, can be negative
    """

    setattr(obj, attr_name, getattr(obj, attr_name) + shift)


def chance(percentage):
    """Decorates a function to be executed at a static chance.

    Takes a percentage as a parameter, returns an other decorator
    that wraps the original function so that it only gets executed
    at a chance of the given percentage.

    Args:
        percentage: Chance of execution in percentage (0-100)

    Returns:
        New function that doesn't always get executed when called
    """

    def method_decorator(method):
        @wraps(method, assigned=WRAPPER_ASSIGNMENTS+('__dict__',), updated=())
        def method_wrapper(self, game_event):
            if randint(0, 100) <= percentage:
                return method(self, game_event)
            return 1  # Failed to execute
        return method_wrapper
    return method_decorator


def chancef(fn):
    """Decorates a function to be executed at a dynamic chance.

    Takes a percentage as a parameter, returns an other decorator
    that wraps the original function so that it only gets executed
    at a chance of the percentage calculated by given function.

    Args:
        fn: Function to determine the chance of the method's execution

    Returns:
        New function that doesn't always get executed when called
    """

    def method_decorator(method):
        @wraps(method, assigned=WRAPPER_ASSIGNMENTS+('__dict__',), updated=())
        def method_wrapper(self, game_event):
            if randint(0, 100) <= fn(self, game_event):
                return method(self, game_event)
            return 2  # Failed to execute
        return method_wrapper
    return method_decorator


def _empty(*args, **kwargs):
    """Empty function, does nothing."""

    pass


def cooldown(time):
    """Decorates a function to have a static cooldown.

    Decorator function for easily adding cooldown as
    a static time (integer) into skill's methods.

    Args:
        time: Cooldown of the method

    Returns:
        Decorated method with a static cooldown
    """

    def method_decorator(method):
        @wraps(method, assigned=WRAPPER_ASSIGNMENTS+('__dict__',), updated=())
        def method_wrapper(self, game_event):
            if method_wrapper.cooldown.remaining <= 0:
                method_wrapper.cooldown.start(1, time)
                return method(self, game_event)
            return 3 # Failed to execute
        method_wrapper.cooldown = TickRepeat(_empty)
        return method_wrapper
    return method_decorator


def cooldownf(fn):
    """Decorates a method to have a dynamic cooldown.

    Decorator function for easily adding cooldown as a dynamic time
    (function) into skill's methods. The function gets called when the
    cooldown is needed, and the skill is passed to the function.

    Args:   
        fn: Function to determine the cooldown of the method
    
    Returns:
        Decorated method with a dynamic cooldown
    """

    def method_decorator(method):
        @wraps(method, assigned=WRAPPER_ASSIGNMENTS+('__dict__',), updated=())
        def method_wrapper(self, game_event):
            if method_wrapper.cooldown.remaining <= 0:
                method_wrapper.cooldown.start(1, fn(self, game_event))
                return method(self, game_event)
            return 4  # Failed to execute
        method_wrapper.cooldown = TickRepeat(_empty)
        return method_wrapper
    return method_decorator
