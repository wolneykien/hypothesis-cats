# This file is a part of the Hypothesis-Cats Python package.
#
# Copyright (C) 2022  Paul Wolneykien <manowar@altlinux.org>
#
# This file is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301, USA.

"""
Hypothesis-Cats allows you to classify values generated by a
`Hypothesis <https://hypothesis.readthedocs.io/en/latest/>`_ 
strategy. This module defines stuff for making assertions
based on categories of the given set of values.
"""

from typing import Any, Optional, Union, Sequence, TypedDict, \
    Callable, List, Pattern
from collections.abc import Iterable
import re

from .cat_desc import Cat
from .cat_strategies import cats

class GuardedRaisesDict(TypedDict):
    """
    A helper class defining the dictionary layout for parsing
    ``'raises': { ... }`` dictionaries in the category declarations.
    """
    err: type[Exception]
    pattern: Union[str, Pattern]
    requires: dict[str, str]

def tryGetCatName(ctg: Any) -> str:
    """
    Tryies to return the name of the given category. If ``ctg`` is a
    a :class:`.cat_desc.Cat` value, the functions returns ``ctg.name``.
    Otherwise, if the given object is a dictionary, it tries to access
    its ``name`` key. Otherwise, a string representation of the whole
    object as ``str(ctg)`` is returned.

    :param ctg: A category name or a descriptor.

    :return: The name of the category as described above.

    :raises KeyError: If there is no ``'name'`` key in the
        supplied dictionary.

    :raises ValueError: If the value ``'name'`` is empty.
    """
    ctgobj: Optional[Cat] = None
    if isinstance(ctg, Cat):
        ctgobj = ctg
    elif isinstance(ctg, dict):
        ctgobj = Cat.from_dict(ctg)

    if ctgobj:
        return ctgobj.name
    else:
        return str(ctg)

class GuardedRaises():
    """
    A class representing an :class:`Exception` exceptation, declared by
    an :class:`ExCat` category.
    """

    def __init__(self,
                 err: Union[None, type[Exception]] = None,
                 pattern: Union[None, str, Pattern] = None,
                 requires: Union[None, dict[str, str]] = None):
        """
        :param err: An :class:`Exception` type that is expected to be
            raised by the code under test if the value of the
            corresponding parameter falls into the surrounding
            category (i.e. the category that declares this
            expectation).

        :param pattern: A string with a regular expression or an
            already compiled :class:`re.Pattern` which is used to check
            the error message. If the match is unsuccessful that the
            exception expectation is also not met.

        :param requires: A string-string dictionary declaring
            category names of values of other classes. The declared
            exception is only expected if the requirements are empty
            or are met.

        :raises ValueError: If no exception type was supplied.
        """
        if not err:
            raise ValueError('An exception type should be specified!')
        self.err = err
        if pattern:
            self.pattern = re.compile(pattern)
        self.requires = requires

    def isExpected(self, ex: Exception, cts: dict[str, Any]) -> bool:
        """
        Checks if the given exception is expected under conditions,
        determined by the supplied class-category layout.

        :param ex: The :class:`Exception` object to examine.

        :param cts: The category layout normally exposed by the
            :func:`.cat_strategies.classify` and
            :func:`.cat_strategies.subdivide` functions and accessed
            via the :func:`.cat_strategies.cats` function.

        :return: ``True`` if the supplied exception object matches
            the declared type and regular expression, and all
            requirements, if any, are met by the supplied
            category layout. ``False`` otherwise.
        """
        if isinstance(ex, self.err):
            if self.pattern:
                if self.pattern.match(str(ex)):
                    return self.checkReqs(cts)
        return False

    def checkReqs(self, cts: dict[str, Any]) -> bool:
        """
        Checks that all requirements, if any, are met by the supplied
        class-category layout.

        :param cts: The category layout normally exposed by the
            :func:`.cat_strategies.classify` and
            :func:`.cat_strategies.subdivide` functions and accessed
            via the :func:`.cat_strategies.cats` function.

        :return: ``True`` if all requirements are met or no
            requirements are declared. ``False`` otherwise.
        """
        if self.requires:
            for r in self.requires:
                if self.requires[r]:
                    if r not in cts:
                        return False
                    else:
                        if self.requires[r] != tryGetCatName(cts[r]):
                            return False

        return True

    def __repr__(self) -> str:
        """
        Returns the string representation of this expectation.

        :return: A string consisting of the exception class name
            and the optional regular expression. For instance:
            ``TypeError(/^Name/)``.
        """
        estr = self.err.__name__

        if self.pattern:
            estr = estr + "(/" + self.pattern.pattern + "/)"

        return estr

