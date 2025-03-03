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


# Globals
A_IS_NEWER = 1
A_EQUALS_B = 0
B_IS_NEWER = -1


def _compare_segment(segment_a, segment_b):
    """
    Compares 2 segments of a version tag
    """
    if segment_a[0].isdigit():
        _remove_leading_zeroes(segment_a)
        _remove_leading_zeroes(segment_b)
        if len(segment_a) > len(segment_b):
            return A_IS_NEWER
        elif len(segment_a) < len(segment_b):
            return B_IS_NEWER
    if segment_a == segment_b:
        return A_EQUALS_B
    else:
        if segment_a > segment_b:
            return A_IS_NEWER
        else:
            return B_IS_NEWER


def _pop_digits(char_list):
    """Pops the leading digits of a char list"""
    digits = []
    while (
        len(char_list) != 0 and
        char_list[0].isdigit()
    ):
        digits.append(char_list.pop(0))
    return digits


def _pop_letters(char_list):
    """Pops the leading letters of a char list"""
    letters = []
    while (
        len(char_list) != 0 and
        char_list[0].isalpha()
    ):
        letters.append(char_list.pop(0))
    return letters


def _pop_segments_and_compare(chars_a, chars_b):
    """Pops the next segment of the tag and returns the compared value"""
    first_is_digit = chars_a[0].isdigit()
    if first_is_digit:
        segment_a = _pop_digits(chars_a)
        segment_b = _pop_digits(chars_b)
    else:
        segment_a = _pop_letters(chars_a)
        segment_b = _pop_letters(chars_b)

    # B segment length is 0 if:
    # - a starts with digit and b with letter
    # - vice-versa
    if len(segment_b) == 0:
        if first_is_digit:
            return A_IS_NEWER
        return B_IS_NEWER
    compare_segment_result = _compare_segment(segment_a, segment_b)
    return compare_segment_result


def _remove_non_alphanumeric_start(char_list):
    """Removes non-alphanumeric or non-~ leading characters"""
    while len(char_list) != 0:
        if (
            (
                char_list[0].isalnum() and
                isascii(char_list[0])
            ) or
            char_list[0] == '~' or
            char_list[0] == '^'
        ):
            return
        char_list.pop(0)


def _remove_leading_zeroes(char_list):
    """Removes the leading zeroes of a char list"""
    while (
        len(char_list) != 0 and
        char_list[0] == '0'
    ):
        char_list.pop(0)


def compare_version(a_tag, b_tag):
    """Compares one version string to another"""
    if a_tag == b_tag:
        return A_EQUALS_B

    chars_a, chars_b = list(a_tag), list(b_tag)
    while len(chars_a) != 0 and len(chars_b) != 0:
        _remove_non_alphanumeric_start(chars_a)
        _remove_non_alphanumeric_start(chars_b)

        if len(chars_a) == 0 or len(chars_b) == 0:
            break

        if (
            (chars_a[0] == '~' and chars_b[0] == '~') or
            (chars_a[0] == '^' and chars_b[0] == '^')
        ):
            chars_a.pop(0)
            chars_b.pop(0)
        elif chars_a[0] == '~':
            return B_IS_NEWER
        elif chars_b[0] == '~':
            return A_IS_NEWER
        elif chars_a[0] == '^':
            if len(chars_b) == 0:
                # If A is a snapshot(^) and B the base version
                # A is newer
                return A_IS_NEWER
            else:
                # A is a snapshot but B has more fields
                # B is newer
                B_IS_NEWER
        elif chars_b[0] == '^':
            if len(chars_a) == 0:
                return B_IS_NEWER
            else:
                A_IS_NEWER

        segment_result = _pop_segments_and_compare(chars_a, chars_b)
        if segment_result != A_EQUALS_B:
            return segment_result
    if len(chars_a) == len(chars_b):
        return A_EQUALS_B

    if len(chars_a) > len(chars_b):
        if chars_a[0] == '~':
            return B_IS_NEWER
        else:
            return A_IS_NEWER
    else:
        if chars_b[0] == '~':
            return A_IS_NEWER
        else:
            return B_IS_NEWER


def compare_rpm_labels(a_label, b_label):
    """ Compares tuples of epoch, version and release"""
    a_epoch, a_version, a_release = a_label
    b_epoch, b_version, b_release = b_label

    if a_epoch != b_epoch:
        return A_IS_NEWER if a_epoch > b_epoch else B_IS_NEWER

    version_compare = compare_version(a_version, b_version)
    if version_compare != A_EQUALS_B:
        return version_compare
    release_compare = compare_version(a_release, b_release)
    return release_compare


def isascii(string_to_check):
    """
    Returns a boolean indicating if string provided is ascii or not.
    Python 3.6 compatible
    """
    try:
        return string_to_check.isascii()
    except AttributeError:
        return all([ord(c) < 128 for c in string_to_check])
