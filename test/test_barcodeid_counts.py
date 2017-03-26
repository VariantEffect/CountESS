#  Copyright 2016-2017 Alan F Rubin
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
import unittest
import pandas as pd
import numpy as np
import os.path


from enrich2.libraries.barcode import BarcodeSeqLib


def suite():
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestBarcodeSeqLibCounts
    )
    return suite


class TestBarcodeSeqLibCounts(unittest.TestCase):

    @classmethod
    def fileIO(cls):
        cfg_file = os.path.join(
            os.path.dirname(__file__),
            "data", "config", "multi_barcode.json"
        )
        print(cfg_file)
        try:
            with open(cfg_file, "rt") as fp:
                return json.load(fp)
        except IOError:
            raise IOError("Failed to open '{}' "
                          "[{}]".format(cfg_file, __file__))
        except ValueError:
            raise ValueError("Improperly formatted .json file "
                             "[{}]".format(__file__))


    @classmethod
    def setUpClass(cls):
        cls._cfg = cls.fileIO()
        cls._obj = BarcodeSeqLib()

        # set analysis options
        cls._obj.force_recalculate = False
        cls._obj.component_outliers = False
        cls._obj.scoring_method = 'counts'
        cls._obj.logr_method = 'wt'
        cls._obj.plots_requested = False
        cls._obj.tsv_requested = False
        cls._obj.output_dir_override = False

        # perform the analysis
        cls._obj.configure(cls._cfg)
        cls._obj.validate()
        cls._obj.store_open(children=True)
        cls._obj.calculate()

    @classmethod
    def tearDownClass(cls):
        cls._obj.store_close(children=True)
        os.remove(cls._obj.store_path)
        os.rmdir(cls._obj.output_dir)

    def test_multi_barcode_counts(self):
        path = os.path.join(os.path.dirname(__file__),
                            "data", "result", "multi_barcode_count.tsv")
        # order in h5 matters
        result = pd.DataFrame.from_csv(path, sep='\t').astype(np.int32)
        self.assertTrue(self._obj.store['/raw/barcodes/counts'].equals(result))

    def test_multi_barcode_counts_unsorted(self):
        path = os.path.join(os.path.dirname(__file__),
                            "data", "result", "multi_barcode_count.tsv")
        # order in h5 doesn't matter
        result = pd.DataFrame.from_csv(path, sep='\t').astype(np.int32)
        store = self._obj.store['/raw/barcodes/counts'].sort_index()
        self.assertTrue(store.equals(result.sort_index()))

    def test_filter_stats(self):
        result = pd.DataFrame(
            [0], index=['total'], columns=['count']
        ).astype(int)
        self.assertTrue(self._obj.store['/raw/filter'].equals(result))

if __name__ == "__main__":
    unittest.main()
