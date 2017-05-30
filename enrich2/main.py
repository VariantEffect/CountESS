#!/usr/bin/env python
#
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


import json
import logging
import os.path
import sys
from tkinter import Toplevel
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from .base.constants import SCORING_METHODS, LOGR_METHODS
from .experiment.experiment import Experiment
from .experiment.condition import Condition
from .selection.selection import Selection
from .config import config_check
from .gui.configurator import Configurator
from .libraries.barcode import BarcodeSeqLib
from .libraries.barcodeid import BcidSeqLib
from .libraries.barcodevariant import BcvSeqLib
from .libraries.basic import BasicSeqLib
from .libraries.idonly import IdOnlySeqLib
from .gui.logging_frame import WindowLoggingHandler


__author__ = "Alan F Rubin, Daniel C Esposito"
__copyright__ = "Copyright 2016-2017, Alan F Rubin, Daniel C Esposito"
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "Alan F Rubin"
__email__ = "alan.rubin@wehi.edu.au"


globals()['Selection'] = Selection
globals()['Condition'] = Condition
globals()['Experiment'] = Experiment
globals()['BarcodeSeqLib'] = BarcodeSeqLib
globals()['BcidSeqLib'] = BcidSeqLib
globals()['BcvSeqLib'] = BcvSeqLib
globals()['BasicSeqLib'] = BasicSeqLib
globals()['IdOnlySeqLib'] = IdOnlySeqLib


#: Name of the driver script. Used for logging output.
DRIVER_NAME = os.path.basename(sys.argv[0])


#: Format string for log entries (console or file).
LOG_FORMAT = "%(asctime)-15s [%(oname)s] %(message)s"


def start_logging(log_file, log_level):
    """
    Begin logging. This function should be called by the driver at the start 
    of program execution. 
    Message format is defined by :py:const:`LOG_FORMAT`.

    Args:
        log_file (str, None): Name of the log output file, or 
        ``None`` to output to console.

        log_level: Requested logging level. 
            See :py:class:`~logging.Logger` for a detailed 
            description of the options. Most program 
            status messages are output at the ``INFO`` level.

    """
    if log_file is not None:
        logging.basicConfig(
            filename=log_file, level=log_level, format=LOG_FORMAT)
    else:
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(LOG_FORMAT)
        stream_handler.setFormatter(formatter)
        logging.basicConfig(
            level=log_level, format=LOG_FORMAT, handlers=[stream_handler])


def main_gui():
    """
    Entry point for GUI.

    """
    start_logging(None, logging.DEBUG)
    app = Configurator()

    # GUI logger to the logger's handlers
    win = Toplevel(master=app)
    win.title('Enrich 2 Log')
    log_window = WindowLoggingHandler(window=win)
    formatter = logging.Formatter(LOG_FORMAT)
    log_window.setFormatter(formatter)
    logging.getLogger().addHandler(log_window)
    logging.info("Starting Enrich 2...", extra={'oname': DRIVER_NAME})

    app.mainloop()


