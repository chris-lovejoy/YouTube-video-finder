#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 16:09:52 2020

@author: chrislovejoy
"""


# Load dependencies
import pandas as pd
from datetime import datetime, timedelta
from apiclient.discovery import build

def get_start_date_string(search_period_days):
    """Returns string for date at start of search period."""
    search_start_date = datetime.today() - timedelta(search_period_days)
    date_string = datetime(year=search_start_date.year,month=search_start_date.month,
                           day=search_start_date.day).strftime('%Y-%m-%dT%H:%M:%SZ')
    return date_string


def search_each_term(search_term_list, api_key, uploaded_since,
                        views_threshold=5000, num_to_print=5):
    """Uses search term list to execute API calls and print results."""
    if type(search_term_list) == str:
        num_searches = 1
        # convert string search term into list
        search_term = search_term_list
        search_term_list = []
        search_term_list.append(search_term)
    elif type(search_term_list) == list:
        num_searches = len(search_term_list)
    else:
        num_searches = 0


    list_of_dfs = []
    for i in range(num_searches):
        df = find_videos(search_term_list[i], api_key, views_threshold=views_threshold,
                         uploaded_since = uploaded_since)
        df = df.sort_values(['Custom_Score'], ascending=[0])
        list_of_dfs.append(df)

    # 1 - concatenate them all
    full_df = pd.concat((list_of_dfs),axis=0)
    full_df = full_df.sort_values(['Custom_Score'], ascending=[0])
    print("THE TOP VIDEOS OVERALL ARE:")
    print_top_videos(full_df, num_to_print)
    print("==========================\n")

    # 2 - in total
    for i in range(num_searches):
        results_df = list_of_dfs[i]
        print("THE TOP VIDEOS FOR SEARCH TERM '{}':".format(search_term_list[i]))
        print_top_videos(results_df, num_to_print)

    results_df_dict = dict(zip(search_term_list, list_of_dfs))
    results_df_dict['top_videos'] = full_df

    return results_df_dict


def find_videos(search_terms, api_key, views_threshold, uploaded_since):
    """Calls other functions (below) to find results and populate dataframe."""

    # Initialise results dataframe
    dataframe = pd.DataFrame(columns=('Title', 'Video URL', 'Custom_Score',
                            'Views', 'Channel Name','Num_subscribers',
                            'View-Subscriber Ratio','Channel URL'))

    # Run search
    search_results, youtube_api = search_through_api(search_terms, api_key,
                                                        uploaded_since)

    results_df = populate_dataframe(search_results, youtube_api, dataframe,
                                                        views_threshold)

    return results_df


def search_through_api(search_terms, api_key, uploaded_since):
    """Executes search through API and returns result."""

    # Initialise API call
    youtube_api = build('youtube', 'v3', developerKey = api_key)

    #Make the search
    results = youtube_api.search().list(q=search_terms, part='snippet',
                                type='video', order='viewCount', maxResults=50,
                                publishedAfter=uploaded_since).execute()

    return results, youtube_api


def populate_dataframe(results, youtube_api, df, views_threshold):
    """Extracts relevant information and puts into dataframe"""
    # Loop over search results and add key information to dataframe
    i = 1
    for item in results['items']:
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
            df.loc[i] = [title, video_url, score, viewcount, channel_name,\
                                    num_subs, ratio, channel_url]
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
            title = video['Title']
            views = video['Views']
            subs = video['Num_subscribers']
            link = video['Video URL']
            print("Video #{}:\nThe video '{}' has {} views, from a channel \
with {} subscribers and can be viewed here: {}\n"\
                                        .format(i+1, title, views, subs, link))
            print("==========================\n")


## ======================================================================= ##
## ====== SERIES OF FUNCTIONS TO PARSE KEY INFORMATION ABOUT VIDEOS ====== ##
## ======================================================================= ##

def find_title(item):
    title = item['snippet']['title']
    return title

def find_video_url(item):
    video_id = item['id']['videoId']
    video_url = "https://www.youtube.com/watch?v=" + video_id
    return video_url

def find_viewcount(item, youtube):
    video_id = item['id']['videoId']
    video_statistics = youtube.videos().list(id=video_id,
                                        part='statistics').execute()
    viewcount = int(video_statistics['items'][0]['statistics']['viewCount'])
    return viewcount

def find_channel_id(item):
    channel_id = item['snippet']['channelId']
    return channel_id

def find_channel_url(item):
    channel_id = item['snippet']['channelId']
    channel_url = "https://www.youtube.com/channel/" + channel_id
    return channel_url

def find_channel_title(channel_id, youtube):
    channel_search = youtube.channels().list(id=channel_id,
                                            part='brandingSettings').execute()
    channel_name = channel_search['items'][0]\
                                    ['brandingSettings']['channel']['title']
    return channel_name

def find_num_subscribers(channel_id, youtube):
    subs_search = youtube.channels().list(id=channel_id,
                                            part='statistics').execute()
    if subs_search['items'][0]['statistics']['hiddenSubscriberCount']:
        num_subscribers = 1000000
    else:
        num_subscribers = int(subs_search['items'][0]\
                                    ['statistics']['subscriberCount'])
    return num_subscribers

def view_to_sub_ratio(viewcount, num_subscribers):
    if num_subscribers == 0:
        return 0
    else:
        ratio = viewcount / num_subscribers
        return ratio

def how_old(item):
    when_published = item['snippet']['publishedAt']
    when_published_datetime_object = datetime.strptime(when_published,
                                                        '%Y-%m-%dT%H:%M:%SZ')
    today_date = datetime.today()
    days_since_published = int((today_date - when_published_datetime_object).days)
    if days_since_published == 0:
        days_since_published = 1
    return days_since_published

def custom_score(viewcount, ratio, days_since_published):
    if ratio > 5:
        ratio = 5
    score = (viewcount * ratio) / days_since_published
    return score
