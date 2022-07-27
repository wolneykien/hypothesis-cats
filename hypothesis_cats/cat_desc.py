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
Hypothesis strategy. This module defines utility classes for
category descriptors.
"""

from typing import Optional

class Cat():
    """
    A simple base category descriptor consisting of a category
    name and a comment.
    """

    def __init__(self, name: str = None,
                 comment: Optional[str] = None):
        """
        :param name: The name of the category.

        :param comment: The comment or a description for it.

        :raises ValueError: If the name is empty.
        """
        if not name:
            raise ValueError('Category name should not be empty!')
        self.name = name
        self.comment = comment

    def __repr__(self) -> str:
        """
        The default string representation of a category ommits
        the comment.

        :return: Name of the category.
        """
        return self.name

    @classmethod
    def from_dict(cls, d: dict) -> Cat:
        return Cat(**d)