def main_cmd():
    """
    Entry point for command line.

    """
    # build description string based on available methods
    desc_string = "Command-line driver for Enrich2 v{}".format(__version__) + \
        "\n\nscoring methods:\n" + \
        "\n".join(["  {:22}{}".format(k, v) for k, v in
                   SCORING_METHODS.items()]) + \
        "\n\nlog ratio methods:\n" + \
        "\n".join(["  {:22}{}".format(k, v) for k, v in
                   LOGR_METHODS.items()])

    # create parser and add description
    parser = ArgumentParser(prog="Enrich2", description=desc_string,
                            formatter_class=RawDescriptionHelpFormatter)

    # add command line arguments
    parser.add_argument("config", help="JSON configuration file")

    # parser.add_argument("scoring_method", help="scoring method",
    #                     choices=list(SCORING_METHODS.keys()))
    # parser.add_argument("logr_method", help="log ratio method",
    #                     choices=list(LOGR_METHODS.keys()))

    # add support for semantic version checking
    parser.add_argument("--version", action="version",
                        version="%(prog)s {}".format(__version__))

    # add analysis options
    parser.add_argument("--log", metavar="FILE", dest="log_file",
                        help="path to log file")
    parser.add_argument("--no-tsv", dest="tsv_requested",
                        action="store_false", default=True,
                        help="don't generate tsv files")
    parser.add_argument("--recalculate", dest="force_recalculate",
                        action="store_true", default=False,
                        help="force recalculation")
    parser.add_argument("--component-outliers", dest="component_outliers",
                        action="store_true", default=False,
                        help="calculate component outlier stats")
    parser.add_argument("--output-dir", metavar="DIR",
                        dest="output_dir_override",
                        help="override the config file's output directory")
    args = parser.parse_args()

    # start the logs
    start_logging(args.log_file, logging.DEBUG)

    # read the JSON file
    try:
        cfg = json.load(open(args.config, "U"))
    except IOError:
        raise IOError("Failed to open '{}' [{}]".format(
            args.config, DRIVER_NAME))
    except ValueError:
        raise ValueError("Improperly formatted .json file [{}]".format(
            DRIVER_NAME))

    # identify config file type and create the object
    if config_check.is_experiment(cfg):
        logging.info("Detected an Experiment config file",
                     extra={'oname': DRIVER_NAME})
        obj = Experiment()
    elif config_check.is_selection(cfg):
        logging.info("Detected a Selection config file",
                     extra={'oname': DRIVER_NAME})
        obj = Selection()
    elif config_check.is_seqlib(cfg):
        seqlib_type = config_check.seqlib_type(cfg)
        logging.info("Detected a %s config file", seqlib_type,
                     extra={'oname': DRIVER_NAME})
        if seqlib_type == "BarcodeSeqLib":
            obj = BarcodeSeqLib()
        elif seqlib_type == "BcidSeqLib":
            obj = BcidSeqLib()
        elif seqlib_type == "BcvSeqLib":
            obj = BcvSeqLib()
        elif seqlib_type == "BasicSeqLib":
            obj = BasicSeqLib()
        elif seqlib_type == "IdOnlySeqLib":
            obj = IdOnlySeqLib()
        else:
            raise ValueError("Unrecognized SeqLib type '{}' [{}]".format(
                seqlib_type, DRIVER_NAME))
    else:
        raise ValueError("Unrecognized .json config [{}]".format(DRIVER_NAME))

    # set analysis options
    obj.force_recalculate = args.force_recalculate
    obj.component_outliers = args.component_outliers
    # obj.scoring_method = args.scoring_method
    # obj.logr_method = args.logr_method
    obj.tsv_requested = args.tsv_requested

    if args.output_dir_override is not None:
        obj.output_dir_override = True
        obj.output_dir = args.output_dir_override
    else:
        obj.output_dir_override = False

    # make sure objects are valid
    try:
        # configure the object
        from .config.types import SelectionConfiguration
        # If Selection is root, require that scorer parameters be present
        if isinstance(obj, Selection):
            cfg = SelectionConfiguration(cfg, has_scorer=True)
        obj.configure(cfg)
        obj.validate()
    except Exception:
        print("Program finished running but with errors. See log for details.")
        logging.exception("Invalid configuration",
                          extra={'oname': DRIVER_NAME})
    else:
        # open HDF5 files for the object and all child objects
        obj.store_open(children=True)

        # perform the analysis
        try:
            obj.calculate()
        except Exception as e:
            print("Program finished running but with errors. "
                  "See log for details.")
            logging.exception(e, extra={'oname': DRIVER_NAME})
            obj.store_close(children=True)
            sys.exit(0)

        try:
            obj.write_tsv()
        except Exception:
            print("Program finished running but with errors. "
                  "See log for details.")
            logging.exception(
                "Calculations completed, but TSV ouput failed.",
                extra={'oname': DRIVER_NAME}
            )
            obj.store_close(children=True)
            sys.exit(0)

        # clean up
        obj.store_close(children=True)
        print("Program finished successfully! See log for information.")
        logging.info("Done!", extra={'oname': DRIVER_NAME})


if __name__ == "__main__":
    gui_mode = False

    try:
        if sys.argv[1] == "gui":
            gui_mode = True
    except IndexError:
        pass

    if gui_mode:
        main_gui()
    else:
        main_cmd()
