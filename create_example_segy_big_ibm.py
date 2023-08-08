import os
import pathlib
import io
import struct

import segyio
from segytools import SegyFileHeaderRev2

def write_first_five_traces(input_segy_file:str, output_segy_context_manager:io.BufferedIOBase):
    path_segy_file = pathlib.Path(str(input_segy_file))
    assert (path_segy_file.is_file())
    print(f"reading {path_segy_file.name}")

    segy_file_size = os.path.getsize(input_segy_file)
    print(f"segy file size {segy_file_size}")
    
    file_header_input = SegyFileHeaderRev2(segy_logger=None)

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
        
        output_segy_context_manager.write(b_text_header)
        output_segy_context_manager.write(b_file_header)
        
        # Loop through traces ...
        cntr = 0
        while cntr < 5:    
            # TRACE HEADER
            b_trace_header = fobj.read(240)
            output_segy_context_manager.write(b_trace_header)
            
            # TRACE DATA
            b_trace_data = fobj.read(trc_data_length_in_bytes)
            output_segy_context_manager.write(b_trace_data)
            
            cntr += 1

        fobj.close()
    
    
# --- original big endian IBM Float32
sgy_file = "/mnt/storage5/skylayer5/data/dataunderground_penobscot/Penobscot_3D_gathers_part1/3D_gathers_pstm_nmo_X1001.sgy"
sgy_file_out = "3D_gathers_pstm_nmo_X1001_original_big_endian_ibm.sgy"
with open(sgy_file_out, 'ab') as fout:
    write_first_five_traces(input_segy_file=sgy_file, output_segy_context_manager=fout)
    fout.close()

# --- segyio read back
with segyio.open(sgy_file_out, mode='r', ignore_geometry=True, endian='big') as segy_handle:

    # Memory map file for faster reading (especially if file is big...)
    # segy_handle.mmap()

    start = 0
    stop = 5
    block_headers = [segy_handle.header[trc_idx] for trc_idx in range(start, stop)]
    for hdr in block_headers[:3]:
        print(hdr[5], hdr[9])

    tmp = block_headers[0]
    print(type(tmp))  # <class 'segyio.field.Field'>
    # print(tmp)
    tmp_buf = tmp.buf  # 240 bytes trace header
    print(len(tmp_buf))
    print(struct.unpack_from('>i', tmp_buf, offset=4))
    print(int.from_bytes(tmp_buf[4:8], byteorder='big', signed=False))


# OUTPUT
# 1000 1000
# 1000 1000
# 1000 1000
# <class 'segyio.field.Field'>
# 240
# (1000,)
# 1000
