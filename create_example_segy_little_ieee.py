import os
import pathlib
import io
import struct

import numpy
import segyio
from segytools import SegyHeaderItem, SegyAbstractHeader, SegyFileHeaderRev2
from segytools.segy_trace_header import CORRELATED, COORDINATE_UNITS, COORDINATE_SCALAR_MULTIPLIER, DATA_USE, TRACE_IDENTIFICATION_CODE
from segytools.datatypes import DATA_SAMPLE_FORMAT_INT16, DATA_SAMPLE_FORMAT_INT32
from segytools.utils import read_trace_data

class SegyTraceHeaderCustomInput(SegyAbstractHeader):

    def __init__(self, segy_logger=None):
        super().__init__()
        self.byte_length = 240
        self.segy_logger = segy_logger  # used for writing information to terminal or file; see https://docs.python.org/3.10/library/logging.html

        # HEADERS
        self.byte001_int32 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,
            start_byte=1,
            description="",
            segy_logger=self.segy_logger,
            )  # maps to rev2.trc_seq_num_within_line
        self.byte005_int32 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,
            start_byte=5,
            description="INCREMENTAL LINE  NUMBER CDP-X",
            segy_logger=self.segy_logger,
            )  # maps to rev2.in_line
        self.byte009_int32 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,
            start_byte=9,
            description="INCREMENTAL LINE  NUMBER CDP-Y",
            segy_logger=self.segy_logger,
            )  # maps to rev2.cross_line
        self.byte033_int16 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,
            start_byte=33,
            description="FOLD",
            segy_logger=self.segy_logger,
            )  # maps to rev2.num_horz_summed_traces
        self.byte037_int32 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,
            start_byte=37,
            description="OFFSET",
            segy_logger=self.segy_logger,
            )  # maps to rev2.offset
        self.byte073_int32 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,
            start_byte=73,
            description="UTM EASTING FOR CDP BIN CENTER",
            segy_logger=self.segy_logger,
            )  # maps to rev2.ens_x_coord
        self.byte077_int32 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,
            start_byte=77,
            description="UTM NORTHING FOR CDP BIN CENTER",
            segy_logger=self.segy_logger,
            )  # maps to rev2.ens_y_coord
        self.byte115_int16 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=115,
            description="number of samples in this trace",
            segy_logger=self.segy_logger,
            )  # maps to rev2.num_samples
        self.byte117_int16 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=117,
            description="sample interval in ms for this trace",
            segy_logger=self.segy_logger,
            )  # maps to rev2.sample_interval
        self.byte201_int32 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,
            start_byte=201,
            description="WATTER BOTTOM TIME (MS)",
            segy_logger=self.segy_logger,
            )  # maps to rev2.undefined233 NOTE IN EBCDIC!
        self.byte205_int32 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,
            start_byte=205,
            description="WATTER BOTTOM DEPTH (M) FOR WATER VELOCITY 1500M/S",
            segy_logger=self.segy_logger,
            )  # maps to rev2.undefined237 NOTE IN EBCDIC!
        
