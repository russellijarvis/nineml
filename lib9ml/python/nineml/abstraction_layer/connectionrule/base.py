#!/usr/bin/env python
"""
docstring goes here

.. module:: connection_generator.py
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Mikael Djurfeldt <mikael.djurfeldt@incf.org>
.. moduleauthor:: Dragan Nikolic <dnikolic@incf.org>

:copyright: Copyright 2010-2013 by the Python lib9ML team, see AUTHORS.
:license: BSD-3, see LICENSE for details.
"""

from abc import ABCMeta, abstractmethod, abstractproperty
from nineml.abstraction_layer.components import BaseComponentClass
from ..base import BaseALObject


class ComponentClass(BaseComponentClass):

    defining_attributes = ('name', '_parameters', '_connection_rule')

    def __init__(self, name, parameters=None, connection_rule=None):
        super(ComponentClass, self).__init__(name, parameters)
        self._connection_rule = connection_rule


class IntervalSet(BaseALObject):

    defining_attributes = ('intervals', 'skip')

    def __init__(self, intervals=[], skip=1):
        """
        intervals is a list of 2-tuples (FROM, TO) representing all
        integers i, FROM <= i <= TO
        """
        self.intervals = intervals
        self._skip = skip

    @property
    def skip(self):
        return self._skip

    def __iter__(self):
        return self.intervals.__iter__()


class Mask(BaseALObject):

    defining_attributes = ('sources', 'targets')

    def __init__(self,
                 sources=[], targets=[],
                 sourceSkip=1, targetSkip=1):
        """
        sources and targets are lists of 2-tuples (FROM, TO)
        representing all integers i, FROM <= i <= TO
        """
        self.sources = IntervalSet(sources, sourceSkip)
        self.targets = IntervalSet(targets, targetSkip)


class StandardLibraryConnectionRule(BaseALObject):

    defining_attributes = ('reference_url',)

    def __init__(self, reference_url):
        self.reference_url = reference_url


class ConnectionGenerator(BaseALObject):

    """
    The ConnectionGenerator interface.
    """

    __metaclass__ = ABCMeta

    @abstractproperty
    def arity(self):
        """
        Returns the number of parameters specified for an individual
        connection. It can be zero.

        :rtype: Integer
        :raises: TypeError
        """
        pass

    @abstractmethod
    def setMask(self, mask):
        """
        Inform the generator of which source and target indexes exist
        (must always be called before any of the methods below)

        :param mask: Mask object. skip (specified in mask) can be used in
                     round-robin allocation schemes.

        :rtype: None
        :raises: TypeError
        """
        pass

    def setMasks(self, masks, local):
        """
        For a parallel simulator, we want to know the masks for all ranks

        :param masks: list of Mask objects
        :param mask: integer

        :rtype: None
        :raises:
        """
        self.setMask(masks[local])

    @abstractmethod
    def __len__(self):
        """
        Returns the number of connections in the generator.

        :rtype: Integer (the number of the connections).
        :raises: TypeError
        """
        pass

    @abstractmethod
    def __iter__(self):
        """
        Initializes and returns an iterator.
        Items are tuples (source_index, target_index, parameter0, parameter1, ...).
        The number of parameters is equal to arity.

        :rtype: Iterator
        :raises: TypeError
        """
        pass

    tagMap = {}

    @classmethod
    def selectImplementation(cls, tag, module):
        cls.tagMap[tag] = module

    @classmethod
    def fromXML(cls, root):
        """
        Returns a connection generator closure.
        """
        if not root.tag in cls.tagMap:
            raise NotImplementedError('found no implementation for XML tag %s' % root.tag)
        module = cls.tagMap[root.tag]
        return module.connectionGeneratorClosureFromXML(root)
