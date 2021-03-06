"""
Enrich2 sequence fqread module
==============================
This module contains the ``FQRead`` class for representing a read in FASTQ
format. Additionally, this module contains utility functions for parsing and 
handling FASTQ files.
"""


from sys import stderr
import os.path
import re
import itertools
import bz2
import gzip
from array import array


__all__ = [
    "header_pattern",
    "BUFFER_SIZE",
    "dna_trans",
    "FQRead",
    "split_fastq_path",
    "create_compressed_outfile",
    "read_fastq",
    "read_fastq_multi",
    "fastq_filter_chastity",
]


# The following regex is referenced by line number in the class documentation.
# Matches FASTQ headers based on the following pattern (modify as needed):
# @<MachineName>:<Lane>:<Tile>:<X>:<Y>:<Chastity>#<IndexRead>/<ReadNumber>
header_pattern = re.compile(
    "@(?P<MachineName>.+)"
    ":(?P<Lane>\d+)"
    ":(?P<Tile>\d+)"
    ":(?P<X>\d+)"
    ":(?P<Y>\d+)"
    ":(?P<Chastity>[01])"
    "#(?P<IndexRead>\d)"
    "/(?P<ReadNumber>\d)"
)


# empirically optimized for reading FASTQ files
BUFFER_SIZE = 100000


# Helper translator for dna complimenting
dna_trans = str.maketrans("actgACTG", "tgacTGAC")


class FQRead(object):
    """
    Stores a single record from a FASTQ_ file. Quality values are stored 
    internally as a list of integer `Phred quality scores \
    <http://www.phrap.com/phred/#qualityscores>`_. The *qbase* parameter is 
    the ASCII value that correponds to Phred score of 0. The *sequence* and 
    *quality* strings must be the same length. 
    
    Parameters
    ----------
    header : `str`
        The header line of a FQ read.
    sequence : `str`
        The line containing the actual sequence characters.
    header2 : `str`
        Header line relating to the quality line ``quality``
    quality : `str`
        The ascii quality characters of ``sequence``.
    qbase : `int`
        Integer ASCII value that correponds to Phred score of 0
    
    Attributes
    ----------
    header : `str`
        The header line of a FQ read.
    sequence : `str`
        The line containing the actual sequence characters.
    header2 : `str`
        Header line relating to the quality line ``quality``
    quality : `list`
        List of Phred integers corresponding to each base.
    qbase : `int`
        Integer ASCII value that correponds to Phred score of 0
    
    Methods
    -------
    trim
        Trims a read from a specified ``start`` and ``end`` position
    trim_length
        Trims a read to contain a specified number bases starting from
        a specified position.
    revcomp
        Performs reverse complement on the read and quality sequences
    header_information
        Parses the first FASTQ_ header (@ header) and returns a dictionary
        of matches corresponding to a supplied regex pattern.
    min_quality
        Returns the minimum quality of the sequence bases.
    mean_quality
        Returns the mean quality of the sequence bases.
    is_chaste
        Returns ``True`` if the chastity bit is set in the header
    
    
    """

    # use slots for memory efficiency
    __slots__ = ("header", "sequence", "header2", "quality", "qbase")

    def __init__(self, header, sequence, header2, quality, qbase=33):
        lst = [header, sequence, header2, quality]

        # print(header, len(header))
        # print(sequence, len(sequence))
        # print(header2, len(header2))
        # print(quality, len(quality))

        if not all(isinstance(x, str) for x in lst):
            raise ValueError(
                "Bad file contents. Expeceted str got type " "{}".format(type(lst[-1]))
            )
        if not all(len(x) for x in lst):
            raise ValueError("Missing fields in FASTQ record")
        if len(sequence) != len(quality):
            raise ValueError("Different lengths for sequence and quality")
        if header[0] != "@" or header2[0] != "+":
            raise ValueError("Improperly formatted FASTQ record")

        self.header = header
        self.sequence = sequence
        self.header2 = header2
        # quality is a list of integers
        self.quality = [x - qbase for x in array("b", quality.encode("ascii")).tolist()]
        self.qbase = qbase

    def __str__(self):
        """
        Reformat as a four-line FASTQ_ record. This method converts the 
        integer quality values back into a string.
        """
        quality = array("b", [x + self.qbase for x in self.quality]).tobytes()
        quality = quality.decode("ascii")
        return "\n".join([self.header, self.sequence, self.header2, quality])

    def __len__(self):
        """
        Object length is the length of the sequence.
        """
        return len(self.sequence)

    def trim(self, start=1, end=None):
        """
        Trims this :py:class:`~FQRead` to contain bases between 
        *start* and *end* (inclusive). Bases are numbered starting at 1.
        
        Parameters
        ----------
        start : `int`, default: 1
            Position to start read trimming.
        end : `int`, default: None
            Position to end read trimming.
        """
        self.sequence = self.sequence[start - 1 : end]
        self.quality = self.quality[start - 1 : end]

    def trim_length(self, length, start=1):
        """
        Trims this :py:class:`~FQRead` to contain *length* bases, 
        beginning with *start*. Bases are numbered starting at 1.
        
        Parameters
        ----------
        length : `int`
            Number of bases to keep
        start : `int`, default: 1
            Position to start trimming at.
        """
        self.trim(start=start, end=start + length - 1)

    def revcomp(self):
        """
        Reverse-complement the sequence in place. Also reverses the array of 
        quality values.
        """
        self.sequence = self.sequence.translate(dna_trans)[::-1]
        self.quality = self.quality[::-1]

    def header_information(self, pattern=header_pattern):
        """
        Parses the first FASTQ_ header (@ header) and returns a dictionary. 
        Dictionary keys are the named groups in the regular expression 
        *pattern*. Unnamed matches are ignored. Integer values are converted 
        from strings to integers.

        The default pattern matches a header in the format::

            @<MachineName>:<Lane>:<Tile>:<X>:<Y>:<Chastity>#<IndexRead>/<ReadNumber>
        
        Parameters
        ----------
        pattern : `__Regex`, optional
            Regular expression pattern to parse the header with.
            
        Returns
        -------
        `dict`
        """
        match = pattern.match(self.header)
        if match is None:
            return None
        else:
            header_dict = match.groupdict()
            for key in header_dict:
                if header_dict[key].isdigit():
                    header_dict[key] = int(header_dict[key])
            return header_dict

    def min_quality(self):
        """
        Return the minimum Phred-like quality score.
        
        Returns
        -------
        `int`
        """
        return min(self.quality)

    def mean_quality(self):
        """
        Return the average Phred-like quality score.
        
        Returns
        -------
        `int`
        """
        return float(sum(self.quality)) / len(self)

    def is_chaste(self, raises=True):
        """
        Returns ``True`` if the chastity bit is set in the header. The 
        regular experession used by :py:meth:`header_information` must  
        include a ``'Chastity'`` match that equals ``1`` if the read is 
        chaste.

        If ``raises`` is ``True``, raises an informative error if the 
        chastity information in the header is not found. Otherwise, a 
        read without chastity information is treated as unchaste.
        
        Parameters
        ----------
        raises : `bool`
            If ``raises`` is ``True``, raises an informative error if the 
            chastity information in the header is not found. Otherwise, a 
            read without chastity information is treated as unchaste.
        
        Returns
        -------
        `bool`
        """
        try:
            if self.header_information()["Chastity"] == 1:
                return True
            else:
                return False
        except KeyError:  # no 'Chastity' in pattern
            if raises:
                raise KeyError("No chastity bit in FASTQ header pattern")
            else:
                return False
        except TypeError:  # no header match (unexpected format)
            if raises:
                raise ValueError("Unexpected FASTQ header format")
            else:
                return False


