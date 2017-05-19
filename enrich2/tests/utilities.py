#  Copyright 2016-2017 Alan F Rubin, Daniel Esposito
#
#  This file is part of Enrich2.
#
#  Enrich2 is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Enrich2 is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Enrich2.  If not, see <http://www.gnu.org/licenses/>.

import os
import json
import pandas as pd


TOP_LEVEL = os.path.dirname(__file__)


DEFAULT_STORE_PARAMS = {
    'force_recalculate': False,
    'component_outliers': False,
    'tsv_requested': False,
    'output_dir_override': False,
}


def create_file_path(fname, direc='data/result/'):
    """
    Utility function to create an absolute path to data in the tests directory.
    
    Parameters
    ----------
    fname : str
        The name of the file.
    direc : str
        The directory of the file in tests directory.

    Returns
    -------
    str
        Absolute file path.

    """
    path = os.path.join(TOP_LEVEL, direc, fname)
    return path


def load_config_data(fname, direc='data/config/'):
    """
    Utility function to load a configuration file.
    
    Parameters
    ----------
    fname : str
        Name of file in the directory `direc`.
    direc : str (optional)
        Directory where the file is relative to :py:module: `~..tests`.

    Returns
    -------
        dict
            Dictionary containing the loaded key-value pairs.

    """
    path = create_file_path(fname, direc)
    try:
        with open(path, "rt") as fp:
            return json.load(fp)
    except (IOError, ValueError):
        raise IOError("Failed to open '{}".format(path))


def load_df_from_txt(fname, direc='data/result/', sep='\t'):
    """
    Utility function to load a table stored as txt with an arbitrary separator.
    
    Parameters
    ----------
    fname : str
        Name of file in the directory `direc`.
    direc : str
        Directory where the file is relative to :py:module: `~..tests`.
    sep : str
        Delimiter to use between columns.
        
    Returns
    -------
        pd.DataFrame
            A Pandas DataFrame object parsed from the file.
    """
    path = create_file_path(fname, direc)
    try:
        return pd.DataFrame.from_csv(path, sep=sep)
    except IOError:
        raise IOError("Failed to open '{}".format(path))


def load_df_from_pkl(fname, direc='data/result/'):
    """
    Utility function to load a table stored in py:module: `pickle` format.
    
    Parameters
    ----------
    fname : str
        Name of file in the directory `direc`.
    direc : str
        Directory where the file is relative to :py:module: `~..tests`.

    Returns
    -------
        pd.DataFrame
            A Pandas DataFrame object parsed from the file.
    """
    path = create_file_path(fname, direc)
    try:
        return pd.read_pickle(path)
    except IOError:
        raise IOError("Failed to open '{}".format(path))


def save_result_to_txt(test_obj, direc, prefix, sep='\t'):
    """
    Utility function to save a :py:class: `pd.HDFStore` as a series of 
    delimited tsv. One file is created for each :py:class: `pd.DataFrame` in
    the store.
    
    Parameters
    ----------
    test_obj : pd.HDFStore
        HDFStore object to save to delimited text files.
    direc : str
        Directory to save the file.
    prefix : str
        Prefix to add to each key in the store to use as a filename,
    sep : str
        Delimiter to use between columns.

    Returns
    -------
    None
        This function does not return anything.

    """
    for key in test_obj.store:
        name = "{}/{}_{}.tsv".format(
            direc,
            prefix,
            key[1:].replace("/", "_")
        )
        path = create_file_path(name, direc="")
        print("saving {} to {}".format(key, path))
        test_obj.store[key].to_csv(path, sep=sep, index=True)
    return


def save_result_to_pkl(test_obj, direc, prefix):
    """
    Utility function to save a :py:class: `pd.HDFStore` as a series of 
    pickle files. One file is created for each :py:class: `pd.DataFrame` in
    the store. Each file has the extension 'pkl'.

    Parameters
    ----------
    test_obj : pd.HDFStore
        HDFStore object to save to pickle files.
    direc : str
        Directory to save the file.
    prefix : str
        Prefix to add to each key in the store to use as a filename,

    Returns
    -------
    None
        This function does not return anything.

    """
    for key in test_obj.store:
        name = "{}/{}_{}.pkl".format(
            direc,
            prefix,
            key[1:].replace("/", "_")
        )
        path = create_file_path(name, direc="")
        print("saving {} to {}".format(key, path))
        test_obj.store[key].to_pickle(path)
    return


