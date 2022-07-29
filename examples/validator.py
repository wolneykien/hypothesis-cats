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
from hypothesis.strategies import integers, text
from hypothesis_cats import subdivide, cat, cats, CatChecker, ExCat, parseCats
# import pytest

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

# @given(name=text(max_size=0))
# def test_name_empty(name):
#     with pytest.raises(TypeError, match='^Name'):
#         u = User(name)
# 
# @given(age=integers(max_value=0))
# def test_wrong_age(age):
#     with pytest.raises(ValueError, match='^Age'):
#         u = User('test', age=age)
# 
# @given(name=text(min_size=1), role=text(), age=integers(min_value=1))
# def test_good_parms(name, role, age):
#     u = User(name, role=role, age=age)
# 
# @given(name=text(), role=text(), age=integers())
# def test_all_naive(name, role, age):
#     if not name: # Bad: same logic as in __init__!
#         with pytest.raises(TypeError, match='^Name'):
#             u = User(name, role=role, age=age)
#     elif age <= 0: # Bad: same logic as in __init__!
#         with pytest.raises(ValueError, match='^Age'):
#             u = User(name, role=role, age=age)
#     else:
#         u = User(name, role=role, age=age)
# 
# # Although, it's possible to find the bug with the test function above
# # such test code is somehow meaningless: it uses the same logic as
# # the prameter validator itself.

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
# Uncomment to make the test pass:
#                 'requires': {
#                     'role': "empty"
#                 }
            }
        }
    }
})

@given(name=subdivide("name",
            cat("empty", text(max_size=0)),
            cat("non-empty", text(min_size=1))),
       role=subdivide("role",
            cat("empty", text(max_size=0)),
            cat("non-empty", text(min_size=1))),
       age=subdivide("age",
            cat("positive", integers(min_value=1)),
            cat("non-positive", integers(max_value=0))),
       cts=cats()
)
def test_all_better(name, role, age, cts):
    with CatChecker(cts, ctg_defs):
        u = User(name, role, age)

if __name__ == "__main__":
#    test_name_empty()
#    test_wrong_age()
#    test_good_parms()
#    test_all_naive()
    test_all_better()