def split_fastq_path(fname):
    """
    Check that *fname* exists and has a valid FASTQ_ file extension. Valid 
    file extensions are ``.fastq`` or ``.fq``, optionally followed by ``.gz`` 
    or ``.bz2`` if the file is compressed. 

    Returns a tuple containing the directory, the file base name with no 
    extension, the FASTQ_ file extension used, and the compression format 
    (``"gz"``, ``"bz2"``, or ``None``).

    Raises an ``IOError`` if the file doesn't exist. Returns ``None`` if the 
    file extension is not recognized.
    
    Parameters
    ----------
    fname : `str`
        Path to the fastq file.
    
    Returns
    -------
    `tuple`
        Filename split into ``head``, ``base``, ``extension``, 
        ``compression extension``
    """
    if os.path.isfile(fname):
        compression = None
        head, tail = os.path.split(fname)
        base, ext = os.path.splitext(tail)
        if ext.lower() == ".bz2":
            compression = "bz2"
            base, ext = os.path.splitext(base)
        elif ext.lower() == ".gz":
            compression = "gz"
            base, ext = os.path.splitext(base)
        if ext.lower() in (".fq", ".fastq"):
            return head, base, ext, compression
        else:
            print(
                "Warning: unexpected file extension for '{fname}'".format(fname=fname),
                file=stderr,
            )
            return None
    else:
        raise IOError("file '{fname}' doesn't exist".format(fname=fname))


def create_compressed_outfile(fname, compression):
    """
    Utility function for opening compressed output files. Accepted values for 
    *compression* are ``"gz"``, ``"bz2"``, or ``None``. Returns a file handle 
    of the appropriate type opened for writing. Existing files with the same 
    name are overwritten.
    
    Parameters
    ----------
    fname : `str`
        Path to the fastq file. 
    compression : {'bz2', 'gz', None}
        Compression format to use.
        
    Returns
    -------
    `IO`
       The file handle to the compressed file. 
    """
    if compression == "bz2":
        handle = bz2.open(fname + ".bz2", "wt")
    elif compression == "gz":
        handle = gzip.open(fname + ".gz", "wt")
    elif compression is None:
        handle = open(fname, "wt")
    else:
        raise IOError("unrecognized compression mode '{mode}'".format(mode=compression))
    return handle


