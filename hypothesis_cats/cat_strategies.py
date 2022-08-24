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
strategy. This module defines a strategy to assign category
descriptors to values generated by other strategies, a strategy to
extract categorized values while exposing the resulting category
descriptor to the shared dictionary and another ones to access that
dictionary.
"""

from hypothesis import given
from hypothesis import strategies as st

# Typing
from typing import Union, Sequence, Any, Callable, TypeVar, \
    Optional, Mapping

T = TypeVar('T')

try:
    from typing import TypeAlias # type: ignore [attr-defined]
except ImportError:
    from typing_extensions import TypeAlias

try:
    DrawFn: TypeAlias = st.DrawFn # type: ignore [attr-defined]
except AttributeError:
    # In case of an older version of Hypothesis that doesn't define
    # the DrawFn type.
    DrawFn = Callable[[st.SearchStrategy[T]], T]

# The module
CATS_LAYOUT_KEY = '_hypothesis_cats_layout'
CATS_DESC_KEY = '_hypothesis_cats_desc'

@st.composite
def __just__(draw: DrawFn, val: Any) -> Any:
    """
    Just for reliability.

    The Hypothesis docs says that the ``val`` isn't copied.
    Hu Nose, however...
    """
    return val

@st.composite
def cat(draw: DrawFn, cat_desc: Any, base_st: st.SearchStrategy[T]) -> tuple[T, Any]:
    """
    Generates pair tuples by pairing the values generated by the
    underlying base strategy with the given category descriptor or
    a category marker.

    :param draw: A special function supplied by Hypothesis.

    :param cat_desc: Any value you want to assign as a category
        descriptor or a category marker. For the purpose of making
        assertions based on given category layout see
        :class:`.cat_checks.CatChecker.`

    :param base_st: The base strategy to get values from.

    :return: A strategy generating value-category pair tuples.

    For instance, the following is a way to produce integers values
    marked with the given string:

    .. code-block:: pycon

       >>> cat('CAT-1', integers()).example()
       (-26556, 'CAT-1')

    See the :func:`classify` for a complete example.
    """
    return draw(st.tuples(base_st, __just__(cat_desc)))

@st.composite
def cats(draw: DrawFn, dictObj: Optional[Mapping] = None) -> Mapping[str, Any]:
    """
    Within the given test run always returns the shared dictionary
    object where resulting category layout is exposed.

    :param draw: A special function supplied by Hypothesis.

    :param dictObj: An optional base dictionary object to be used
        to represent the layout. By default, plain ``{}`` is
        instantiated.

    :return: The set of categories that consist the given
        example data in the form of class-category dictionary.
    """
    if dictObj is None:
        dictObj = {}
    return draw(st.shared(__just__(dictObj), key=CATS_LAYOUT_KEY))

@st.composite
def getcat(draw: DrawFn, class_name: str,
           dictObj: Optional[Mapping] = None) -> Any:
    """
    Extracts the named category descriptor or marker from the shared
    dictionary where the resulting category layout is exposed.

    :param draw: A special function supplied by Hypothesis.

    :param class_name: An arbitrary name used to distinguish a class
        of values subdivided into a number of categories.

    :param dictObj: An optional base dictionary object to be passed
        to :func:`cats`.

    :return The category descriptor or the category marker of the
        given class of values within the current category layout of
        the example data.
    """
    return draw(cats(dictObj=dictObj))[class_name]

@st.composite
def classify(draw: DrawFn,
             class_name: str,
             base_st: st.SearchStrategy[tuple[T, Any]],
             dictObj: Optional[Mapping] = None) -> T:
    """
    Extracts the original values from value-category tuples produced
    by the :func:`cat` strategy while exposing the corresponding
    category descriptors or markers to the shared dictionary that can
    be accessed via :func:`cats` or :func:`getcat.`

    :param draw: A special function supplied by Hypothesis.

    :param class_name: An arbitrary name used to distinguish a class
        of values subdivided into a number of categories.

    :param base_st: The base strategy producing value-category tuples.

    :param dictObj: An optional base dictionary object to be passed
        to :func:`cats`.

    :return: The original values extracted from value-category tuples.

    This is how to test a sign function using the cats approach:

    .. code-block:: python

       from hypothesis import given
       from hypothesis.strategies import integers, one_of
       from hypothesis_cats import classify, cat, cats
       
       def my_sgn(x):
           return x > 0
       
       @given(
           x=classify("x", one_of(
               cat("positive", integers(min_value=1)),
               cat("non-positive", integers(max_value=0))
           )),
           cts=cats()
       )
       def test_sgn(x, cts):
           if cts["x"] == "positive":
               assert my_sgn(x)
           else:
               assert not my_sgn(x)

    While the same effect can be achieved with the use of just two
    corresponding separate test functions, it might not be so easy to
    write the set of test functions for a more complex functionality.
    See :class:`.cat_checks.CatChecker` for an example.
    """
    cts = draw(cats(dictObj=dictObj))
    catval = draw(base_st)
    cts[class_name] = catval[1]
    return catval[0]

@st.composite
def subdivide(draw: DrawFn,
              class_name: str,
              *onto: st.SearchStrategy[tuple[T, Any]],
              dictObj: Optional[Mapping] = None) -> T:
    """
    Implements the behavior of :func:`classify` + :func:`st.one_of.`
    I.e., instead of writing
    ``classify('x', one_of(cat('I',...), cat('II',...)))``
    you can simply write ``subdivide('x', cat('I', ...), cat('II', ...))``.

    :param draw: A special function supplied by Hypothesis.

    :param class_name: An arbitrary name used to distinguish a class
        of values subdivided into a number of categories.

    :param onto: A number of :func:`cat` strategies producing
        value-category tuples.

    :param dictObj: An optional base dictionary object to be passed
        to :func:`cats`.

    :return: The original values extracted from value-category tuples.
    """
    return draw(classify(class_name, st.one_of(*onto),
                         dictObj=dictObj))

@st.composite
def cats_desc(draw: DrawFn, desc: Optional[Mapping[str, Any]] = None) -> Mapping[str, Any]:
    """
    Within the given test run always returns the shared dictionary
    object for category descriptors.

    :param draw: A special function supplied by Hypothesis.

    :param desc: Optional dictionary object with category descriptors.
      If specified, then the shared dict is updated with values in
      the given one.

    :return: The shared dictionary for category descriptors.
    """
    if not desc:
        desc = {}
    shared_desc = draw(st.shared(__just__(desc), key=CATS_DESC_KEY))
    if desc:
        shared_desc.update(desc)
    return shared_desc

def nonequal(src: st.SearchStrategy[T], eq_by: Optional[Callable[[T, T], bool]] = None) -> Callable[[Any], st.SearchStrategy[T]]:
    """
    Returns a function to be used with
    :func:`st.SearchStrategy.flatmap` that filters out values of the
    given strategy that are equal to values produced by the base
    strategy.

    :param src: A strategy to draw values from.

    :param eq_by: An optional equality function.

    :return: A function that filters out values that are
        equal to values of the base, i.e. mapped, strategy.
    """
    if eq_by is not None:
        eq_by_func = eq_by
        return lambda v0: src.filter(
            lambda v: not eq_by_func(v, v0)
        )
    else:
        return lambda v0: src.filter(
            lambda v: v != v0
        )