def dispatch_loader(fname, direc, sep='\t'):
    """
    Utility function to load a filename based on the extension it has.
    
    Parameters
    ----------
    fname : str
        Filename with extension in {'pkl', 'tsv', 'txt'}
    direc : str
        Directory to save the file.
    sep : str
        Delimiter to use between columns.

    Returns
    -------
    pd.DataFrame
        DataFrame parsed from the file.
    """
    ext = fname.split('.')[-1]
    if ext in ('tsv' or 'txt'):
        return load_df_from_txt(fname, direc, sep)
    elif ext == 'pkl':
        return load_df_from_pkl(fname, direc)
    else:
        raise IOError("Unexpected file extension {}.".format(ext))


def print_test_comparison(test_name, expected, result):
    """
    Utility function to nicely format the a test comparison as a string.
    
    Parameters
    ----------
    test_name : str
        Name of the test.
    expected : Any
        Expected test result that can be represented as text
    result : Any
        Expected test result that can be represented as text

    Returns
    -------
    str
        String object represeting a test.
    """
    line = '\n'
    line += "-" * 60 + '\n'
    line += "{}\n".format(test_name)
    line += "-" * 60 + '\n'
    line += "-" * 26 + "EXPECTED" + "-" * 26 + '\n'
    line += "{}\n".format(expected)
    line += "-" * 28 + "END" + "-" * 29 + '\n'
    line += "-" * 27 + "RESULT" + "-" * 27 + '\n'
    line += "{}\n".format(result)
    line += "-" * 28 + "END" + "-" * 29 + '\n'
    line += '\n'
    return line


def update_cfg_file(cfg, scoring, logr):
    """
    Utility function that takes a configuration dictionary and updates the
    scorer fields.
    
    Parameters
    ----------
    cfg : dict
        Dictionary that can initialize a 
        :py:class: `~..enrich2.base.store.StoreManager` object.
    scoring : {'WLS', 'OLS', 'counts', 'ratios', 'simple'}
        Choice of scoring option in {'WLS', 'OLS', 'counts', 'ratios', 'simple'}
    logr : {'complete', 'full', 'wt'}
        Choice of scoring normalization method in {'complete', 'full', 'wt'}

    Returns
    -------
    dict
        Modified dictionary (in-place)

    """
    cfg["scorer"]["scorer_path"] = SCORING_PATHS.get(scoring)
    cfg["scorer"]["scorer_options"] = SCORING_ATTRS.get(scoring).get(logr)
    return cfg


SCORING_PATHS = {
    'counts': create_file_path('counts_scorer.py', 'data/plugins'),
    'ratios': create_file_path('ratios_scorer.py', 'data/plugins'),
    'simple': create_file_path('simple_scorer.py', 'data/plugins'),
    'WLS': create_file_path('regression_scorer.py', 'data/plugins'),
    'OLS': create_file_path('regression_scorer.py', 'data/plugins')
}


SCORING_ATTRS = {
    'WLS': {
        'full': {'logr_method': 'full', 'weighted': True},
        'complete': {'logr_method': 'complete', 'weighted': True},
        'wt': {'logr_method': 'wt', 'weighted': True}
    },
    'OLS': {
        'full': {'logr_method': 'full', 'weighted': False},
        'complete': {'logr_method': 'complete', 'weighted': False},
        'wt': {'logr_method': 'wt', 'weighted': False}
    },
    'ratios': {
        'full': {'logr_method': 'full'},
        'complete': {'logr_method': 'complete'},
        'wt': {'logr_method': 'wt'}
    },
    'counts': {
        'full': {},
        'complete': {},
        'wt': {}
    },
    'simple': {
        'full': {},
        'complete': {},
        'wt': {}
    }
}

