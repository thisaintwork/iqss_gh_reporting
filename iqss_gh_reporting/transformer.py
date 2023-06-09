from datetime import timedelta

# from argparse import ArgumentParser
# from dict2xml import dict2xml
# from argparse import ArgumentParser
from github import Github
# from gql import gql, Client
# from gql.transport.aiohttp import AIOHTTPTransport
# from json2xml import json2xml
from pathvalidate import sanitize_filename
from pathvalidate import sanitize_filepath
# from typing import Literal
# import argparse
# import asyncio
import datetime
# import json
import os
import pandas as pd
import re
import copy
from iqss_gh_reporting import pdata

def string_cleaned(to_be_cleaned: str=None):
    # ===================================================================================================================
    # This cleans up a string to remove characters that I do not want allowed in file names and directory names
    # There is an assumption that the stings will also be sanity checked using a library for filenames and directory names
    # ===================================================================================================================
    x = {
        ' ': '_',
        ',': '_',
        ';': '_',
        ':': '_',
        '-': '_',
        '@': '_',
        '!': '_',
        '$': '_',
        '%': '_',
        '^': '_',
        '&': '_',
        '*': '_',
        '(': '_',
        ')': '_',
        '=': '_',
        '-': '_',
        '\\': '_',
        '|': '_',
        '=': '_',
        '[': '_',
        ']': '_',
        '{': '_',
        '}': '_',
        '"': '_',
        "'": '_',
        "?": '_',
        ">": '_',
        "<": '_'
        }
    if to_be_cleaned is None:
        return None
    else:
        return to_be_cleaned.translate(str.maketrans(x))


class RequiredSprintColumnValues:
    # ===================================================================================================================
    # This defines a list of the sprint column values that we include as part of an active sprint.
    # Notes:
    # - for now this is a static class. I would really like this to be instead driven off a JSON file.
    # - This class would have the existing mapping in the file.
    # - It would dynamically add unrecognized values to the file
    # ===================================================================================================================

    NAMES = [
            "This Sprint 🏃‍♀️ 🏃",
            "IQSS Team - In Progress  💻",
            "Ready for Review ⏩",
            "In Review 🔎",
    ]

    @staticmethod
    def list():
        return RequiredSprintColumnValues.NAMES

    @staticmethod
    def print():
        print(f"values: {RequiredSprintColumnValues.NAMES}")


class AllSprintColumnValues:
    # ===================================================================================================================
    # This defines a list of the sprint column values that we include as part of an active sprint.
    # Notes:
    # - for now this is a static class. I would really like this to be instead driven off a JSON file.
    # - This class would have the existing mapping in the file.
    # - It would dynamically add unrecognized values to the file
    # ===================================================================================================================

    NAMES = [
            "▶ SPRINT READY",
            "This Sprint 🏃‍♀️ 🏃",
            "IQSS Team - In Progress  💻",
            "Ready for Review ⏩",
            "In Review 🔎",
            "Ready for QA ⏩",
            "QA ✅",
            "Done 🚀",

    ]

    @staticmethod
    def list():
        return AllSprintColumnValues.NAMES

    @staticmethod
    def print():
        print(f"values: {AllSprintColumnValues.NAMES}")


class RequiredDfColumnHeaderNames:
    # ===================================================================================================================
    # This is  a way (albeit clunky) to that the data gets consistent data headers.
    # Notes:
    # - for now this is a static class. I would really like this to be instead driven off a JSON file.
    # - This class would have the existing mapping in the file.
    # - It would dynamically add unrecognized values to the file
    # ===================================================================================================================

    # This dictionary should be edited to to be what is expected.
    # prolly in a real app this would be a config file.
    # These are required mappings
    NAMES = {
        "project": "Project",
        "column": "Column",
        "type": "Type",
        "number": "Number",
        "labels": "Labels",
        "repo": "Repo",
        "state": "State",
    }
    # These are additional mappings
    # we would like to standardize
    MAP = {
        "size": "Size",
        "card": "Title",
        "title": "Title",
        "cardurl": "CardURL",
        "repo": "Repo",
        "createdat": "CreatedAt",
        "updatedat": "UpdatedAt",
        "closedat": "ClosedAt",
        "closedby": "ClosedBy",
        "closes": "Closes",
    }






    @staticmethod
    def value(name: str = None):
        # return a names or MAP value
        if name in RequiredDfColumnHeaderNames.NAMES:
            return str(RequiredDfColumnHeaderNames.NAMES[name])
        if name in RequiredDfColumnHeaderNames.MAP:
            return str(RequiredDfColumnHeaderNames.MAP[name])
        # print(f"Note: {name} is not a standard column name.")
        return name

    @staticmethod
    def names():
        # col names
        return list(RequiredDfColumnHeaderNames.NAMES.keys())

    @staticmethod
    def values():
        # col values
        return list(RequiredDfColumnHeaderNames.NAMES.values())

    @staticmethod
    def print():
        print(f"Column names: {RequiredDfColumnHeaderNames.NAMES}")