class ExCat(Cat):
    """
    A category descriptor with exception expectations.
    With the use of :class:`CatChecker` can be replaced by the
    corresponding dictionary object.
    """

    def __init__(self,
                 name: str = None,
                 comment: Optional[str] = None,
                 raises: Union[
                     None,
                     type[Exception], GuardedRaises,
                     GuardedRaisesDict,
                     Sequence[
                         Union[
                             type[Exception], GuardedRaises,
                             GuardedRaisesDict
                         ]
                     ]
                 ] = None):
        """
        :param name: The name of the category.

        :param comment: The comment or a description for it.

        :param raises: Accepts an :class:`Exception` type,
            a :class:`GuardedRaises` object or a corresponding
            dictionary object or a sequence of any of such
            values. For all supplied :class:`Exception` types
            corresponding :class:`GuardedRaises` objects are
            constructed automatically.

        :raises ValueError: If name is empty or no exception type
            was specified in one or more dictionary objects passed
            to ``raises``.
        """
        super().__init__(name, comment)

        self.raises: List[GuardedRaises] = []
        if raises:
            if isinstance(raises, Sequence):
                for r in raises:
                    self.appendRaises(r)
            else:
                self.appendRaises(raises)

    def appendRaises(self,
                     raises: Union[
                         type[Exception], GuardedRaises,
                         GuardedRaisesDict
                     ]):
        """
        Appends the given single exception expectation to the list
        of the expected raises.

        :param raises: Accepts an :class:`Exception` type,
            a :class:`GuardedRaises` object or a corresponding
            dictionary object.

        :raises TypeError: If it has failed to interpret the given
            ``raises`` object.

        :raises ValueError: If no exception type was specified in the
            dictionary object passed to ``raises``.
        """
        if isinstance(raises, type) and \
               issubclass(raises, Exception):
            self.raises.append(GuardedRaises(raises, None))
        elif isinstance(raises, dict):
            self.raises.append(GuardedRaises(**raises))
        elif isinstance(raises, GuardedRaises):
            self.raises.append(raises)
        else:
            raise TypeError('appendRaises(r) expects an exception type or a GuardedRaises object optionallly represented by a plain dictionary.')

    def isExpected(self, ex: Exception, cts: dict[str, Any]) -> bool:
        """
        Checks if the given exception is expected under conditions,
        determined by the supplied class-category layout.

        :param ex: The :class:`Exception` object to examine.

        :param cts: The category layout normally exposed by the
            :func:`.cat_strategies.classify` and
            :func:`.cat_strategies.subdivide` functions and accessed
            via the :func:`.cat_strategies.cats` function.

        :return: ``True`` if the supplied exception object is matched
            by *any* of the exception expectations declared for this
            category and that the corresponding requirements, if any,
            are met by the supplied category layout. ``False``
            otherwise.
        """
        for r in self.raises:
            if r.isExpected(ex, cts):
                return True

        return False

    def expectedRaises(self, cts: dict[str, Any]) -> List[GuardedRaises]:
        """
        Returns the list of all exception expectation whose
        requirements are met by the supplied category layout.

        :param cts: The category layout normally exposed by the
            :func:`.cat_strategies.classify` and
            :func:`.cat_strategies.subdivide` functions and accessed
            via the :func:`.cat_strategies.cats` function.

        :return: The, possible empty, list of exception expectation
            objects whose requirements are met by the supplied
            category layout.
        """
        expected: List[GuardedRaises] = []
        for r in self.raises:
            if r.checkReqs(cts):
                expected.append(r)

        return expected

    @classmethod
    def from_dict(cls, d: dict) -> 'ExCat':
        """
        Tries to create the :class:`ExCat` from a dictionary.
        The dictionary has to define a value under the ``'name'`` key.
        The optional ``'comment'`` and ``'raises'`` values, if such
        keys are is present, are also used. The other values in the
        dictionary are silently ignored.

        :param d: A dictionary with at least ``'name'`` and,
            optionally, ``'comment'`` and ``'raises'`` keys.

        :return: The fresh :class:`ExCat:` instance with name, comment
            and the list of exception expectations taken from the
            dictionary.

        :raises KeyError: If there is no ``'name'`` key in the
            supplied dictionary.

        :raises ValueError: If the value ``'name'`` is empty.
        """
        _d = {}
        _d['name'] = d['name']
        if 'comment' in d:
            _d['comment'] = d['comment']
        if 'raises' in d:
            _d['raises'] = d['raises']
        return cls(**d)