def read_fastq(fname, filter_function=None, buffer_size=BUFFER_SIZE, qbase=33):
    """
    Generator function for reading from FASTQ_ file *fname*. Yields an 
    :py:class:`~FQRead` object for each FASTQ_ record in the file. The 
    *filter_function* must operate on an :py:class:`~FQRead` object 
    and return ``True`` or ``False``. If the result is ``False``, the record 
    will be skipped silently.

    Parameters
    ----------
    fname : `str`
        Path to the fastq file. 
    filter_function : `Callable`, default: None
        A function operating on a :py:class:`~FQRead` object that returns a
        `bool` indicting if a read should be discarded or not.
    buffer_size : `int`, default: 100000
        Size of the buffer that :py:func:`open.read` accepts.
    qbase : `int`, default: 33
        Integer ASCII value that correponds to Phred score of 0
        
    Returns
    -------
    `generator`
        A generator of :py:class:`~FQRead` objects.
    
    Notes
    -----
    .. note:: To read multiple files in parallel (such as index or \
        forward/reverse reads), use :py:func:`read_fastq_multi` instead.
    """
    _, _, ext, compression = split_fastq_path(fname)
    if compression is None and ext in (".fq", ".fastq"):  # raw FASTQ
        open_func = open
    elif compression == "bz2":
        open_func = bz2.open
    elif compression == "gz":
        open_func = gzip.open
    else:
        raise IOError(
            "Unrecognized compression " "mode '{mode}'".format(mode=compression)
        )

    eof = False
    leftover = ""
    with open_func(fname, "rt") as handle:
        while not eof:
            buf = handle.read(buffer_size)
            if len(buf) < buffer_size:
                eof = True

            buf = leftover + buf  # prepend partial record from previous buffer
            lines = buf.split("\n")
            fastq_count = len(lines) // 4

            if not eof:  # handle lines from the trailing partial FASTQ record
                dangling = len(lines) % 4
                if dangling == 0:  # quality line (probably) incomplete
                    dangling = 4
                    fastq_count = fastq_count - 1
                # join the leftover lines back into a string
                leftover = "\n".join(lines[len(lines) - dangling :])

            # index into the list of lines to pull out the FASTQ records
            for i in range(fastq_count):
                # (header, sequence, header2, quality)
                fq = FQRead(*lines[i * 4 : (i + 1) * 4], qbase=qbase)
                if filter_function is None:
                    # no filtering
                    yield fq
                elif filter_function(fq):
                    # passes filtering
                    yield fq
                else:
                    # fails filtering
                    continue


def read_fastq_multi(
    fnames, filter_function=None, buffer_size=BUFFER_SIZE, match_lengths=True, qbase=33
):
    """
    Generator function for reading from multiple FASTQ_ files in parallel. 
    The argument *fnames* is an iterable of FASTQ_ file names. Yields a 
    tuple of :py:class:`~FQRead` objects, one for each file in 
    *fnames*. The *filter_function* must operate on an :py:class:`~FQRead` 
    object and return ``True`` or ``False``. If the result is ``False`` for 
    any :py:class:`~FQRead` in the tuple, the entire tuple will be skipped.

    If *match_lengths* is ``True``, the generator will yield ``None`` if the 
    files do not contain the same number of FASTQ_ records. Otherwise, it 
    will silently ignore partial records.
    
    Parameters
    ----------
    fnames : `list`
        List of fastq file paths to parse. 
    filter_function : `Callable`, default: None
        A function operating on a :py:class:`~FQRead` object that returns a
        `bool` indicting if a read should be discarded or not.
    buffer_size : `int`, default: 100000
        Size of the buffer that :py:func:`open.read` accepts.
    match_lengths : `bool`, default: True
        If *match_lengths* is ``True``, the generator will yield ``None`` if 
        the files do not contain the same number of FASTQ_ records. Otherwise, 
        it will silently ignore partial records.
    qbase : `int`, default: 33
        Integer ASCII value that correponds to Phred score of 0
        
    Returns
    -------
    `generator`
        A generator of tuples of :py:class:`~FQRead` objects.
    """
    fq_generators = list()
    for f in fnames:
        fq_generators.append(
            read_fastq(f, filter_function=None, buffer_size=BUFFER_SIZE, qbase=qbase)
        )

    for records in itertools.zip_longest(*fq_generators, fillvalue=None):
        if None in records:  # mismatched file lengths
            if match_lengths:
                yield None
            else:
                break  # shortest FASTQ file is empty, so we're done
        if filter_function is None:  # no filtering
            yield records
        elif all(filter_function(x) for x in records):  # pass filtering
            yield records
        else:  # fail filtering
            continue


def fastq_filter_chastity(fq):
    """
    Filtering function for :py:func:`read_fastq` and 
    :py:func:`read_fastq_multi`. Returns ``True`` if the 
    :py:class:`~FQRead` object *fq* is chaste.
    
    Parameters
    ----------
    fq : :py:class:`~FQRead`
        Read object to read chastity bit from.
    """
    return fq.is_chaste()