class SegyTraceHeaderCustomOutput(SegyAbstractHeader):
    """Trimmed down version of Rev2.
    """

    def __init__(self, segy_logger=None):
        super().__init__()
        self.byte_length = 240
        self.segy_logger = segy_logger  # used for writing information to terminal or file; see https://docs.python.org/3.10/library/logging.html
        self.byte_array = bytearray(240)

        # HEADERS
        self.trc_seq_num_within_line = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,  # nbytes=4,
            start_byte=1,
            description="trace sequence number within line",
            segy_logger=self.segy_logger,
        )
        self.trc_seq_num_within_file = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,  # nbytes=4,
            start_byte=5,
            description="trace sequence number within segy file",
            segy_logger=self.segy_logger,
        )
        self.trc_identification_code = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=29,
            description="trace identification code",
            map_dict=TRACE_IDENTIFICATION_CODE,
            segy_logger=self.segy_logger,
        )
        self.num_horz_summed_traces = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=33,
            description="number of horizontally stacked traces yielding this trace",
            segy_logger=self.segy_logger,
        )
        self.data_use = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=35,
            description="data use",
            map_dict=DATA_USE,
            value=1,
            segy_logger=self.segy_logger,
        )
        self.offset = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,  # nbytes=4,
            start_byte=37,
            description="distance from center of the source point to the center of the receiver group",
            segy_logger=self.segy_logger,
        )
        self.z_scalar = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=69,
            description="scalar to be applied to all elevations and depths",
            map_dict=COORDINATE_SCALAR_MULTIPLIER,
            value=1,
            segy_logger=self.segy_logger,
        )
        self.xy_scalar = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=71,
            description="scalar to be applied to all coordinates",
            map_dict=COORDINATE_SCALAR_MULTIPLIER,
            value=1,
            segy_logger=self.segy_logger,
        )
        self.coord_units = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=89,
            description="coordinate units",
            map_dict=COORDINATE_UNITS,
            value=1,
            segy_logger=self.segy_logger,
        )
        self.num_samples = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=115,
            description="number of samples in this trace",
            segy_logger=self.segy_logger,
        )
        self.sample_interval = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=117,
            description="sample interval in ms for this trace",
            segy_logger=self.segy_logger,
        )
        self.correlated = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT16,  # nbytes=2,
            start_byte=125,
            description="correlated",
            map_dict=CORRELATED,
            value=1,
            segy_logger=self.segy_logger,
        )
        self.ens_x_coord = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,  # nbytes=4,
            start_byte=181,
            description="x coordinate of ensemble position of this trace",
            segy_logger=self.segy_logger,
        )
        self.ens_y_coord = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,  # nbytes=4,
            start_byte=185,
            description="y coordinate of ensemble position of this trace",
            segy_logger=self.segy_logger,
        )
        self.in_line = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,  # nbytes=4,
            start_byte=189,
            description="for 3D poststack data this field is for in line number",
            segy_logger=self.segy_logger,
        )
        self.cross_line = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,  # nbytes=4,
            start_byte=193,
            description="for 3D poststack data this field is for cross line number",
            segy_logger=self.segy_logger,
        )
        self.undefined233 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,  # nbytes=4,
            start_byte=233,
            description="undefined",
            segy_logger=self.segy_logger,
        )
        self.undefined237 = SegyHeaderItem(
            sample_format=DATA_SAMPLE_FORMAT_INT32,  # nbytes=4,
            start_byte=237,
            description="undefined",
            segy_logger=self.segy_logger,
        )

