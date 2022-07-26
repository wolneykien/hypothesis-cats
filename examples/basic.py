# This file is an example of using the Hypothesis-Cats Python package.
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

from hypothesis import given
from hypothesis.strategies import integers, one_of
from hypothesis_cats import classify, cat, cats

def my_sgn(x):
    return x > 0

@given(x=integers())
def test_naive(x):
    if x > 0:
        assert my_sgn(x)
    else:
        assert not my_sgn(x)

# What's wrong with the test function above is that it tries
# to check my_sgn() correctness using _the same logic_ as
# used in my_sgn() itself! Let's try to get things better:

@given(
    x=classify("x", one_of(
        cat("positive", integers(min_value=1)),
        cat("non-positive", integers(max_value=0))
    )),
    cts=cats()
)
def test_better(x, cts):
    if cts["x"] == "positive":
        assert my_sgn(x)
    else:
        assert not my_sgn(x)

if __name__ == "__main__":
    test_naive()
    test_better()
