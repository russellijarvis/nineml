"""
This file contains utility classes for modifying components.

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from nineml.abstraction_layer.components import Parameter
from nineml.abstraction_layer.dynamics.visitors import ExpandPortDefinition
from nineml.abstraction_layer.dynamics.component.ports import AnalogSendPort, AnalogReducePort, AnalogReceivePort
from nineml.utility import filter_expect_single
from nineml.exceptions import NineMLRuntimeError
from ..base import BaseALObject


class ComponentModifier(BaseALObject):

    """Utility classes for modifying components"""

    @classmethod
    def close_analog_port(cls, component, port_name, value="0"):
        """Closes an incoming analog port by assigning its value to 0"""

        if not component.is_flat():
            raise NineMLRuntimeError('close_analog_port() on non-flat '
                                     'component')

        # Subsitute the value in:
        component.accept_visitor(ExpandPortDefinition(port_name, value))

        # Remove it from the list of ports:
        port = filter_expect_single(component.analog_ports,
                                    lambda ap: ap.name == port_name)
        if isinstance(port, AnalogSendPort):
            component._analog_send_ports.pop(port_name)
        elif isinstance(port, AnalogReceivePort):
            component._analog_receive_ports.pop(port_name)
        elif isinstance(port, AnalogReducePort):
            component._analog_reduce_ports.pop(port_name)
        else:
            raise TypeError("Expected an analog port")

    @classmethod
    def close_all_reduce_ports(cls, component, exclude=None):
        """Closes all the ``reduce`` ports on a component by assigning them a
        value of 0"""
        if not component.is_flat():
            raise NineMLRuntimeError('close_all_reduce_ports() on non-flat '
                                     'component')

        for arp in component.query.analog_reduce_ports:
            if exclude and arp.name in exclude:
                continue
            ComponentModifier.close_analog_port(component=component,
                                                port_name=arp.name,
                                                value='0')

    @classmethod
    def rename_port(cls, component, old_port_name, new_port_name):
        """ Renames a port in a component """
        if not component.is_flat():
            raise NineMLRuntimeError('rename_port() on non-flat component')

        # Find the old port:
        port = filter_expect_single(component.analog_ports,
                                    lambda ap: ap.name == old_port_name)
        port._name = new_port_name

    @classmethod
    def remap_port_to_parameter(cls, component, port_name):
        """ Renames a port in a component """
        if not component.is_flat():
            raise NineMLRuntimeError('rename_port_to_parameter() on non-flat '
                                     'component')

        # Find the old port:
        port = filter_expect_single(component.analog_ports,
                                    lambda ap: ap.name == port_name)
        component._analog_ports.remove(port)

        # Add a new parameter:
        component._parameters[port_name] = Parameter(port_name)