def tryExCat(ctg: Any, ctg_defs: Optional[dict[str, ExCat]] = None) -> Optional[ExCat]:
    """
    Returns the supplied ``ctg`` value as is, if it's already
    an :class:`ExCat` value. Otherwise, there is a chance to get a
    referenced one from the separated set of category definitions,
    if any, or to build a :class:`ExCat` object if ``ctg`` happens
    to be a dictionary.

    :param ctg: A category name, referencing its definition in the
        ``ctg_defs`` dictionary, or a category descriptor in the form
        of a :class:`ExCat` object or a dictionary.

    :param ctg_defs: The dictionary with category descriptors.
        See :class:`CatChecker` for details. Note, however, that
        rather than accept a class-category layout, this function
        expects a set of categories defined for a single particular
        class of values.

    :return: An :class:`ExCat` value corresponding to the supplied
        argument.

    :raises KeyError: If the referenced category isn't found in the
        supplied ``ctg_defs`` dictionary or if there is no ``'name'``
        key in the category descriptor passed in ``ctg``.

    :raises ValueError: If the value ``'name'`` is empty or no
        exception type was specified in one or more
        ``'raises': {...}`` dictionary objects.
    """
    exctg: Optional[ExCat] = None
    if isinstance(ctg, ExCat):
        exctg = ctg
    elif isinstance(ctg, Cat):
        exctg = ExCat(ctg.name, ctg.comment)
    elif isinstance(ctg, dict):
        exctg = ExCat.from_dict(ctg)

    if exctg:
        return exctg
    elif ctg_defs:
        ctgname = str(ctg)
        if ctgname in ctg_defs:
            return ctg_defs[ctgname]

    return None

class CatChecker():
    """
    A `context manager <https://docs.python.org/3/library/stdtypes.html#typecontextmanager>`_
    implementation that could be used to check for expected exceptions
    while testing modules, classes and functions. The example usage
    is as follows:

    .. code-block:: python

       from hypothesis import given
       from hypothesis.strategies import integers, text
       from hypothesis_cats import subdivide, cat, cats, CatChecker

       class User():
           def __init__(self, name: str, role: str = None, age: int = None):
               if not name:
                   raise TypeError('Name should not be empty!')
               self.name = name

               if role:
                   self.role = role
                   return # <---------- BUG!

               if age != None:
                   if age <= 0:
                       raise ValueError('Age should be a positive number!')
                   self.age = age

       @given(name=subdivide("name",
                   cat({ 'name': "empty",
                         'raises': {
                             'err': TypeError,
                             'pattern': '^Name'
                         }
                       }, text(max_size=0)),
                   cat({ 'name': "non-empty" },
                       text(min_size=1))),
              role=text(),
              age=subdivide("age",
                   cat({ 'name': "positive" },
                       integers(min_value=1)),
                   cat({ 'name': "non-positive",
                         'raises': {
                             'err': ValueError,
                             'pattern': '^Age',
                         }
                       }, integers(max_value=0))),
              cts=cats()
       )
       def test_user(name, role, age, cts):
           with CatChecker(cts):
               u = User(name, role, age)

    With the use of ``'requires': { ... }`` it's possible to state that
    the age to role relation in the ``User`` class constructor is not a
    bug, but the desired behavior. For a complete example see the
    ``validator.py`` file from the ``examples/`` directory.

    See :func:`parseCats` to learn how to write more compact
    descriptors.
    """

    def __init__(self, cts: dict[str, Any],
                 ctg_defs: Optional[dict[str, dict[str, Union[Cat, ExCat, dict[str, Any]]]]] = None):
        """
        :param cts: The category layout normally exposed by the
            :func:`.cat_strategies.classify` and
            :func:`.cat_strategies.subdivide` functions and accessed
            via the :func:`.cat_strategies.cats` function. The
            categories in the layout can be represented by complex
            :class:`ExCat` descriptors (possible, in the form of
            dictionaries) or by simple strings referencing the
            corresponding descriptions defined elsewhere. In the
            latter case that definitions should be passed separately
            wiin the ``ctg_defs`` param.

        :param ctg_defs: The category definitions. For convenience,
            complex descriptors describing categories along with
            exception expectations and their relationships might be
            defined separately from the testing strategies. You can
            use :func:`parseCats` to get the right :class:`ExCat`
            descriptor dictionary from the plain dictionary.

        :raises KeyError: If there is no ``'name'`` key in one of the
            category descriptors passed in ``ctg_defs``.

        :raises ValueError: Raises :class:`ValueError` for the same
            cases as :func:`parseCats`.
        """
        self.cts = cts
        if ctg_defs:
            self.ctg_defs = parseCats(ctg_defs)
        else:
            self.ctg_defs = {}

    def __enter__(self) -> 'CatChecker':
        """
        Returns this context manager object. This function is an entry
        point and should not be directly invoked. The return value
        could be get via the ``as`` part of the ``with`` expression.

        :return: The dictionary representing all currently expected
            exceptions.
        """
        return self

    def __exit__(self, exc_type: type[Exception],
                 exc_value: Exception, traceback) -> bool:
        """
        The exit point of the context manager. Controls, whether the
        raised exception, if any, should propagate further or, if it
        is an expected exception, should be suppressed.

        :return: ``True`` if the given exception happens to be one
        of the expected exceptions.
        """
        if exc_value:
            for cls in self.cts:
                exctg = self.tryGetCat(cls)
                if exctg:
                    if exctg.isExpected(exc_value, self.cts):
                        return True
            return False
        else:
            expected = self.expectedRaises()
            if expected:
                raise AssertionError('One of the following exceptions was expected: %s' % expected)

        return False

    def tryGetCat(self, cls: str) -> Optional[ExCat]:
        """
        Tries to get the current category for the given class of
        values using the class-category layout and an optional
        dictionary with category descriptors that were passed upon
        construction of this :class:`CatChecker` instance.

        :param cls: The name of the value class.

        :return: The corresponding category descriptor, if found.
        """
        if self.ctg_defs and cls in self.ctg_defs:
            return tryExCat(self.cts[cls],
                            ctg_defs=self.ctg_defs[cls])
        return None

    def expectedRaises(self) -> dict[str, List[GuardedRaises]]:
        """
        Returns the dictionary representing all exceptions,
        expected under the current category layout (i.e. the
        categories of values currently given for the test)
        with their relation to particular values (more precicely,
        the declared classes of values).

        :return: The dictionary representing all currently expected
            exceptions as described above.
        """
        expected: dict[str, List[GuardedRaises]] = {}
        for cls in self.cts:
            exctg = self.tryGetCat(cls)
            if exctg:
                exlist = exctg.expectedRaises(self.cts)
                if exlist:
                    expected[cls] = exlist

        return expected

