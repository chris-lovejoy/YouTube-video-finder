#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 16:09:52 2020

@author: chrislovejoy
"""


import typing as T
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import pandas as pd

# Load dependencies
import requests
from apiclient.discovery import build

DEFAULT_INVIDIOUS = "http://127.0.0.1:3000"


def get_start_date_string(search_period_days):
    """Returns string for date at start of search period."""
    search_start_date = datetime.today() - timedelta(search_period_days)
    date_string = datetime(
        year=search_start_date.year,
        month=search_start_date.month,
        day=search_start_date.day,
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    return date_string


def search_each_term(
    search_terms,
    api_key,
    uploaded_since,
    views_threshold=5000,
    num_to_print=5,
    invidious=None,
) -> T.Dict["str", pd.DataFrame]:
    """Uses search term list to execute API calls and print results."""
    if type(search_terms) == str:
        search_terms = [search_terms]

    list_of_dfs = []
    for index, search_term in enumerate(search_terms):
        df = find_videos(
            search_terms[index],
            api_key,
            views_threshold=views_threshold,
            uploaded_since=uploaded_since,
            use_invidious=True if invidious else False,
            session=Session(base=invidious) if invidious else None,
        )
        df = df.sort_values(["Custom_Score"], ascending=[0])
        list_of_dfs.append(df)

    # 1 - concatenate them all
    full_df = pd.concat((list_of_dfs), axis=0)
    full_df = full_df.sort_values(["Custom_Score"], ascending=[0])
    print("THE TOP VIDEOS OVERALL ARE:")
    print_top_videos(full_df, num_to_print)
    print("==========================\n")

    # 2 - in total
    for index, search_term in enumerate(search_terms):
        results_df = list_of_dfs[index]
        print("THE TOP VIDEOS FOR SEARCH TERM '{}':".format(search_terms[index]))
        print_top_videos(results_df, num_to_print)

    results_df_dict = dict(zip(search_terms, list_of_dfs))
    results_df_dict["top_videos"] = full_df

    return results_df_dict


def find_videos(
    search_terms,
    api_key,
    views_threshold,
    uploaded_since,
    use_invidious=True,
    session=None,
):
    """Calls other functions (below) to find results and populate dataframe."""

    # Initialise results dataframe
    dataframe = pd.DataFrame(
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
    )

    if use_invidious:
        if session is None:
            session = Session()
        return populate_dataframe_invidious(
            session.search_api(search_terms),
            dataframe,
            views_threshold,
            session,
        )
    # Run search
    search_results, youtube_api = search_api(search_terms, api_key, uploaded_since)

    return populate_dataframe(search_results, youtube_api, dataframe, views_threshold)


def search_api(search_terms, api_key, uploaded_since):
    """Executes search through API and returns result."""

    # Initialise API call
    youtube_api = build("youtube", "v3", developerKey=api_key)

    # Make the search
    results = (
        youtube_api.search()
        .list(
            q=search_terms,
            part="snippet",
            type="video",
            order="viewCount",
            maxResults=50,
            publishedAfter=uploaded_since,
        )
        .execute()
    )

    return results, youtube_api


def populate_dataframe(results, youtube_api, df, views_threshold):
    """Extracts relevant information and puts into dataframe"""
    # Loop over search results and add key information to dataframe
    i = 1
    for item in results["items"]:
        viewcount = find_viewcount(item, youtube_api)
        if viewcount > views_threshold:
            title = find_title(item)
            video_url = find_video_url(item)
            channel_url = find_channel_url(item)
            channel_id = find_channel_id(item)
            channel_name = find_channel_title(channel_id, youtube_api)
            num_subs = find_num_subscribers(channel_id, youtube_api)
            ratio = view_to_sub_ratio(viewcount, num_subs)
            days_since_published = how_old(item)
            score = custom_score(viewcount, ratio, days_since_published)
            df.loc[i] = [
                title,
                video_url,
                score,
                viewcount,
                channel_name,
                num_subs,
                ratio,
                channel_url,
            ]
        i += 1
    return df


@dataclass
class Session:

    num_subscriber_dict: dict = field(default_factory=dict)
    base: str = DEFAULT_INVIDIOUS

    def search_api(self, search_terms) -> T.List[T.Dict[str, T.Any]]:
        return requests.get(
            self.base + "/api/v1/search",
            params={"q": search_terms, "type": "video"},
        ).json()

    def find_num_subscribers(self, channel_id):
        if channel_id not in self.num_subscriber_dict:
            num_subscriber = (
                requests.get(
                    self.base + "/api/v1/channels/" + channel_id,
                    params={"fields": "subCount"},
                )
                .json()
                .get("subCount", None)
            )
            self.num_subscriber_dict[channel_id] = num_subscriber
            return num_subscriber
        return self.num_subscriber_dict[channel_id]


def populate_dataframe_invidious(results, df, views_threshold, session):
    """Extracts relevant information and puts into dataframe"""
    # Loop over search results and add key information to dataframe
    i = 1
    for item in results:
        viewcount = item.get("viewCount", 0)
        if viewcount > views_threshold:
            video_id = item.get("videoId", None)
            author_url = item.get("authorUrl", None)
            channel_id = item.get("authorId", None)
            num_subs = session.find_num_subscribers(channel_id)
            ratio = view_to_sub_ratio(viewcount, num_subs)
            args = [
                item.get("title", None),
                "https://youtu.be/" + video_id if video_id else None,
                custom_score(
                    viewcount,
                    ratio,
                    how_old_from_datetime(datetime.fromtimestamp(item["published"])),
                ),
                viewcount,
                item.get("author", None),
                num_subs,
                ratio,
                ("https://youtube.com" + author_url) if author_url else None,
            ]
            df.loc[i] = args
        i += 1
    return df


def print_top_videos(df, num_to_print):
    """Prints top videos to console, with details and link to video."""
    if len(df) < num_to_print:
        num_to_print = len(df)
    if num_to_print == 0:
        print("No video results found")
    else:
        for i in range(num_to_print):
            video = df.iloc[i]
            title = video["Title"]
            views = video["Views"]
            subs = video["Num_subscribers"]
            link = video["Video URL"]
            print(
                "Video #{}:\nThe video '{}' has {} views, from a channel \
with {} subscribers and can be viewed here: {}\n".format(
                    i + 1, title, views, subs, link
                )
            )
            print("==========================\n")


## ======================================================================= ##
## ====== SERIES OF FUNCTIONS TO PARSE KEY INFORMATION ABOUT VIDEOS ====== ##
## ======================================================================= ##


def find_title(item):
    title = item["snippet"]["title"]
    return title


def find_video_url(item):
    video_id = item["id"]["videoId"]
    video_url = "https://www.youtube.com/watch?v=" + video_id
    return video_url


def find_viewcount(item, youtube):
    video_id = item["id"]["videoId"]
    video_statistics = youtube.videos().list(id=video_id, part="statistics").execute()
    viewcount = int(video_statistics["items"][0]["statistics"]["viewCount"])
    return viewcount


def find_channel_id(item):
    channel_id = item["snippet"]["channelId"]
    return channel_id


def find_channel_url(item):
    channel_id = item["snippet"]["channelId"]
    channel_url = "https://www.youtube.com/channel/" + channel_id
    return channel_url


def find_channel_title(channel_id, youtube):
    channel_search = (
        youtube.channels().list(id=channel_id, part="brandingSettings").execute()
    )
    channel_name = channel_search["items"][0]["brandingSettings"]["channel"]["title"]
    return channel_name


def find_num_subscribers(channel_id, youtube):
    subs_search = youtube.channels().list(id=channel_id, part="statistics").execute()
    if subs_search["items"][0]["statistics"]["hiddenSubscriberCount"]:
        num_subscribers = 1000000
    else:
        num_subscribers = int(subs_search["items"][0]["statistics"]["subscriberCount"])
    return num_subscribers


def view_to_sub_ratio(viewcount, num_subscribers):
    if num_subscribers == 0:
        return 0
    else:
        ratio = viewcount / num_subscribers
        return ratio


def how_old_from_datetime(datetime_obj):
    # compatibility
    when_published_datetime_object = datetime_obj

    today_date = datetime.today()
    days_since_published = int((today_date - when_published_datetime_object).days)
    if days_since_published == 0:
        days_since_published = 1
    return days_since_published


def how_old(item):
    when_published = item["snippet"]["publishedAt"]
    when_published_datetime_object = datetime.strptime(
        when_published, "%Y-%m-%dT%H:%M:%SZ"
    )
    today_date = datetime.today()
    days_since_published = int((today_date - when_published_datetime_object).days)
    if days_since_published == 0:
        days_since_published = 1
    return days_since_published


def custom_score(viewcount, ratio, days_since_published):
    ratio = min(ratio, 5)
    score = (viewcount * ratio) / days_since_published
    return score
