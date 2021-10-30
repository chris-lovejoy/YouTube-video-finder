#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import pytest
import requests

import video_finder as vf


@pytest.mark.parametrize(
    "input_, output", [[1, "2021-10-29T00:00:00Z"], [1.5, "2021-10-28T00:00:00Z"]]
)
def test_get_start_date_string(input_, output, freezer):
    assert vf.get_start_date_string(input_) == output


@pytest.mark.vcr()
@pytest.mark.golden_test("data/test_populate_dataframe_invidious*.yaml")
def test_populate_dataframe_invidious(freezer, golden):
    resp = requests.get(
        "http://127.0.0.1:3000/api/v1/search",
        params={"q": golden["q"], "type": "video"},
    )
    session = vf.Session()
    res_df = vf.populate_dataframe_invidious(
        results=resp.json(),
        df=pd.DataFrame(
            columns=(
                "Title",
                "Video URL",
                "Custom_Score",
                "Views",
                "Channel Name",
                "Num_subscribers",
                "View-Subscriber Ratio",
                "Channel URL",
            )
        ),
        views_threshold=0,
        session=session,
    )
    assert res_df.to_dict() == golden.out["output"]
    assert session.num_subscriber_dict == golden.out["num_subscriber_dict"]
