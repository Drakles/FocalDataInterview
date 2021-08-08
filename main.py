import numpy as np
import pandas as pd
from datetime import date
import re

import os


def normalise_empty_values(df):
    # The data science pipeline expects that NULL values are coded in a
    # consistent fashion. Transform all missing values such that they are
    # consistent with one another
    df = df.replace(r'^\s*$', np.NaN, regex=True)

    if not df[df.columns[1:]].all().any():
        raise ValueError('Dataframe still contains empty string values')

    return df


def unique_rows(df):
    # De-duplicate the data such that every row is unique.
    ids = ['survey_id', 'respondent_id']
    # drop rows with empty survey id or resdpondent id
    df.dropna(subset=ids, inplace=True)
    # drop duplicates
    df.drop_duplicates(subset=ids, keep='last', inplace=True)

    # add new ID column based on survey and respondent id
    df.insert(loc=0, column='ID', value=df.survey_id.astype(str).str.cat(
        df.respondent_id.astype(str)))

    if not df.ID.is_unique:
        raise ValueError('IDs are not unique')

    return df


def drop_all_empty_columns(df):
    # drop completely empty columns as they are irrelevant
    df = df.dropna(axis=1, how='all')

    if df.isna().all().any():
        raise ValueError('some columns has all nan values')

    return df


def rename_columns(df):
    # rename columns to shorter form. All columns are explained in
    # columns_explained.txt file
    df.columns = list(df.columns[:6]) + \
                 ['Q' + str(i) for i in range(df.shape[1] - 6)]
    return df


def convert_year_birt_to_age(df):
    # Convert the year of birth column into an “age” column
    # (i.e. year_of_birth: 1990 => age: 30)
    df.insert(loc=4, column='age',
              value=date.today().year - pd.to_datetime(df.Q63, format='%Y',
                                                       errors='ignore').dt.year)
    if df[(df.age < 0) | (df.age > 125)].age.any():
        raise ValueError('age of some respondents is below 0 or over 125 years')

    return df


def convert_postcodes(df, lookup_table_path):
    # Using the lookup table (postcode_lookup.csv) convert the postcode
    # column into a Westminster Constituency Code
    postcodes = pd.read_csv(lookup_table_path).set_index('postcode') \
        ['westminster_constituency'].to_dict()
    df.insert(loc=5,
              column='postcode',
              value=df.Q4.apply(
                  lambda postcode: postcodes.get(postcode, np.nan)))

    return df


def reformat_follow_ups(df):
    # You will see that certain questions are follow-ups, and only get asked
    # according to the response to the previous question (“If you answered
    # yes, to the previous question - would you ever ...?”). In these cases
    # please combine the two such that the “no” response (in this case)
    # appears in the follow-up question, rather than the follow-up column
    # containing missing values for those people to whom the question was not
    # presented.
    df.loc[df.Q6.str.contains('No', flags=re.IGNORECASE, regex=True, na=False),
           ['Q7']] = 'no'

    if df[df.Q6.str.contains('No', flags=re.IGNORECASE, regex=True,
                             na=False) & df.Q7.isna()].Q7.any(skipna=False):
        raise ValueError('some follow up questions still contain nan values')

    return df


def max_range(val):
    # retrieve max value from column with values as range or scalar
    if isinstance(val, str):
        # if val is in range format i.e 10-20
        if '-' in val:
            return int(val.split('-')[1])
        return int(val)

    return val


def append_bad_responded_flag(df):
    # In adding a “is_bad_respondent” flag to a row of the survey we are
    # stating that this respondent’s responses cannot be relied upon as
    # credible
    flag = 'is_bad_respondent'
    df[flag] = False

    # Suspiciously fast response times
    df.start_time = pd.to_datetime(df.start_time)
    df.end_time = pd.to_datetime(df.end_time)

    # assuming spending on average less than 3 seconds per question is
    # suspicious
    time_threshold = 3 * len(df.columns.values[7:])
    df.loc[(df.end_time - df.start_time).dt.seconds < time_threshold, [flag]] \
        = True

    # Inconsistency of responses
    # responder who voted in EU Referendum in 2016 being younger than 18 at
    # that time
    df.loc[df.Q5.str.startswith('I voted', na=False) & (df.age < 23), [flag]] \
        = True

    # responder who voted in general elections in 2019 being younger than 18 at
    # that time
    df.loc[df.Q6.str.startswith('Yes', na=False) & (df.age < 20), [flag]] = True

    # responder who claimed to vote in general elections in 2019 but stated
    # # she/he didn't vote in the follow up questions
    df.loc[df.Q6.str.startswith('Yes', na=False) &
           (df.Q7.str.startswith('I didn\'t', na=False)), [flag]] = True

    # responder to claim to disapprove the government but has warm attitude
    # towards the ruling party
    df.loc[df.Q10.str.contains('disapprove', na=False) &
           (df.Q11.apply(max_range) > 80), [flag]] = True

    # responder to claim to approve the government but has cold attitude
    # towards the ruling party
    df.loc[df.Q10.str.contains(' approve', na=False, regex=True) &
           (df.Q11.apply(max_range) < 20), [flag]] = True

    return df


if __name__ == '__main__':
    df_raw = pd.read_csv('./data/raw_survey.csv')
    df = normalise_empty_values(df_raw)
    df = unique_rows(df)
    df = drop_all_empty_columns(df)
    df = rename_columns(df)
    df = convert_year_birt_to_age(df)
    df = convert_postcodes(df, './data/postcode_lookup.csv')
    df = reformat_follow_ups(df)
    df = append_bad_responded_flag(df)

    df.to_csv('./data/output/final_output.csv')