def parseCats(desc_layout: dict[str, dict[str, Union[Cat, ExCat, dict[str, Any]]]]) -> dict[str, dict[str, ExCat]]:
    """
    Parses the given value-class -> catecory-descriptor dictionary.
    The descriptors for named classes of values might be represented
    by already constructed :class:`.cat_desc.Cat` and :class:`ExCat`
    objects or by dictionaries. When using the dictionary form it's
    possible to omit the ``name`` field: then the corresponding
    key of the surrounding dictionary is used. For instance:

    .. code-block:: python

       ctg_defs = parseCats({
           'name': {
               'empty': {
                   'raises': {
                       'err': TypeError,
                       'pattern': '^Name'
                   }
               }
           },
           'age': {
               'non-positive': {
                   'raises': {
                       'err': ValueError,
                       'pattern': '^Age',
                        'requires': {
                            'role': "empty"
                        }
                   }
               }
           }
       })

    :param desc_layout: A value-class -> catecory-descriptor
        dictionary as described above.

    :return: The corresponding value-class -> catecory-descriptor
        dictionary with :class:`ExCat` descriptors.

    :raises ValueError: If no exception type was specified in one
        or more ``'raises': {...}`` dictionary objects or when
        a name inside a category descriptor doesn't match the
        key under which thay category is defined.
    """
    ret: dict[str, dict[str, ExCat]] = {}
    for cls in desc_layout:
        ret[cls] = {}
        for ctgname in desc_layout[cls]:
            exctg = None
            ctg = desc_layout[cls][ctgname]
            if isinstance(ctg, ExCat):
                exctg = ctg
            elif isinstance(ctg, Cat):
                exctg = ExCat(ctg.name, ctg.comment)
            else:
                if 'name' in ctg:
                    exctg = ExCat(**ctg)
                else:
                    exctg = ExCat(name=ctgname, **ctg)

            if exctg.name != ctgname:
                raise ValueError('A descriptor with name "%s" is specified under key "%s".')

            ret[cls][ctgname] = exctg

    return ret