def list_contains_at_least(required_list: list = None, submitted_list: list = None):
    # ===================================================================================================================
    # This takes a required list of strings and a submitted list of strings.
    # It checks to see if the submitted list contains at least the required list.
    #
    # It is used to check that the column names in a dataframe are what is expected.
    # It is used to check that the subset of sprint column values that we use to define what is active in a sprint
    #  are actually present in the sprint column data. e.g. The code compares teh contents of:
    #  RequiredSprintColumnValues with the unique list of values extracted from the sprint column data.
    # ===================================================================================================================
    print(f" required list entries: {required_list}")
    print(f" submitted list entries: {submitted_list}")

    if submitted_list is None:
        print("No entries were submitted.")
        return False
    if len(list(set(submitted_list))) != len(submitted_list):
        print("Duplicate column names found.")
        return False
    missing_names = [col for col in required_list if col not in list(set(submitted_list))]
    if missing_names:
        print(f"Missing entries: {missing_names}")
        return False
    else:
        print("All desired entries are present.")
        return True


class SprintSizeSummarizer:
    # ===================================================================================================================
    # This takes a dataframe containing raw information from a sprint that has been post-processed to include a
    # column called size.  It then summarizes the size of the cards in each column.
    #
    # The original dataframe is not modified.
    # A new datdaframe is created that contains a summary of the sprint data
    #
    # It will fail if:
    # - The dataframe does not contain the minimum required column headers of the correct names
    # - The column values do not include the required sprint state values
    # - There is no column called size
    #
    #  You can:
    #    - get the modified dataframe
    # ===================================================================================================================
    def __init__(self, sp_data: pdata = None):
        self._sprint_name = sp_data.sprint_name
        self._timestamp = sp_data.data_collected_time
        self._df = None
        self._df_summary = None
        self._row_values = []
        self._row_counts = []
        self._sprint_col_values = []
        if not isinstance(sp_data.df, pd.DataFrame):
            raise TypeError("df must be a Pandas DataFrame")
        self._df = sp_data.df.copy(deep=True)
        self._dest_dir = sp_data.dest_dir_name
        self._dest_file = sp_data.dest_file_name
        self._transform()

    def _summarize_size_column(self):
        for col_val in AllSprintColumnValues.list():

            # return the sum of all the values value in the size column for this column
            sumnum = 0 + self._df[self._df[RequiredDfColumnHeaderNames.value('column')] == col_val][
                RequiredDfColumnHeaderNames.value('size')].sum()

            itemcount = 0 + self._df[self._df[RequiredDfColumnHeaderNames.value('column')] == col_val][
                RequiredDfColumnHeaderNames.value('size')].count()
            # new_row = {
            #     RequiredDfColumnHeaderNames.value('column'): col_val,
            #     RequiredDfColumnHeaderNames.value('size'): sumnum,
            #     RequiredDfColumnHeaderNames.value('CardCount'): itemcount
            # }
            self._row_values.append(sumnum)
            self._row_counts.append(itemcount)
            # self._df_summary = pd.concat([self.df_summary, pd.DataFrame([new_row])], ignore_index=True)
            # print(f"{sumnum}\t{col_val}")
            # print(f"{self._row_values}")
            # print(f"{self._row_counts}")

    def _summarize_size_in_sprint_column_group(self):
        # now create a list of the columns we consider to be active sprint columns
        sumnum = 0
        itemcount = 0
        for name in RequiredSprintColumnValues.list():
            sumnum = sumnum + self._df[self._df[RequiredDfColumnHeaderNames.value('column')] == name][
                RequiredDfColumnHeaderNames.value('size')].sum()
            itemcount = itemcount + self._df[self._df[RequiredDfColumnHeaderNames.value('column')] == name][
                RequiredDfColumnHeaderNames.value('size')].count()
        # new_row = {
        #     RequiredDfColumnHeaderNames.value('column'): "ActiveSprint",
        #     RequiredDfColumnHeaderNames.value('size'): sumnum,
        #     RequiredDfColumnHeaderNames.value('CardCount'): itemcount
        # }
        self._row_values.append(sumnum)
        self._row_counts.append(itemcount)
        #self._df_summary = pd.concat([self.df_summary, pd.DataFrame([new_row])], ignore_index=True)
        # print(f"{sumnum}\tInTheSprint")
        # print(f"{self._row_values}")
        # print(f"{self._row_counts}")

    @property
    def type(self):
        return type(self).__name__

    @property
    def df_summary(self):
        return self._df_summary

    @property
    def df(self):
        return self._df

    def _transform(self):
        if not list_contains_at_least(RequiredDfColumnHeaderNames().values(), self._df.columns):
            raise ValueError("Failed data header name check")
        self._sprint_col_values = list(self._df[RequiredDfColumnHeaderNames.value('column')].unique())
        # See #19
        # if not list_contains_at_least(RequiredSprintColumnValues.list(), self._sprint_col_values):
        #     raise ValueError("Failed  sprint column value check")
        self._create_summary_dataframe()

    def write(self, postfix: str = ""):
        # ===================================================================================================================
        # This writes the contents of a dataframe to a tab delimited file.
        # ===================================================================================================================
        out_file = sanitize_filepath(self._dest_dir, platform="auto") \
                   + '/' + sanitize_filename(self._dest_file, platform="auto") \
                   + '-' \
                   + postfix \
                   + ".tsv"
        print(f"Saving result to file.")
        print(f" {out_file}")
        self._df_summary.to_csv(out_file, sep='\t', index=False)

    def _create_summary_dataframe(self):
        self._summarize_size_column()
        self._summarize_size_in_sprint_column_group()

        init_columns = ["DateTimeStamp", "SprintName"]
        init_columns.extend(AllSprintColumnValues.list())
        init_columns.append("SprintActiveCards")
        init_columns.extend([i + "_" for i in AllSprintColumnValues.list()])
        init_columns.append("SprintActiveCards_")

        new_row = [self._timestamp, self._sprint_name]
        new_row.extend(self._row_values)
        new_row.extend(self._row_counts)
        self._df_summary = pd.concat([self._df_summary, pd.DataFrame([new_row], columns=init_columns)], ignore_index=True)


