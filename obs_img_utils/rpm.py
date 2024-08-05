# Copyright (c) 2024 SUSE LLC, All rights reserved.
#
# This file is part of obs-img-utils. obs-img-utils provides
# an api and command line utilities for images in OBS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from itertools import zip_longest

# RPM version comparison adapted from:
# https://stackoverflow.com/questions/3206319/how-do-i-compare-rpm-versions-in-python/42967591#42967591

# Emulate RPM field comparisons
#
# * Search each string for alphabetic fields [a-zA-Z]+ and
#   numeric fields [0-9]+ separated by junk [^a-zA-Z0-9]*.
# * Successive fields in each string are compared to each other.
# * Alphabetic sections are compared lexicographically, and the
#   numeric sections are compared numerically.
# * In the case of a mismatch where one field is numeric and one is
#   alphabetic, the numeric field is always considered greater (newer).
# * In the case where one string runs out of fields, the other is always
#   considered greater (newer).


_subfield_pattern = re.compile(
    r"(?P<junk>[^a-zA-Z0-9]*)((?P<text>[a-zA-Z]+)|(?P<num>[0-9]+))"
)


def _iter_rpm_subfields(field):
    """Yield subfields as 2-tuples that sort in the desired order
    Text subfields are yielded as (0, text_value)
    Numeric subfields are yielded as (1, int_value)
    """
    for subfield in _subfield_pattern.finditer(field):
        text = subfield.group("text")
        if text is not None:
            yield (0, text)
        else:
            yield (1, int(subfield.group("num")))


def _compare_rpm_field(lhs, rhs):
    # Short circuit for exact matches (including both being None)
    if lhs == rhs:
        return 0
    # Otherwise assume both inputs are strings
    lhs_subfields = _iter_rpm_subfields(lhs)
    rhs_subfields = _iter_rpm_subfields(rhs)
    for lhs_sf, rhs_sf in zip_longest(lhs_subfields, rhs_subfields):
        if lhs_sf == rhs_sf:
            # When both subfields are the same, move to next subfield
            continue
        if lhs_sf is None:
            # Fewer subfields in LHS, so it's less than/older than RHS
            return -1
        if rhs_sf is None:
            # More subfields in LHS, so it's greater than/newer than RHS
            return 1
        # Found a differing subfield, so it determines the relative order
        return -1 if lhs_sf < rhs_sf else 1
    # No relevant differences found between LHS and RHS
    return 0


def compare_rpm_labels(lhs, rhs):
    lhs_epoch, lhs_version, lhs_release = lhs
    rhs_epoch, rhs_version, rhs_release = rhs
    result = _compare_rpm_field(lhs_epoch, rhs_epoch)
    if result:
        return result
    result = _compare_rpm_field(lhs_version, rhs_version)
    if result:
        return result
    return _compare_rpm_field(lhs_release, rhs_release)
