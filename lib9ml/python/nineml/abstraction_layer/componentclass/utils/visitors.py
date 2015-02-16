"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
from ...expressions.utils import get_reserved_and_builtin_symbols


class ComponentVisitor(object):

    def visit(self, obj, **kwargs):
        return obj.accept_visitor(self, **kwargs)


class ComponentActionVisitor(ComponentVisitor):

    def __init__(self, require_explicit_overrides=True):
        self.require_explicit_overrides = require_explicit_overrides

    def visit_componentclass(self, componentclass, **kwargs):
        self.action_componentclass(componentclass, **kwargs)
        nodes = chain(componentclass.parameters, componentclass.ports)
        for p in nodes:
            p.accept_visitor(self, **kwargs)

    def visit_parameter(self, parameter, **kwargs):
        self.action_parameter(parameter, **kwargs)

    def visit_alias(self, alias, **kwargs):
        self.action_alias(alias, **kwargs)

    def visit_randomvariable(self, randomvariable, **kwargs):
        self.action_randomvariable(randomvariable, **kwargs)

    def visit_constant(self, constant, **kwargs):
        self.action_constant(constant, **kwargs)

    def visit_piecewise(self, piecewise, **kwargs):
        self.action_piecewise(piecewise, **kwargs)

    def check_pass(self):
        if self.require_explicit_overrides:
            assert False, ("There is an overriding function missing from {}"
                           .format(self.__class__.__name__))
        else:
            pass

    # To be overridden:
    def action_componentclass(self, componentclass, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable @IgnorePep8
        self.check_pass()

    def action_constant(self, constant, **kwargs):  # @UnusedVariable
        self.check_pass()

    def action_piecewise(self, piecewise, **kwargs):  # @UnusedVariable
        self.check_pass()


class ComponentRequiredDefinitions(object):
    """
    Gets lists of required parameters, states, ports, random variables,
    constants and expressions (in resolved order of execution).
    """

    def __init__(self, componentclass, expressions):
        # Expression can either be a single expression or an iterable of
        # expressions
        self.parameters = set()
        self.ports = set()
        self.constants = set()
        self.random_variables = set()
        self.expressions = list()
        self._required_stack = []
        self._push_required_symbols(expressions)
        self._componentclass = componentclass
        self.visit(componentclass)

    def _push_required_symbols(self, expression):
        required_atoms = set()
        try:
            for expr in expression:
                required_atoms.update(expr.rhs_atoms)
        except TypeError:
            required_atoms.update(expression.rhs_atoms)
        # Strip builtin symbols from required atoms
        required_atoms.difference_update(get_reserved_and_builtin_symbols())
        self._required_stack.append(required_atoms)

    def _is_required(self, name):
        return name in self._required_stack[-1]

    def action_parameter(self, parameter, **kwargs):  # @UnusedVariable
        if self._is_required(parameter.name):
            self.parameters.add(parameter)

    def action_analogreceiveport(self, port, **kwargs):  # @UnusedVariable
        if self._is_required(port.name):
            self.ports.add(port)

    def action_analogreduceport(self, port, **kwargs):  # @UnusedVariable
        if self._is_required(port.name):
            self.ports.add(port)

    def action_constants(self, constant, **kwargs):  # @UnusedVariable
        if self._is_required(constant.name):
            self.constants.add(constant)

    def action_randomvariable(self, randomvariable, **kwargs):  # @UnusedVariable @IgnorePep8
        if self._is_required(randomvariable.name):
            self.random_variables.add(randomvariable)

    def action_alias(self, alias, **kwargs):  # @UnusedVariable
        if (self._is_required(alias.name) and
                alias.name not in self.expressions):
            # Since aliases may be dependent on other aliases/piecewises the
            # order they are executed is important so we make sure their
            # dependencies are added first
            self._push_required_symbols(alias)
            self.visit(self._componentclass)
            self._required_stack.pop()
            self.expressions.append(alias)

    def action_piecewise(self, piecewise, **kwargs):  # @UnusedVariable
        if (self._is_required(piecewise.name) and
                piecewise.name not in self.expressions):
            # Since piecewises may be dependent on other aliases/piecewises the
            # order they are executed is important so we make sure their
            # dependencies are added first
            self._push_required_symbols(piecewise)
            self.visit(self._componentclass)
            self._required_stack.pop()
            self.expressions.append(piecewise)

    @property
    def parameter_names(self):
        return (p.name for p in self.parameters)

    @property
    def port_names(self):
        return (p.name for p in self.ports)

    @property
    def constant_names(self):
        return (c.name for c in self.constants)

    @property
    def random_variable_names(self):
        return (r.name for r in self.random_variables)