def write_first_five_traces(input_segy_file:str, output_segy_context_manager:io.BufferedIOBase):
    path_segy_file = pathlib.Path(str(input_segy_file))
    assert (path_segy_file.is_file())
    print(f"reading {path_segy_file.name}")

    segy_file_size = os.path.getsize(input_segy_file)
    print(f"segy file size {segy_file_size}")
    
    file_header_input = SegyFileHeaderRev2(segy_logger=None)
    file_header_output = SegyFileHeaderRev2(segy_logger=None)
    trace_header_input = SegyTraceHeaderCustomInput(segy_logger=None)
    trace_header_output = SegyTraceHeaderCustomOutput(segy_logger=None)

    with open(path_segy_file, 'rb') as fobj:
        # read the first 3200 bytes.
        # This will always be 3200 byte textual file header
        b_text_header = fobj.read(3200)
        
        b_file_header = fobj.read(file_header_input.byte_length)
        file_header_input.set_header_values(buf=b_file_header, byteorder='>')
        
        sample_size_in_bytes = file_header_input.sample_format_size_in_bytes()
        trc_data_length_in_bytes = file_header_input.num_samples_per_trace.value * sample_size_in_bytes

        n_traces_in_file_estimate = (segy_file_size - 3600) // (240 + trc_data_length_in_bytes)
        print(f"estimated number of traces is {n_traces_in_file_estimate}")
        
        # update file header, output traces will be ieee rather than ibm float
        file_header_output.set_header_values(buf=b_file_header, byteorder='>')
        file_header_output.data_sample_format_code.value = int(5)
        #print(f"file header data sample format {file_header_output.data_sample_format_code.value}, {file_header_output.data_sample_format_code.mapped_value}")
        file_header_output.num_traces_per_ensemble.value = int(61)
        file_header_output.num_aux_traces_per_ensemble.value = int(0)
        file_header_output.fold.value = int(61)
        file_header_output.sort_code.value = int(2)  # CDP Ensemble
        file_header_output.segy_revision.value = int(2)
        file_header_output.measurement_system.value = int(2)  # meters
        file_header_output.fixed_length.value = int(1)
        
        output_segy_context_manager.write(b_text_header)
        output_segy_context_manager.write(file_header_output.to_bytes(byteorder='<'))
        
        # Loop through traces ...
        cntr = 0
        while cntr < 5:    
            # TRACE HEADER
            b_trace_header = fobj.read(240)
            trace_header_input.set_header_values(buf=b_trace_header, byteorder='>')
            
            # write output trace header to output bytearray using little endian
            trace_header_output.trc_seq_num_within_file.value = cntr
            trace_header_output.trc_seq_num_within_line.value = trace_header_input.byte001_int32.value
            trace_header_output.in_line.value = trace_header_input.byte005_int32.value
            trace_header_output.cross_line.value = trace_header_input.byte009_int32.value
            trace_header_output.offset.value = trace_header_input.byte037_int32.value
            trace_header_output.ens_x_coord.value = trace_header_input.byte073_int32.value  # scaling checked, all OK
            trace_header_output.ens_y_coord.value = trace_header_input.byte077_int32.value  # scaling checked, all OK
            trace_header_output.num_samples.value = trace_header_input.byte115_int16.value
            trace_header_output.sample_interval.value = trace_header_input.byte117_int16.value
            trace_header_output.undefined233.value = trace_header_input.byte201_int32.value
            trace_header_output.undefined237.value = trace_header_input.byte205_int32.value
            trace_header_output.trc_identification_code.value = int(1)
            output_segy_context_manager.write(trace_header_output.to_bytes(byteorder='<'))
            
            # TRACE DATA
            b_trace_data = fobj.read(trc_data_length_in_bytes)
            tmp_trace = read_trace_data(buf=b_trace_data, fmt=file_header_input.sample_format_datatype(), byteorder='>')
            # print(file_header_input.sample_format_datatype())  # DataSampleFormat(format='ibm', ctype='ibm', size_in_bytes=4)
            # print(f"tmp_trace shape {tmp_trace.shape}, tmp trace dtype {tmp_trace.dtype}")
            tmp_trace = numpy.float32(tmp_trace)
            # assert(len(tmp_trace.tobytes(order='C')) == 6004)
            output_segy_context_manager.write(tmp_trace.tobytes(order='C'))
            
            cntr += 1

        fobj.close()
    
    
# --- reformatted little endian IEEE Float32
sgy_file = "/mnt/storage5/skylayer5/data/dataunderground_penobscot/Penobscot_3D_gathers_part1/3D_gathers_pstm_nmo_X1001.sgy"
sgy_file_out = "3D_gathers_pstm_nmo_X1001_formatted_little_endian_ieee.sgy"
with open(sgy_file_out, 'ab') as fout:
    write_first_five_traces(input_segy_file=sgy_file, output_segy_context_manager=fout)
    fout.close()

# --- segyio read back
with segyio.open(sgy_file_out, mode='r', ignore_geometry=True, endian='little') as segy_handle:

    # Memory map file for faster reading (especially if file is big...)
    # segy_handle.mmap()

    start = 0
    stop = 5
    block_headers = [segy_handle.header[trc_idx] for trc_idx in range(start, stop)]
    for hdr in block_headers[:3]:
        # --print(hdr[segyio.TraceField.INLINE_3D], hdr[segyio.TraceField.CROSSLINE_3D])
        print(hdr[189], hdr[193])

    tmp = block_headers[0]
    print(type(tmp))  # <class 'segyio.field.Field'>
    # print(tmp)
    tmp_buf = tmp.buf  # 240 bytes trace header
    print(len(tmp_buf))
    print(f"struct unpack as little: {struct.unpack_from('<i', tmp_buf, offset=188)}")
    print(f"int to_bytes as little: {int.from_bytes(tmp_buf[188:192], byteorder='little', signed=False)}")
    print(f"struct unpack as big: {struct.unpack_from('>i', tmp_buf, offset=188)}")
    print(f"int to_bytes as big: {int.from_bytes(tmp_buf[188:192], byteorder='big', signed=False)}")


# OUTPUT
# 1000 1000
# 1000 1000
# 1000 1000
# <class 'segyio.field.Field'>
# 240
# struct unpack as little: (-402456576,)
# int to_bytes as little: 3892510720
# struct unpack as big: (1000,)
# int to_bytes as big: 1000
