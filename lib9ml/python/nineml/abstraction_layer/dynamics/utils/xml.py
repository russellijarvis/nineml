"""
docstring needed

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""
from itertools import chain
from nineml.annotations import annotate_xml
from nineml.utils import expect_single
from nineml.xmlns import E
from ..base import DynamicsClass, Dynamics
from nineml.annotations import read_annotations
from ...ports import (EventSendPort, EventReceivePort, AnalogSendPort,
                      AnalogReceivePort, AnalogReducePort)
from ..transitions import OnEvent, OnCondition, StateAssignment, EventOut
from ..regimes import Regime, StateVariable, TimeDerivative
from ...componentclass.utils.xml import (
    ComponentClassXMLLoader, ComponentClassXMLWriter)


class DynamicsClassXMLLoader(ComponentClassXMLLoader):

    """This class is used by XMLReader interny.

    This class loads a NineML XML tree, and stores
    the components in ``components``. It o records which file each XML node
    was loaded in from, and stores this in ``component_srcs``.

    """

    @read_annotations
    def load_componentclass(self, element):

        blocks = ('Parameter', 'AnalogSendPort', 'AnalogReceivePort',
                  'EventSendPort', 'EventReceivePort', 'AnalogReducePort',
                  'Dynamics', 'Subnode', 'ConnectPorts', 'Component')

        subnodes = self._load_blocks(element, blocks=blocks)

        dynamics = expect_single(subnodes["Dynamics"])
        return DynamicsClass(
            name=element.get('name'),
            parameters=subnodes["Parameter"],
            analog_ports=chain(subnodes["AnalogSendPort"],
                               subnodes["AnalogReceivePort"],
                               subnodes["AnalogReducePort"]),
            event_ports=chain(subnodes["EventSendPort"],
                              subnodes["EventReceivePort"]),
            dynamics=dynamics,
            subnodes=dict(subnodes['Subnode']),
            portconnections=subnodes["ConnectPorts"])

    @read_annotations
    def load_eventsendport(self, element):
        return EventSendPort(name=element.get('name'))

    @read_annotations
    def load_eventreceiveport(self, element):
        return EventReceivePort(name=element.get('name'))

    @read_annotations
    def load_analogsendport(self, element):
        return AnalogSendPort(
            name=element.get("name"),
            dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_analogreceiveport(self, element):
        return AnalogReceivePort(
            name=element.get("name"),
            dimension=self.document[element.get('dimension')])

    @read_annotations
    def load_analogreduceport(self, element):
        return AnalogReducePort(
            name=element.get('name'),
            dimension=self.document[element.get('dimension')],
            reduce_op=element.get("operator"))

    @read_annotations
    def load_dynamics(self, element):

        subblocks = ('Regime', 'Alias', 'StateVariable', 'Constant',
                     'Piecewise')

        subnodes = self._load_blocks(element, blocks=subblocks)

        return Dynamics(regimes=subnodes["Regime"],
                        aliases=subnodes["Alias"],
                        state_variables=subnodes["StateVariable"],
                        constants=subnodes["Constant"],
                        piecewises=subnodes["Piecewise"])

    @read_annotations
    def load_regime(self, element):
        subblocks = ('TimeDerivative', 'OnCondition', 'OnEvent')
        subnodes = self._load_blocks(element, blocks=subblocks)
        transitions = subnodes["OnEvent"] + subnodes['OnCondition']
        return Regime(name=element.get('name'),
                      time_derivatives=subnodes["TimeDerivative"],
                      transitions=transitions)

    @read_annotations
    def load_statevariable(self, element):
        name = element.get("name")
        dimension = self.document[element.get('dimension')]
        return StateVariable(name=name, dimension=dimension)

    @read_annotations
    def load_timederivative(self, element):
        variable = element.get("variable")
        expr = self.load_single_internmaths_block(element)
        return TimeDerivative(dependent_variable=variable,
                              rhs=expr)

    @read_annotations
    def load_oncondition(self, element):
        subblocks = ('Trigger', 'StateAssignment', 'EventOut')
        subnodes = self._load_blocks(element, blocks=subblocks)
        target_regime = element.get('target_regime', None)
        trigger = expect_single(subnodes["Trigger"])

        return OnCondition(trigger=trigger,
                           state_assignments=subnodes["StateAssignment"],
                           event_outputs=subnodes["EventOut"],
                           target_regime_name=target_regime)

    @read_annotations
    def load_onevent(self, element):
        subblocks = ('StateAssignment', 'EventOut')
        subnodes = self._load_blocks(element, blocks=subblocks)
        target_regime_name = element.get('target_regime', None)

        return OnEvent(src_port_name=element.get('port'),
                       state_assignments=subnodes["StateAssignment"],
                       event_outputs=subnodes["EventOut"],
                       target_regime_name=target_regime_name)

    # FIXME: This should return a Trigger element not just an internal
    #        maths block (TGC 1/15)
    def load_trigger(self, element):
        return self.load_single_internmaths_block(element)

    @read_annotations
    def load_stateassignment(self, element):
        lhs = element.get('variable')
        rhs = self.load_single_internmaths_block(element)
        return StateAssignment(lhs=lhs, rhs=rhs)

    @read_annotations
    def load_eventout(self, element):
        port_name = element.get('port')
        return EventOut(port_name=port_name)

    tag_to_loader = {
        "ComponentClass": load_componentclass,
        "Regime": load_regime,
        "StateVariable": load_statevariable,
        "EventSendPort": load_eventsendport,
        "AnalogSendPort": load_analogsendport,
        "EventReceivePort": load_eventreceiveport,
        "AnalogReceivePort": load_analogreceiveport,
        "AnalogReducePort": load_analogreduceport,
        "Dynamics": load_dynamics,
        "OnCondition": load_oncondition,
        "OnEvent": load_onevent,
        "TimeDerivative": load_timederivative,
        "Trigger": load_trigger,
        "StateAssignment": load_stateassignment,
        "EventOut": load_eventout,
    }


class DynamicsClassXMLWriter(ComponentClassXMLWriter):

    @annotate_xml
    def visit_componentclass(self, componentclass):
        elements = ([p.accept_visitor(self)
                     for p in componentclass.analog_ports] +
                    [p.accept_visitor(self)
                     for p in componentclass.event_ports] +
                    [p.accept_visitor(self)
                     for p in componentclass.parameters] +
                    [componentclass.dynamics.accept_visitor(self)])
        return E('ComponentClass', *elements, name=componentclass.name)

    @annotate_xml
    def visit_dynamics(self, dynamics):
        elements = ([r.accept_visitor(self) for r in dynamics.regimes] +
                    [b.accept_visitor(self) for b in dynamics.aliases] +
                    [c.accept_visitor(self) for c in dynamics.constants] +
                    [c.accept_visitor(self) for c in dynamics.piecewises] +
                    [b.accept_visitor(self) for b in dynamics.state_variables])
        return E('Dynamics', *elements)

    @annotate_xml
    def visit_regime(self, regime):
        nodes = ([node.accept_visitor(self)
                  for node in regime.time_derivatives] +
                 [node.accept_visitor(self) for node in regime.on_events] +
                 [node.accept_visitor(self) for node in regime.on_conditions])
        return E('Regime', name=regime.name, *nodes)

    @annotate_xml
    def visit_statevariable(self, state_variable):
        return E('StateVariable',
                 name=state_variable.name,
                 dimension=state_variable.dimension.name)

    @annotate_xml
    def visit_eventout(self, event_out):
        return E('EventOut',
                 port=event_out.port_name)

    @annotate_xml
    def visit_analogreceiveport(self, port):
        return E('AnalogReceivePort', name=port.name,
                 dimension=port.dimension.name)

    @annotate_xml
    def visit_analogreduceport(self, port):
        return E('AnalogReducePort', name=port.name,
                 dimension=port.dimension.name, operator=port.reduce_op)

    @annotate_xml
    def visit_analogsendport(self, port):
        return E('AnalogSendPort', name=port.name,
                 dimension=port.dimension.name)

    @annotate_xml
    def visit_eventsendport(self, port):
        return E('EventSendPort', name=port.name)

    @annotate_xml
    def visit_eventreceiveport(self, port):
        return E('EventReceivePort', name=port.name)

    @annotate_xml
    def visit_assignment(self, assignment):
        return E('StateAssignment',
                 E("MathInline", assignment.rhs),
                 variable=assignment.lhs)

    @annotate_xml
    def visit_timederivative(self, time_derivative):
        return E('TimeDerivative',
                 E("MathInline", time_derivative.rhs),
                 variable=time_derivative.dependent_variable)

    @annotate_xml
    def visit_oncondition(self, on_condition):
        nodes = chain(on_condition.state_assignments,
                      on_condition.event_outputs, [on_condition.trigger])
        newNodes = [n.accept_visitor(self) for n in nodes]
        return E('OnCondition', *newNodes,
                 target_regime=on_condition._target_regime.name)

    @annotate_xml
    def visit_trigger(self, trigger):
        return E('Trigger', E("MathInline", trigger.rhs))

    @annotate_xml
    def visit_onevent(self, on_event):
        elements = ([p.accept_visitor(self)
                     for p in on_event.state_assignments] +
                    [p.accept_visitor(self) for p in on_event.event_outputs])
        return E('OnEvent', *elements, port=on_event.src_port_name,
                 target_regime=on_event.target_regime.name)
