#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

import video_finder as vf


@pytest.mark.parametrize(
    "input_, output", [[1, "2021-10-28T00:00:00Z"], [1.5, "2021-10-28T00:00:00Z"]]
)
def test_get_start_date_string(input_, output, freezer):
    assert vf.get_start_date_string(input_) == output