class SprintCardSizer:
    # ===================================================================================================================
    # This takes a dataframe containing raw information from a sprint
    # It changes the dataframe in the following ways:
    # - If no column called size exists, it creates one and extracts the size from the labels.
    # It will fail if:
    # - The dataframe does not contain the minimum required column headers of the correct names
    #  You can:
    #    - get the modified dataframe
    # ===================================================================================================================
    def __init__(self, sp_data: pdata = None):
        self._sprint_col_values = []
        if not isinstance(sp_data.df, pd.DataFrame):
            raise TypeError("df must be a Pandas DataFrame")
        self._df = sp_data.df.copy()
        self._transform()
        return

    def print_issues(self):
        print(self._df.to_string(index=False))

    def _clean_labels(self):
        # Make sure there is at least an empty string in the labels column
        for index, row in self._df.iterrows():
            # if not isinstance(row[RequiredDfColumnHeaderNames.value('labels')], str):
            if len(str(row[RequiredDfColumnHeaderNames.value('labels')])) == 0:
                self._df.at[index, RequiredDfColumnHeaderNames.value('labels')] = "NO_LABELS"

    def _add_size_column(self):
        # ----------------------------------------------------------------------------------------------------------
        # This function adds a column to the dataframe to store the size as extracted from the "Size: X"
        # It is careful to use the predefined column name for the size column.
        # It will delete any existing column called size and replace it.
        # ----------------------------------------------------------------------------------------------------------
        if RequiredDfColumnHeaderNames.value('size') in self._df.Column:
            self._df = self._df.drop(RequiredDfColumnHeaderNames.value('size'), axis=1)
        self._df[RequiredDfColumnHeaderNames.value('size')] = 0

        for index, row in self._df.iterrows():
            size_num = 0
            label_list = str(row[RequiredDfColumnHeaderNames.value('labels')]).split(',')
            lower_list = [label.lower() for label in label_list]
            size_label = [label.strip() for label in lower_list if 'size:' in label]
            if len(size_label) > 0:
                size_label_str = ' '.join(size_label)
                search_result = re.search(r'[0-9]+', size_label_str)
                if search_result is not None:
                    search_result = re.search(r'[0-9]+', size_label_str).group()
                    size_num = int(search_result)
                self._df.at[index, RequiredDfColumnHeaderNames.value('size')] = size_num
                # print(f" num:{row[RequiredDfColumnHeaderNames.value('number')]} state:{row[RequiredDfColumnHeaderNames.value('column')]} \
                #    s:{size_num}  labels:{row[RequiredDfColumnHeaderNames.value('labels')]}")

    @property
    def type(self):
        return type(self).__name__

    @property
    def df(self):
        return self._df

    def _transform(self):
        # This class is only usable with the data from a sprint
        # Come back later and add a way to validate the data type

        if not list_contains_at_least(RequiredDfColumnHeaderNames().values(), self._df.columns):
            raise ValueError(f"{self.__class__.__name__} Failed data header name check")

        self._sprint_col_values = list(self._df[RequiredDfColumnHeaderNames.value('column')].unique())
        # See #19
        #if not list_contains_at_least(RequiredSprintColumnValues.list(), self._sprint_col_values):
        #    raise ValueError("Failed  sprint column value check")

        # missing an else statement that exits here
        # create the output dataframe
        self._clean_labels()
        self._add_size_column()

